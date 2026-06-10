#!/usr/bin/env python3
# main.py - Small-C Interactive Interpreter shell

import os
import sys
import re

from interpreter import Interpreter
from memory import Scope
from parser import ParseError
from lexer import LexError

# ── Syntax highlighting ────────────────────────────────────────────────────

_C_KEYWORDS = frozenset({
    'int', 'char', 'void', 'if', 'else', 'while', 'for', 'do',
    'return', 'break', 'continue', 'struct', 'sizeof',
})

# ANSI colour codes（可由 COLOR 指令切換）
_HI_KW    = "\033[94m"      # bright blue  – keywords
_HI_PREP  = "\033[95m"      # magenta       – #define
_HI_STR   = "\033[92m"      # bright green  – strings
_HI_CHAR  = "\033[96m"      # cyan          – char literals
_HI_NUM   = "\033[93m"      # yellow        – numbers
_HI_CMT   = "\033[90m"      # dark grey     – comments
_HI_FUNC  = "\033[96m"      # cyan          – function names
_RESET    = "\033[0m"

# ── 主題定義 ──────────────────────────────────────────────────────────────
_THEMES = {
    'default': dict(KW="\033[94m", PREP="\033[95m", STR="\033[92m",
                    CHAR="\033[96m", NUM="\033[93m", CMT="\033[90m",
                    FUNC="\033[96m"),
    'matrix':  dict(KW="\033[92m",  PREP="\033[32m",  STR="\033[92m",
                    CHAR="\033[32m", NUM="\033[92m",  CMT="\033[90m",
                    FUNC="\033[92m"),
    'warm':    dict(KW="\033[91m",  PREP="\033[95m",  STR="\033[93m",
                    CHAR="\033[33m", NUM="\033[91m",  CMT="\033[90m",
                    FUNC="\033[93m"),
    'ocean':   dict(KW="\033[96m",  PREP="\033[34m",  STR="\033[94m",
                    CHAR="\033[36m", NUM="\033[34m",  CMT="\033[90m",
                    FUNC="\033[96m"),
    'off':     dict(KW="", PREP="", STR="", CHAR="", NUM="", CMT="", FUNC=""),
}
_current_theme = 'default'

def _apply_theme(name: str) -> bool:
    """Apply a named theme; return True on success."""
    global _HI_KW, _HI_PREP, _HI_STR, _HI_CHAR, _HI_NUM, _HI_CMT, _HI_FUNC
    global _current_theme
    t = _THEMES.get(name.lower())
    if t is None:
        return False
    _HI_KW   = t['KW'];  _HI_PREP = t['PREP']; _HI_STR  = t['STR']
    _HI_CHAR = t['CHAR']; _HI_NUM  = t['NUM'];  _HI_CMT  = t['CMT']
    _HI_FUNC = t['FUNC']
    _current_theme = name.lower()
    return True

def _colorize(line: str) -> str:
    """Return a syntax-highlighted version of one source line."""
    out = []
    i   = 0
    n   = len(line)

    while i < n:
        # ── Line comment ──────────────────────────────────────────────
        if line[i:i+2] == '//':
            out.append(_HI_CMT + line[i:] + _RESET)
            break

        # ── Block comment fragment (single-line portion) ──────────────
        if line[i:i+2] == '/*':
            j = line.find('*/', i + 2)
            if j == -1:
                out.append(_HI_CMT + line[i:] + _RESET)
                break
            out.append(_HI_CMT + line[i:j+2] + _RESET)
            i = j + 2
            continue

        # ── String literal ────────────────────────────────────────────
        if line[i] == '"':
            j = i + 1
            while j < n:
                if line[j] == '\\':
                    j += 2
                    continue
                if line[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(_HI_STR + line[i:j] + _RESET)
            i = j
            continue

        # ── Char literal ──────────────────────────────────────────────
        if line[i] == "'":
            j = i + 1
            while j < n:
                if line[j] == '\\':
                    j += 2
                    continue
                if line[j] == "'":
                    j += 1
                    break
                j += 1
            out.append(_HI_CHAR + line[i:j] + _RESET)
            i = j
            continue

        # ── #define / preprocessor ────────────────────────────────────
        if line[i] == '#':
            j = i + 1
            while j < n and (line[j].isalnum() or line[j] == '_'):
                j += 1
            out.append(_HI_PREP + line[i:j] + _RESET)
            i = j
            continue

        # ── Hex number ────────────────────────────────────────────────
        if line[i:i+2] in ('0x', '0X'):
            j = i + 2
            while j < n and line[j] in '0123456789abcdefABCDEF':
                j += 1
            out.append(_HI_NUM + line[i:j] + _RESET)
            i = j
            continue

        # ── Decimal number (not part of an identifier) ─────────────────
        if line[i].isdigit() and (i == 0 or not (line[i-1].isalnum() or line[i-1] == '_')):
            j = i
            while j < n and line[j].isdigit():
                j += 1
            out.append(_HI_NUM + line[i:j] + _RESET)
            i = j
            continue

        # ── Identifier / keyword / function call ──────────────────────
        if line[i].isalpha() or line[i] == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'):
                j += 1
            word = line[i:j]
            # Peek past whitespace for '('
            k = j
            while k < n and line[k] == ' ':
                k += 1
            if word in _C_KEYWORDS:
                out.append(_HI_KW + word + _RESET)
            elif k < n and line[k] == '(':
                out.append(_HI_FUNC + word + _RESET)
            else:
                out.append(word)
            i = j
            continue

        out.append(line[i])
        i += 1

    return ''.join(out)

VERSION = "1.0"
AUTHOR  = "Small-C Interpreter"
SEMESTER = "Spring 2026"
PROMPT  = "sc> "
CONT_PROMPT = "  > "   # continuation prompt for multi-line input

_CTRL_C = object()     # sentinel: user pressed Ctrl+C

# ── Brace/completeness check ───────────────────────────────────────────────

def count_depth(text):
    """Count net unclosed braces outside strings/comments."""
    depth = 0
    in_str = False
    in_char = False
    in_lc = False    # line comment
    in_bc = False    # block comment
    i = 0
    while i < len(text):
        c = text[i]
        if in_lc:
            if c == '\n':
                in_lc = False
        elif in_bc:
            if c == '*' and i + 1 < len(text) and text[i + 1] == '/':
                in_bc = False
                i += 1
        elif in_str:
            if c == '\\':
                i += 1
            elif c == '"':
                in_str = False
        elif in_char:
            if c == '\\':
                i += 1
            elif c == "'":
                in_char = False
        else:
            if c == '/' and i + 1 < len(text) and text[i + 1] == '/':
                in_lc = True
            elif c == '/' and i + 1 < len(text) and text[i + 1] == '*':
                in_bc = True
                i += 1
            elif c == '"':
                in_str = True
            elif c == "'":
                in_char = True
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
        i += 1
    return depth


def is_input_complete(text):
    """Return True if the accumulated input looks syntactically complete."""
    stripped = text.strip()
    if not stripped:
        return True
    if count_depth(stripped) > 0:
        return False
    # Must end with ; or } or be a preprocessor directive
    last = stripped.rstrip()
    return (last.endswith(';') or last.endswith('}')
            or last.startswith('#define') or last.endswith('.'))


# ── Shell state ────────────────────────────────────────────────────────────

class Shell:
    def __init__(self):
        self.interp = Interpreter()
        self.program_lines = []    # list of str, no trailing newline
        self.modified = False      # unsaved changes flag
        self.current_file = None

    # ── Input helpers ──────────────────────────────────────────────────────

    def read_line(self, prompt=''):
        try:
            return input(prompt)
        except EOFError:
            return None
        except KeyboardInterrupt:
            print("  ^C")
            return _CTRL_C

    def read_multiline(self, first_line):
        """Accumulate lines until input is syntactically complete."""
        lines = [first_line]
        accumulated = first_line
        while not is_input_complete(accumulated):
            line = self.read_line(CONT_PROMPT)
            if line is None or line is _CTRL_C:
                print("(input cancelled)")
                return ''      # 取消，不執行任何東西
            lines.append(line)
            accumulated = '\n'.join(lines)
        return accumulated

    # ── Program line display ───────────────────────────────────────────────

    # detect whether the terminal supports ANSI colour
    _COLOR = sys.stdout.isatty() or os.environ.get('TERM', '') != ''

    def list_lines(self, start=None, end=None):
        if not self.program_lines:
            print("(program is empty)")
            return
        if start is None:
            start = 1
        if end is None:
            end = len(self.program_lines)
        start = max(1, start)
        end = min(len(self.program_lines), end)
        for i in range(start - 1, end):
            raw  = self.program_lines[i]
            body = _colorize(raw) if self._COLOR else raw
            print(f"\033[90m{i+1:4d}:\033[0m {body}" if self._COLOR
                  else f"{i+1:4d}: {raw}")

    # ── Commands ───────────────────────────────────────────────────────────

    def cmd_about(self):
        print(f"Small-C Interactive Interpreter v{VERSION}")
        print(f"Author : {AUTHOR}")
        print(f"Course : System Software")
        print(f"Semester: {SEMESTER}")

    def cmd_help(self):
        help_text = """Available commands:
  ABOUT              Show interpreter information
  HELP               Show this help message
  APPEND             Enter program lines (end with a line containing just '.')
  LIST               List all program lines
  LIST n             List line n
  LIST n1-n2         List lines n1 to n2
  EDIT n             Edit line n
  DELETE n           Delete line n
  INSERT n           Insert lines before line n (end with '.')
  CHECK              Check program for syntax errors
  RUN                Run the current program
  SAVE filename      Save program to file
  LOAD filename      Load program from file
  NEW                Clear program (prompts if unsaved changes)
  TRACE ON           Enable trace mode
  TRACE OFF          Disable trace mode
  VARS               Display all current variables
  FUNCS              List all functions (user-defined and built-ins)
  MEMSHOW            Show memory layout (variables + string literals)
  COLOR              Show available color themes
  COLOR <theme>      Switch theme: default / matrix / warm / ocean / off
  CLEAR              Clear the terminal screen
  QUIT / EXIT        Exit the interpreter"""
        print(help_text)

    def cmd_append(self):
        start_line = len(self.program_lines) + 1
        print(f"(Enter lines; type '.' alone to finish. Auto-indent ON.)")
        lineno = start_line
        depth  = 0          # current indent level
        INDENT = 4          # spaces per level
        DIM    = "\033[90m"
        RST    = "\033[0m"

        while True:
            # 深度提示放在 │ 後面，不佔輸入空間，使用者可自由退格到最左
            hint = f"{DIM}+{depth*INDENT}{RST} " if depth > 0 else "  "
            raw = self.read_line(f"{lineno:4d}│{hint}")
            if raw is None or raw is _CTRL_C:
                print("(append cancelled)")
                return

            text = raw.strip()
            if text == '.':
                break

            # Lines starting with '}' are stored one level back
            store_depth = max(0, depth - 1) if text.startswith('}') else depth
            stored_line = (' ' * (store_depth * INDENT)) + text if text else ''

            self.program_lines.append(stored_line)
            self.modified = True
            lineno += 1

            # Update depth for next line
            depth = max(0, depth + text.count('{') - text.count('}'))

    def cmd_list(self, arg):
        if not arg:
            self.list_lines()
        elif '-' in arg:
            parts = arg.split('-', 1)
            try:
                s, e = int(parts[0]), int(parts[1])
                self.list_lines(s, e)
            except ValueError:
                print("Error: Invalid range format. Use LIST n1-n2")
        else:
            try:
                n = int(arg)
                self.list_lines(n, n)
            except ValueError:
                print("Error: Invalid line number")

    def cmd_edit(self, arg):
        try:
            n = int(arg.strip())
        except ValueError:
            print("Error: EDIT requires a line number")
            return
        if n < 1 or n > len(self.program_lines):
            print(f"Error: Line {n} does not exist (program has {len(self.program_lines)} lines)")
            return
        print(f"{n:4d}: {self.program_lines[n-1]}")
        new_line = self.read_line(f"{n:4d}> ")
        if new_line is not None:
            self.program_lines[n - 1] = new_line
            self.modified = True

    def cmd_delete(self, arg):
        arg = arg.strip()
        if '-' in arg:
            parts = arg.split('-', 1)
            try:
                s, e = int(parts[0]), int(parts[1])
            except ValueError:
                print("Error: Invalid range"); return
            s = max(1, s)
            e = min(len(self.program_lines), e)
            del self.program_lines[s - 1:e]
            self.modified = True
            print(f"Deleted lines {s}-{e}.")
        else:
            try:
                n = int(arg)
            except ValueError:
                print("Error: DELETE requires a line number"); return
            if n < 1 or n > len(self.program_lines):
                print(f"Error: Line {n} does not exist"); return
            del self.program_lines[n - 1]
            self.modified = True

    def cmd_insert(self, arg):
        try:
            n = int(arg.strip())
        except ValueError:
            print("Error: INSERT requires a line number"); return
        n = max(1, min(n, len(self.program_lines) + 1))
        print(f"(Insert before line {n}; type '.' alone to finish. Auto-indent ON.)")
        new_lines = []
        lineno = n
        depth  = 0
        INDENT = 4
        DIM    = "\033[90m"
        RST    = "\033[0m"

        while True:
            hint = f"{DIM}+{depth*INDENT}{RST} " if depth > 0 else "  "
            raw = self.read_line(f"{lineno:4d}│{hint}")
            if raw is None or raw is _CTRL_C:
                break
            text = raw.strip()
            if text == '.':
                break
            store_depth = max(0, depth - 1) if text.startswith('}') else depth
            stored_line = (' ' * (store_depth * INDENT)) + text if text else ''
            new_lines.append(stored_line)
            lineno += 1
            depth = max(0, depth + text.count('{') - text.count('}'))

        for i, line in enumerate(new_lines):
            self.program_lines.insert(n - 1 + i, line)
        if new_lines:
            self.modified = True

    def cmd_check(self):
        if not self.program_lines:
            print("No program loaded.")
            return
        source = '\n'.join(self.program_lines)
        errors = self.interp.check_program(source)
        if errors:
            for e in errors:
                print(f"Error: {e}")
        else:
            print("No errors found.")

    def cmd_run(self):
        if not self.program_lines:
            print("No program loaded.")
            return
        source = '\n'.join(self.program_lines)
        self.interp.run_program(source, list(self.program_lines))

    def cmd_save(self, filename):
        filename = filename.strip()
        if not filename:
            print("Error: SAVE requires a filename"); return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for line in self.program_lines:
                    f.write(line + '\n')
            self.current_file = filename
            self.modified = False
            n = len(self.program_lines)
            print(f"Saved {n} line{'s' if n != 1 else ''} to '{filename}'.")
        except IOError as e:
            print(f"Error saving file: {e}")

    def cmd_new(self):
        if self.modified:
            ans = self.read_line("Unsaved changes. Clear anyway? (y/n): ")
            if ans is None or ans.strip().lower() not in ('y', 'yes'):
                return
        self.program_lines.clear()
        self.modified = False
        self.current_file = None
        # Reset interpreter interactive state
        self.interp.global_scope = Scope()
        self.interp.user_funcs.clear()
        self.interp.defines.clear()
        self.interp.mem.reset()
        self.interp._string_cache.clear()
        print("All cleared.")

    def cmd_load(self, filename):
        filename = filename.strip()
        if not filename:
            print("Error: LOAD requires a filename"); return
        if self.modified:
            ans = self.read_line("Unsaved changes. Load anyway? (y/n): ")
            if ans is None or ans.strip().lower() not in ('y', 'yes'):
                return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f.readlines()]
            # Remove trailing empty lines
            while lines and not lines[-1].strip():
                lines.pop()
            self.program_lines = lines
            self.modified = False
            self.current_file = filename
            n = len(self.program_lines)
            print(f"Loaded {n} line{'s' if n != 1 else ''} from '{filename}'.")
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
        except IOError as e:
            print(f"Error loading file: {e}")

    def cmd_trace(self, arg):
        a = arg.strip().upper()
        if a == 'ON':
            self.interp.trace = True
            print("Trace mode enabled.")
        elif a == 'OFF':
            self.interp.trace = False
            print("Trace mode disabled.")
        else:
            print("Usage: TRACE ON | TRACE OFF")

    def cmd_vars(self):
        self.interp.show_vars(self.interp.global_scope)

    def cmd_funcs(self):
        self.interp.show_funcs()

    def cmd_memshow(self):
        self.interp.show_memory(self.interp.global_scope)

    def cmd_color(self, arg):
        R = "\033[0m"; B = "\033[1m"
        name = arg.strip().lower()
        if not name:
            # 顯示目前主題 + 可用主題預覽
            print(f"目前主題：{B}{_current_theme}{R}")
            print("可用主題：")
            previews = {
                'default': "\033[94mkeyword\033[0m  \033[92m\"string\"\033[0m  \033[93m42\033[0m  \033[90m// comment\033[0m",
                'matrix':  "\033[92mkeyword\033[0m  \033[92m\"string\"\033[0m  \033[92m42\033[0m  \033[90m// comment\033[0m",
                'warm':    "\033[91mkeyword\033[0m  \033[93m\"string\"\033[0m  \033[91m42\033[0m  \033[90m// comment\033[0m",
                'ocean':   "\033[96mkeyword\033[0m  \033[94m\"string\"\033[0m  \033[34m42\033[0m  \033[90m// comment\033[0m",
                'off':     "keyword  \"string\"  42  // comment",
            }
            for n, preview in previews.items():
                mark = " ◀ 目前" if n == _current_theme else ""
                print(f"  COLOR {B}{n:<10}{R}  {preview}{mark}")
            return
        if _apply_theme(name):
            print(f"主題已切換為：{B}{name}{R}")
        else:
            keys = ' / '.join(_THEMES.keys())
            print(f"未知主題 '{name}'，可用：{keys}")

    def cmd_clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def cmd_quit(self):
        if self.modified:
            ans = self.read_line("Unsaved changes. Quit anyway? (y/n): ")
            if ans is None or ans.strip().lower() not in ('y', 'yes'):
                return False
        print("Goodbye!")
        return True  # signal to exit

    # ── Main command dispatcher ────────────────────────────────────────────

    def dispatch(self, raw):
        line = raw.strip()
        if not line:
            return False

        upper = line.upper()
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        arg = parts[1] if len(parts) > 1 else ''

        if cmd == 'ABOUT':
            self.cmd_about()
        elif cmd == 'HELP':
            self.cmd_help()
        elif cmd == 'APPEND':
            self.cmd_append()
        elif cmd == 'LIST':
            self.cmd_list(arg)
        elif cmd == 'EDIT':
            self.cmd_edit(arg)
        elif cmd == 'DELETE':
            self.cmd_delete(arg)
        elif cmd == 'INSERT':
            self.cmd_insert(arg)
        elif cmd == 'CHECK':
            self.cmd_check()
        elif cmd == 'RUN':
            self.cmd_run()
        elif cmd == 'SAVE':
            self.cmd_save(arg)
        elif cmd == 'NEW':
            self.cmd_new()
        elif cmd == 'LOAD':
            self.cmd_load(arg)
        elif cmd == 'TRACE':
            self.cmd_trace(arg)
        elif cmd == 'VARS':
            self.cmd_vars()
        elif cmd == 'FUNCS':
            self.cmd_funcs()
        elif cmd == 'MEMSHOW':
            self.cmd_memshow()
        elif cmd == 'COLOR':
            self.cmd_color(arg)
        elif cmd == 'CLEAR':
            self.cmd_clear()
        elif cmd in ('QUIT', 'EXIT'):
            return self.cmd_quit()
        else:
            # Treat as Small-C code (interactive execution)
            full_input = self.read_multiline(raw)
            self.interp.exec_interactive(full_input)
        return False

    # ── REPL loop ──────────────────────────────────────────────────────────

    @staticmethod
    def _load_ascii_art():
        """Try to load ascii_art.txt from the same directory as this script."""
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(here, 'ascii_art.txt')
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read().rstrip('\n')
        except Exception:
            return None

    def run(self):
        C  = "\033[96m"   # cyan
        G  = "\033[92m"   # green
        Y  = "\033[93m"   # yellow
        DIM= "\033[90m"   # grey
        B  = "\033[1m"    # bold
        R  = "\033[0m"    # reset

        # ── ASCII art ──────────────────────────────────────────────────────
        art = self._load_ascii_art()
        if art:
            for line in art.splitlines():
                print(f"\033[0;37m{line}{R}")
            print()

        # ── Title box ──────────────────────────────────────────────────────
        W  = 50   # inner width
        L1 = f"Small-C Interactive Interpreter  v{VERSION}"
        L2 = f"System Software  -  {SEMESTER}"
        print(f"{B}{C}╔{'═'*W}╗{R}")
        print(f"{B}{C}║{L1.center(W)}║{R}")
        print(f"{B}{C}║{L2.center(W)}║{R}")
        print(f"{B}{C}╚{'═'*W}╝{R}")
        print()

        # ── Quick-start guide ──────────────────────────────────────────────
        print(f"{B}  快速開始{R}")
        print(f"  {G}APPEND{R}              {DIM}→{R}  輸入程式碼（{Y}.{R} 結束）")
        print(f"  {G}RUN{R}                 {DIM}→{R}  執行程式")
        print(f"  {G}LIST{R}  {Y}[n | n1-n2]{R}   {DIM}→{R}  彩色列出程式碼")
        print(f"  {G}MEMSHOW{R}             {DIM}→{R}  顯示記憶體配置圖")
        print(f"  {G}TRACE ON{R}            {DIM}→{R}  開啟逐行追蹤模式")
        print(f"  {G}SAVE{R} {Y}filename{R}       {DIM}→{R}  存檔  │  {G}LOAD{R} {Y}filename{R} {DIM}→{R} 讀檔")
        print(f"  {G}VARS{R}  {DIM}│{R}  {G}FUNCS{R}         {DIM}→{R}  顯示變數 │ 函式清單")
        print(f"  {G}HELP{R}                {DIM}→{R}  完整指令說明  │  {G}QUIT{R} {DIM}→{R} 離開")
        print()
        print(f"{DIM}  直接輸入 Small-C 程式碼即可執行，例如：{R}")
        print(f"  {DIM}sc>{R} {C}printf(\"%d\\n\", 3 + 4 * 5);{R}")
        print(f"  {DIM}sc>{R} {C}int x = 42;  printf(\"%d\\n\", x);{R}")
        print()
        while True:
            line = self.read_line(PROMPT)
            if line is None:          # EOF (Ctrl+D / Ctrl+Z)
                print()
                print("Goodbye!")
                break
            if line is _CTRL_C:       # Ctrl+C at main prompt → 回到提示符
                continue
            should_exit = self.dispatch(line)
            if should_exit:
                break


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    shell = Shell()
    # Optional: load a file from command line
    if len(sys.argv) > 1:
        shell.cmd_load(sys.argv[1])
    shell.run()
