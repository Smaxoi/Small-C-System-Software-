#!/usr/bin/env python3
# main.py - Small-C 互動式解譯器的「互動介面 (Shell / REPL)」
#
# 【這個檔案的核心任務】
#   提供 sc> 提示符，讓使用者輸入指令（APPEND/LIST/RUN…）或直接打 Small-C 程式碼。
#   它負責「指令分派、程式碼編輯、語法高亮、主題切換」，真正的執行交給 interpreter.py。

import os
import sys
import re

from interpreter import Interpreter
from memory import Scope
from parser import ParseError
from lexer import LexError

# ── 語法高亮 ────────────────────────────────────────────────────────────────

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
    """【語法高亮｜額外功能】手動掃描一行字元，幫關鍵字/字串/數字/註解上不同顏色。"""
    out = []
    i   = 0
    n   = len(line)

    # 核心：逐字元判斷目前是哪種語法元素，包上對應的 ANSI 顏色碼
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

# 【Ctrl+C 哨兵｜額外功能】用一個獨一無二的物件代表「使用者按了 Ctrl+C」，
# 不能用 '' 或 None，因為它們在輸入中有正常意義（空行、EOF）。
_CTRL_C = object()

# ── 括號完整性檢查 ────────────────────────────────────────────────────────────

def count_depth(text):
    """算大括號淨深度（忽略字串/註解內的）；>0 代表還有沒收尾的 {。"""
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
    """【判斷多行輸入是否完整】決定要不要再進連續輸入模式 ( > )。"""
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
    """【互動 Shell】保存目前編輯中的程式、檔案狀態，並驅動整個 REPL 迴圈。"""
    def __init__(self):
        self.interp = Interpreter()
        self.program_lines = []    # 目前編輯中的程式（一行一個字串）
        self.modified = False      # 有沒有未存檔的修改
        self.current_file = None

    # ── 輸入輔助 ──────────────────────────────────────────────────────────────

    def read_line(self, prompt=''):
        """【統一的讀一行】把 Ctrl+D 轉成 None、Ctrl+C 轉成 _CTRL_C 哨兵。"""
        try:
            return input(prompt)
        except EOFError:
            return None              # Ctrl+D / Ctrl+Z → 結束
        except KeyboardInterrupt:
            print("  ^C")
            return _CTRL_C           # 核心：Ctrl+C → 回傳哨兵，讓上層優雅取消

    def read_multiline(self, first_line):
        """【連續輸入】只要輸入還沒完整（如 { 沒收尾），就持續顯示 > 收集後續行。"""
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
        """【APPEND 指令｜含自動縮排額外功能】逐行輸入程式，以單獨一行 '.' 結束。"""
        start_line = len(self.program_lines) + 1
        print(f"(Enter lines; type '.' alone to finish. Auto-indent ON.)")
        lineno = start_line
        depth  = 0          # 目前縮排層數（看到 { 就 +1、} 就 -1）
        INDENT = 4          # 每層幾個空格
        DIM    = "\033[90m"
        RST    = "\033[0m"

        while True:
            # 深度提示（+4）放在 │ 後面只是顯示，不佔輸入空間，使用者可自由退格到最左
            hint = f"{DIM}+{depth*INDENT}{RST} " if depth > 0 else "  "
            raw = self.read_line(f"{lineno:4d}│{hint}")
            if raw is None or raw is _CTRL_C:
                print("(append cancelled)")
                return

            text = raw.strip()
            if text == '.':
                break

            # 以 '}' 開頭的行存的時候退一層，視覺上對齊開頭的 {
            store_depth = max(0, depth - 1) if text.startswith('}') else depth
            stored_line = (' ' * (store_depth * INDENT)) + text if text else ''  # 核心：存檔時補上空格縮排

            self.program_lines.append(stored_line)
            self.modified = True
            lineno += 1

            # 核心：依本行的 { } 數量更新下一行的縮排深度
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
        """【COLOR 指令｜額外功能】無參數 → 顯示主題預覽；有參數 → 切換語法高亮主題。"""
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
        """【指令分派中心】判斷輸入是內建指令還是 Small-C 程式碼，分別處理。"""
        line = raw.strip()
        if not line:
            return False

        upper = line.upper()
        parts = line.split(None, 1)
        cmd = parts[0].upper()              # 指令大小寫不敏感
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
            # 不是任何指令 → 當成 Small-C 程式碼，直接互動執行
            full_input = self.read_multiline(raw)   # 若括號未閉合，會繼續收行
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
        # 【REPL 主迴圈】讀一行 → 分派處理 → 重複，直到 QUIT 或 EOF
        while True:
            line = self.read_line(PROMPT)
            if line is None:          # Ctrl+D / Ctrl+Z（EOF）→ 結束
                print()
                print("Goodbye!")
                break
            if line is _CTRL_C:       # 核心：Ctrl+C → 什麼都不做，回到 sc> 提示符
                continue
            should_exit = self.dispatch(line)
            if should_exit:           # QUIT/EXIT 指令會回傳 True
                break


# ── 程式進入點 ────────────────────────────────────────────────────────────────
#
# 用法：
#   python main.py                  → 直接進入互動模式 sc>
#   python main.py prog.c           → 載入 prog.c 後進入互動模式（可繼續編輯/RUN）
#   python main.py --run prog.c     → 載入 prog.c、自動執行、印出結果後直接離開（批次模式）

if __name__ == '__main__':
    shell = Shell()
    args = sys.argv[1:]

    # 解析 --run 旗標（批次執行模式）
    run_mode = False
    if '--run' in args:
        run_mode = True
        args = [a for a in args if a != '--run']

    # 有給檔名就先載入
    if args:
        shell.cmd_load(args[0])
        if run_mode:
            shell.cmd_run()      # 批次模式：載入後直接執行
            sys.exit(0)          # 執行完就離開，不進互動模式（適合自動化測試）

    # 一般情況：進入互動 REPL
    shell.run()
