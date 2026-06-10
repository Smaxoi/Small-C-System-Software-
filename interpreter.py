# interpreter.py - Tree-walking interpreter for Small-C

import sys
import math
import random

from nodes import *
from memory import Memory, Scope, VarInfo
from parser import parse_source, parse_stmts, ParseError

# ── Control flow signals ───────────────────────────────────────────────────

class BreakSignal(Exception):    pass
class ContinueSignal(Exception): pass
class ReturnSignal(Exception):
    def __init__(self, value=0): self.value = value
class ExitSignal(Exception):
    def __init__(self, code=0):  self.code = code
class RuntimeError_(Exception):
    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.line = line

# ── Interpreter ────────────────────────────────────────────────────────────

class Interpreter:
    def __init__(self):
        self.mem = Memory()
        self.global_scope = Scope()          # global / interactive scope
        self.defines = {}                    # #define constants
        self.user_funcs = {}                 # name -> FuncDef node
        self.trace = False
        self.program_lines = []              # stored program lines (for TRACE)
        self.output_buffer = []              # collects print output (optional)
        self._string_cache = {}             # literal -> addr (reuse literals)

    def reset_runtime(self):
        """Reset memory and scope but keep program structure."""
        self.mem.reset()
        self.global_scope = Scope()
        self._string_cache.clear()

    # ── String literal allocation ──────────────────────────────────────────

    def alloc_string(self, s):
        if s in self._string_cache:
            return self._string_cache[s]
        addr = self.mem.alloc_string_literal(s)
        self._string_cache[s] = addr
        return addr

    # ── Error context display ──────────────────────────────────────────────

    def _show_error_context(self, line_no, source_lines):
        """Print the source line that caused an error, with a marker."""
        if not source_lines or not line_no:
            return
        if 1 <= line_no <= len(source_lines):
            content = source_lines[line_no - 1]
            stripped = content.strip()
            if stripped:
                indent = len(content) - len(content.lstrip())
                print(f"  {'─'*40}")
                print(f"  {line_no:4d} │  {stripped}")
                print(f"       │  {'─' * len(stripped)} ↑ 錯誤位置")
                print(f"  {'─'*40}")

    # ── Loading and registering a program ─────────────────────────────────

    def register_program(self, program_node):
        """Register all #defines and function defs from a Program node."""
        for item in program_node.items:
            if isinstance(item, Define):
                self._register_define(item)
            elif isinstance(item, FuncDef):
                self.user_funcs[item.name] = item

    def _register_define(self, node):
        if isinstance(node.value, int):
            self.defines[node.name] = node.value
        elif isinstance(node.value, str):
            # Value might be another define name
            if node.value in self.defines:
                self.defines[node.name] = self.defines[node.value]
            else:
                try:
                    self.defines[node.name] = int(node.value)
                except ValueError:
                    self.defines[node.name] = 0

    # ── Run a full program ─────────────────────────────────────────────────

    def run_program(self, source, program_lines=None):
        """Parse, register, and run main(). Returns exit code."""
        if program_lines:
            self.program_lines = program_lines
        try:
            prog = parse_source(source)
        except ParseError as e:
            print(f"Syntax error: line {e.line}: {e}")
            return 1

        # Reset runtime state (memory, scopes) but keep defines/user_funcs
        self.mem.reset()
        self._string_cache.clear()
        self.global_scope = Scope()
        self.user_funcs.clear()
        self.defines.clear()

        self.register_program(prog)

        # Execute global variable declarations
        for item in prog.items:
            if isinstance(item, VarDecl):
                self._exec_var_decl(item, self.global_scope)
            elif isinstance(item, Define):
                self._register_define(item)

        # Collect any top-level executable statements (not decls / funcs / defines)
        top_stmts = [item for item in prog.items
                     if not isinstance(item, (VarDecl, FuncDef, Define))]

        if 'main' not in self.user_funcs:
            if not top_stmts:
                print("Error: no main() function defined.")
                return 1
            # Run top-level statements directly (script style)
            try:
                for stmt in top_stmts:
                    self._exec_stmt(stmt, self.global_scope)
                print(f"Program exited with return value 0.")
                return 0
            except ReturnSignal as e:
                code = e.value if e.value is not None else 0
                print(f"Program exited with return value {code}.")
                return code
            except ExitSignal as e:
                print(f"Program exited with return value {e.code}.")
                return e.code
            except RuntimeError_ as e:
                print(f"Runtime error: {e}")
                return 1

        try:
            ret = self._call_func('main', [])
            code = ret if ret is not None else 0
            print(f"Program exited with return value {code}.")
            return code
        except ExitSignal as e:
            print(f"Program exited with return value {e.code}.")
            return e.code
        except RuntimeError_ as e:
            print(f"Runtime error: {e}")
            return 1

    # ── Check program syntax ───────────────────────────────────────────────

    def check_program(self, source):
        """Parse source, return list of error strings (empty = no errors)."""
        errors = []
        try:
            parse_source(source)
        except ParseError as e:
            errors.append(f"Line {e.line}: {e}")
        return errors

    # ── Interactive execution (single statement or declaration) ───────────

    def exec_interactive(self, source):
        """Execute one or more statements/declarations in interactive scope."""
        src_lines = source.split('\n')
        try:
            items = parse_stmts(source)
        except ParseError as e:
            print(f"Syntax error: line {e.line}: {e}")
            self._show_error_context(e.line, src_lines)
            return

        for item in items:
            try:
                if isinstance(item, Define):
                    self._register_define(item)
                elif isinstance(item, FuncDef):
                    self.user_funcs[item.name] = item
                elif isinstance(item, VarDecl):
                    self._exec_var_decl(item, self.global_scope)
                else:
                    self._exec_stmt(item, self.global_scope)
            except RuntimeError_ as e:
                line_info = f" at line {e.line}" if e.line else ""
                print(f"Runtime error{line_info}: {e}")
                self._show_error_context(e.line, src_lines)
            except ExitSignal as e:
                print(f"Program exited with return value {e.code}.")
            except ReturnSignal:
                pass  # return at top level; ignore

    # ── Statement executor ─────────────────────────────────────────────────

    def _exec_stmt(self, node, scope):
        if node is None:
            return

        if (self.trace and hasattr(node, 'line') and node.line > 0
                and not isinstance(node, Block)):
            line_content = ''
            if self.program_lines and 0 < node.line <= len(self.program_lines):
                line_content = self.program_lines[node.line - 1].strip()
            print(f"[line {node.line}] {line_content}")

        if isinstance(node, Block):
            self._exec_block(node, scope)
        elif isinstance(node, VarDecl):
            self._exec_var_decl(node, scope)
        elif isinstance(node, If):
            self._exec_if(node, scope)
        elif isinstance(node, While):
            self._exec_while(node, scope)
        elif isinstance(node, For):
            self._exec_for(node, scope)
        elif isinstance(node, DoWhile):
            self._exec_do_while(node, scope)
        elif isinstance(node, SwitchStmt):
            self._exec_switch(node, scope)
        elif isinstance(node, Break):
            raise BreakSignal()
        elif isinstance(node, Continue):
            raise ContinueSignal()
        elif isinstance(node, Return):
            val = 0
            if node.expr is not None:
                val = self._eval(node.expr, scope)
            raise ReturnSignal(val)
        elif isinstance(node, ExprStmt):
            self._eval(node.expr, scope)
        elif isinstance(node, Define):
            self._register_define(node)
        elif isinstance(node, FuncDef):
            self.user_funcs[node.name] = node
        else:
            raise RuntimeError_(f"Unknown statement node: {type(node).__name__}")

    def _exec_block(self, node, parent_scope):
        block_scope = Scope(parent_scope)
        for stmt in node.stmts:
            if stmt is not None:
                self._exec_stmt(stmt, block_scope)

    def _exec_var_decl(self, node, scope):
        # Resolve #define for array size
        if node.is_array:
            if node.array_size is None:
                size = 1
            else:
                size = self._eval(node.array_size, scope)
            if size <= 0:
                raise RuntimeError_(f"Invalid array size {size}", node.line)
            addr = self.mem.alloc(size)
            info = VarInfo(node.type_, addr, size=size, is_array=True)
            scope.define(node.name, info)
            # Initialize char array from string literal if provided
            if node.init is not None:
                init_val = self._eval(node.init, scope)
                if isinstance(init_val, int):
                    # pointer to string literal
                    s = self.mem.read_string(init_val)
                    self.mem.write_string(addr, s)
        else:
            addr = self.mem.alloc(1)
            is_ptr = node.is_pointer
            info = VarInfo(node.type_, addr, is_pointer=is_ptr)
            scope.define(node.name, info)
            if node.init is not None:
                init_val = self._eval(node.init, scope)
                self.mem.write(addr, init_val)

    def _exec_if(self, node, scope):
        cond = self._eval(node.cond, scope)
        if cond:
            self._exec_stmt(node.then_body, scope)
        elif node.else_body is not None:
            self._exec_stmt(node.else_body, scope)

    def _exec_while(self, node, scope):
        while self._eval(node.cond, scope):
            try:
                self._exec_stmt(node.body, scope)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _exec_for(self, node, scope):
        for_scope = Scope(scope)
        if node.init is not None:
            self._exec_stmt(node.init, for_scope)
        while True:
            if node.cond is not None:
                if not self._eval(node.cond, for_scope):
                    break
            try:
                self._exec_stmt(node.body, for_scope)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            if node.incr is not None:
                self._eval(node.incr, for_scope)

    def _exec_do_while(self, node, scope):
        while True:
            try:
                self._exec_stmt(node.body, scope)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            if not self._eval(node.cond, scope):
                break

    def _exec_switch(self, node, scope):
        val = self._eval(node.expr, scope)
        matched = False
        try:
            for case_val_node, stmts in node.cases:
                if not matched:
                    case_val = self._eval(case_val_node, scope)
                    if val == case_val:
                        matched = True
                if matched:
                    for s in stmts:
                        self._exec_stmt(s, scope)
            if not matched and node.default_stmts is not None:
                for s in node.default_stmts:
                    self._exec_stmt(s, scope)
        except BreakSignal:
            pass   # break exits the switch

    # ── Expression evaluator ───────────────────────────────────────────────

    def _eval(self, node, scope):
        """Evaluate expression node; return integer value."""

        if isinstance(node, IntLit):
            return node.value

        if isinstance(node, CharLit):
            return node.value

        if isinstance(node, StrLit):
            return self.alloc_string(node.value)

        if isinstance(node, Ident):
            # Check #define first
            if node.name in self.defines:
                return self.defines[node.name]
            info = scope.lookup(node.name)
            if info is None:
                raise RuntimeError_(f"Undefined variable '{node.name}'", node.line)
            if info.is_array:
                return info.addr   # array decays to pointer
            return self.mem.read(info.addr)

        if isinstance(node, ArrayAccess):
            base_addr = self._eval_array_base(node.base, scope)
            idx = self._eval(node.index, scope)
            # Bounds check for named arrays
            name = self._get_array_name(node.base)
            if name:
                info = scope.lookup(name)
                if info and info.is_array:
                    if not (0 <= idx < info.size):
                        raise RuntimeError_(
                            f"array index out of bounds (index {idx}, size {info.size})",
                            node.line)
            target_addr = base_addr + idx
            if not self.mem.valid(target_addr):
                raise RuntimeError_(
                    f"Invalid array access at index {idx}", node.line)
            return self.mem.read(target_addr)

        if isinstance(node, UnaryOp):
            return self._eval_unary(node, scope)

        if isinstance(node, PostfixOp):
            return self._eval_postfix(node, scope)

        if isinstance(node, BinaryOp):
            return self._eval_binary(node, scope)

        if isinstance(node, Assign):
            return self._eval_assign(node, scope)

        if isinstance(node, FuncCall):
            return self._eval_func_call(node, scope)

        raise RuntimeError_(f"Unknown expression node: {type(node).__name__}", 0)

    def _get_array_name(self, node):
        if isinstance(node, Ident):
            return node.name
        return None

    def _eval_array_base(self, node, scope):
        """Get base address for array/pointer access."""
        if isinstance(node, Ident):
            if node.name in self.defines:
                return self.defines[node.name]
            info = scope.lookup(node.name)
            if info is None:
                raise RuntimeError_(f"Undefined variable '{node.name}'", node.line)
            if info.is_array:
                return info.addr
            # Pointer: read its value (which is an address)
            return self.mem.read(info.addr)
        # General expression (e.g., pointer arithmetic result)
        return self._eval(node, scope)

    def _eval_lvalue(self, node, scope):
        """Return (address, is_in_bounds_checked) for an lvalue node."""
        if isinstance(node, Ident):
            info = scope.lookup(node.name)
            if info is None:
                raise RuntimeError_(f"Undefined variable '{node.name}'", node.line)
            return info.addr
        if isinstance(node, ArrayAccess):
            base = self._eval_array_base(node.base, scope)
            idx = self._eval(node.index, scope)
            name = self._get_array_name(node.base)
            if name:
                info = scope.lookup(name)
                if info and info.is_array:
                    if not (0 <= idx < info.size):
                        raise RuntimeError_(
                            f"array index out of bounds (index {idx}, size {info.size})",
                            node.line)
            return base + idx
        if isinstance(node, UnaryOp) and node.op == '*':
            ptr_val = self._eval(node.expr, scope)
            return ptr_val
        raise RuntimeError_(f"Not an lvalue: {type(node).__name__}", 0)

    def _eval_unary(self, node, scope):
        op = node.op
        if op == '-':
            return -self._eval(node.expr, scope)
        if op == '!':
            return 0 if self._eval(node.expr, scope) else 1
        if op == '~':
            return ~self._eval(node.expr, scope) & 0xFFFFFFFF
        if op == '&':
            # Address-of
            return self._eval_lvalue(node.expr, scope)
        if op == '*':
            # Dereference
            addr = self._eval(node.expr, scope)
            if not self.mem.valid(addr):
                raise RuntimeError_(f"Null/invalid pointer dereference", node.line)
            return self.mem.read(addr)
        if op == '++pre':
            addr = self._eval_lvalue(node.expr, scope)
            val = self.mem.read(addr) + 1
            self.mem.write(addr, val)
            return val
        if op == '--pre':
            addr = self._eval_lvalue(node.expr, scope)
            val = self.mem.read(addr) - 1
            self.mem.write(addr, val)
            return val
        raise RuntimeError_(f"Unknown unary op: {op}", node.line)

    def _eval_postfix(self, node, scope):
        addr = self._eval_lvalue(node.expr, scope)
        val = self.mem.read(addr)
        if node.op == '++':
            self.mem.write(addr, val + 1)
        else:
            self.mem.write(addr, val - 1)
        return val  # postfix returns old value

    def _eval_binary(self, node, scope):
        op = node.op
        # Short-circuit evaluation
        if op == '&&':
            left = self._eval(node.left, scope)
            if not left:
                return 0
            right = self._eval(node.right, scope)
            return 1 if right else 0
        if op == '||':
            left = self._eval(node.left, scope)
            if left:
                return 1
            right = self._eval(node.right, scope)
            return 1 if right else 0

        left = self._eval(node.left, scope)
        right = self._eval(node.right, scope)

        if op == '+':  return left + right
        if op == '-':  return left - right
        if op == '*':  return left * right
        if op == '/':
            if right == 0:
                raise RuntimeError_("division by zero", node.line)
            # C integer division (truncate toward zero)
            return int(left / right)
        if op == '%':
            if right == 0:
                raise RuntimeError_("Modulo by zero", node.line)
            return int(left - int(left / right) * right)
        if op == '==': return 1 if left == right else 0
        if op == '!=': return 1 if left != right else 0
        if op == '<':  return 1 if left < right else 0
        if op == '<=': return 1 if left <= right else 0
        if op == '>':  return 1 if left > right else 0
        if op == '>=': return 1 if left >= right else 0
        if op == '&':  return left & right
        if op == '|':  return left | right
        if op == '^':  return left ^ right
        if op == '<<': return (left << right) & 0xFFFFFFFF
        if op == '>>': return left >> right
        raise RuntimeError_(f"Unknown binary op: {op}", node.line)

    def _eval_assign(self, node, scope):
        addr = self._eval_lvalue(node.target, scope)
        rval = self._eval(node.value, scope)
        op = node.op
        if op == '=':
            new_val = rval
        else:
            old_val = self.mem.read(addr)
            if   op == '+=': new_val = old_val + rval
            elif op == '-=': new_val = old_val - rval
            elif op == '*=': new_val = old_val * rval
            elif op == '/=':
                if rval == 0: raise RuntimeError_("division by zero", node.line)
                new_val = int(old_val / rval)
            elif op == '%=':
                if rval == 0: raise RuntimeError_("Modulo by zero", node.line)
                new_val = int(old_val - int(old_val / rval) * rval)
            else:
                raise RuntimeError_(f"Unknown assignment op: {op}", node.line)
        self.mem.write(addr, new_val)
        return new_val

    # ── Function calls ─────────────────────────────────────────────────────

    def _eval_func_call(self, node, scope):
        name = node.name
        args = node.args

        # Built-in functions
        builtin = self._get_builtin(name)
        if builtin is not None:
            return builtin(node, args, scope)

        # User-defined function
        if name not in self.user_funcs:
            raise RuntimeError_(f"Undefined function '{name}'", node.line)
        return self._call_func(name, args, scope, node.line)

    def _call_func(self, name, args, caller_scope=None, line=0):
        func = self.user_funcs[name]
        func_scope = Scope(self.global_scope, func_name=name)

        # Bind parameters
        for i, param in enumerate(func.params):
            if i < len(args):
                if caller_scope is not None:
                    # Evaluate argument in caller's scope
                    arg_node = args[i] if not isinstance(args[i], int) else None
                    if arg_node is not None:
                        arg_val = self._eval(arg_node, caller_scope)
                    else:
                        arg_val = args[i]
                else:
                    arg_val = args[i] if isinstance(args[i], int) else 0
            else:
                arg_val = 0

            addr = self.mem.alloc(1)
            is_ptr = param.is_pointer or param.is_array
            info = VarInfo(param.type_, addr, is_pointer=is_ptr)
            func_scope.define(param.name, info)
            self.mem.write(addr, arg_val)

        # Execute function body
        try:
            self._exec_block(func.body, func_scope)
            return 0  # no explicit return
        except ReturnSignal as r:
            return r.value

    # ── Built-in functions ─────────────────────────────────────────────────

    def _get_builtin(self, name):
        builtins = {
            'printf':   self._bi_printf,
            'scanf':    self._bi_scanf,
            'putchar':  self._bi_putchar,
            'getchar':  self._bi_getchar,
            'puts':     self._bi_puts,
            'strlen':   self._bi_strlen,
            'strcpy':   self._bi_strcpy,
            'strcat':   self._bi_strcat,
            'strcmp':   self._bi_strcmp,
            'strncpy':  self._bi_strncpy,
            'atoi':     self._bi_atoi,
            'itoa':     self._bi_itoa,
            'substr':   self._bi_substr,
            'abs':      self._bi_abs,
            'max':      self._bi_max,
            'min':      self._bi_min,
            'pow':      self._bi_pow,
            'sqrt':     self._bi_sqrt,
            'rand':     self._bi_rand,
            'srand':    self._bi_srand,
            'memset':   self._bi_memset,
            'sizeof':   self._bi_sizeof,
            'isalpha':  self._bi_isalpha,
            'isdigit':  self._bi_isdigit,
            'isupper':  self._bi_isupper,
            'islower':  self._bi_islower,
            'toupper':  self._bi_toupper,
            'tolower':  self._bi_tolower,
            'isspace':  self._bi_isspace,
            'exit':     self._bi_exit,
            'strrev':   self._bi_strrev,
            'strtok':   self._bi_strtok,
        }
        return builtins.get(name)

    def _eval_args(self, args, scope):
        return [self._eval(a, scope) for a in args]

    # I/O
    def _bi_printf(self, node, args, scope):
        if not args:
            raise RuntimeError_("printf: missing format string", node.line)
        fmt_addr = self._eval(args[0], scope)
        fmt = self.mem.read_string(fmt_addr)
        arg_vals = [self._eval(a, scope) for a in args[1:]]
        result = self._format_string(fmt, arg_vals, scope)
        sys.stdout.write(result)
        sys.stdout.flush()
        return len(result)

    def _format_string(self, fmt, arg_vals, scope=None):
        """Format a C printf-style format string.
        Supports: %d %c %s %x %X %o %%
        Flags:    - (left-align)  0 (zero-pad)
        Width:    %5d  %-5d  %05d
        """
        result = []
        i = 0
        ai = 0
        while i < len(fmt):
            c = fmt[i]
            if c != '%' or i + 1 >= len(fmt):
                result.append(c); i += 1; continue

            i += 1  # skip '%'

            # ── Parse flags ────────────────────────────────────────────────
            left_align = False
            zero_pad   = False
            while i < len(fmt) and fmt[i] in ('-', '0', '+', ' ', '#'):
                if fmt[i] == '-': left_align = True
                if fmt[i] == '0': zero_pad   = True
                i += 1

            # ── Parse width ────────────────────────────────────────────────
            width = 0
            while i < len(fmt) and fmt[i].isdigit():
                width = width * 10 + int(fmt[i]); i += 1

            if i >= len(fmt):
                break
            spec = fmt[i]; i += 1

            # ── Apply format ───────────────────────────────────────────────
            def pad(s, numeric=False):
                if width <= 0:
                    return s
                if left_align:
                    return s.ljust(width)
                if zero_pad and numeric:
                    neg = s.startswith('-')
                    digits = s[1:] if neg else s
                    padded = digits.zfill(width - (1 if neg else 0))
                    return ('-' + padded) if neg else padded
                return s.rjust(width)

            if spec == 'd':
                val = arg_vals[ai] if ai < len(arg_vals) else 0
                result.append(pad(str(val), numeric=True)); ai += 1
            elif spec == 'c':
                val = arg_vals[ai] if ai < len(arg_vals) else 0
                result.append(pad(chr(val & 0xFF))); ai += 1
            elif spec == 's':
                addr = arg_vals[ai] if ai < len(arg_vals) else 0
                result.append(pad(self.mem.read_string(addr))); ai += 1
            elif spec == 'x':
                val = arg_vals[ai] if ai < len(arg_vals) else 0
                s = hex(val & 0xFFFFFFFF)[2:]
                result.append(pad(s, numeric=True)); ai += 1
            elif spec == 'X':
                val = arg_vals[ai] if ai < len(arg_vals) else 0
                s = hex(val & 0xFFFFFFFF)[2:].upper()
                result.append(pad(s, numeric=True)); ai += 1
            elif spec == 'o':
                val = arg_vals[ai] if ai < len(arg_vals) else 0
                result.append(pad(oct(val)[2:], numeric=True)); ai += 1
            elif spec == '%':
                result.append('%')
            else:
                result.append('%'); result.append(spec)

        return ''.join(result)

    def _bi_scanf(self, node, args, scope):
        if not args:
            return 0
        fmt_addr = self._eval(args[0], scope)
        fmt = self.mem.read_string(fmt_addr)
        count = 0
        ai = 1
        i = 0
        while i < len(fmt) and ai < len(args):
            c = fmt[i]
            if c == '%' and i + 1 < len(fmt):
                spec = fmt[i + 1]
                try:
                    line_in = input()
                except EOFError:
                    break
                addr = self._eval_lvalue(args[ai], scope)
                if spec == 'd':
                    self.mem.write(addr, int(line_in.strip()))
                elif spec == 'c':
                    ch = line_in[0] if line_in else '\0'
                    self.mem.write(addr, ord(ch))
                elif spec == 's':
                    self.mem.write_string(addr, line_in.strip())
                count += 1
                ai += 1; i += 2
            else:
                i += 1
        return count

    def _bi_putchar(self, node, args, scope):
        v = self._eval(args[0], scope) if args else 0
        sys.stdout.write(chr(v & 0xFF))
        sys.stdout.flush()
        return v

    def _bi_getchar(self, node, args, scope):
        try:
            ch = sys.stdin.read(1)
            return ord(ch) if ch else -1
        except Exception:
            return -1

    def _bi_puts(self, node, args, scope):
        if args:
            addr = self._eval(args[0], scope)
            s = self.mem.read_string(addr)
            print(s)
        return 0

    # String
    def _bi_strlen(self, node, args, scope):
        addr = self._eval(args[0], scope)
        return len(self.mem.read_string(addr))

    def _bi_strcpy(self, node, args, scope):
        dst = self._eval(args[0], scope)
        src = self._eval(args[1], scope)
        s = self.mem.read_string(src)
        self.mem.write_string(dst, s)
        return dst

    def _bi_strcat(self, node, args, scope):
        dst = self._eval(args[0], scope)
        src = self._eval(args[1], scope)
        existing = self.mem.read_string(dst)
        appended = self.mem.read_string(src)
        self.mem.write_string(dst, existing + appended)
        return dst

    def _bi_strcmp(self, node, args, scope):
        a = self.mem.read_string(self._eval(args[0], scope))
        b = self.mem.read_string(self._eval(args[1], scope))
        if a < b: return -1
        if a > b: return 1
        return 0

    def _bi_strncpy(self, node, args, scope):
        dst = self._eval(args[0], scope)
        src = self._eval(args[1], scope)
        n = self._eval(args[2], scope)
        s = self.mem.read_string(src)[:n]
        self.mem.write_string(dst, s)
        return dst

    def _bi_atoi(self, node, args, scope):
        addr = self._eval(args[0], scope)
        s = self.mem.read_string(addr).strip()
        try:
            return int(s)
        except ValueError:
            return 0

    def _bi_itoa(self, node, args, scope):
        n = self._eval(args[0], scope)
        buf = self._eval(args[1], scope)
        self.mem.write_string(buf, str(n))
        return buf

    def _bi_substr(self, node, args, scope):
        dst = self._eval(args[0], scope)
        src = self._eval(args[1], scope)
        start = self._eval(args[2], scope)
        length = self._eval(args[3], scope)
        s = self.mem.read_string(src)
        sub = s[start:start + length]
        self.mem.write_string(dst, sub)
        return dst

    # Math
    def _bi_abs(self, node, args, scope):
        return abs(self._eval(args[0], scope))

    def _bi_max(self, node, args, scope):
        a = self._eval(args[0], scope)
        b = self._eval(args[1], scope)
        return a if a > b else b

    def _bi_min(self, node, args, scope):
        a = self._eval(args[0], scope)
        b = self._eval(args[1], scope)
        return a if a < b else b

    def _bi_pow(self, node, args, scope):
        base = self._eval(args[0], scope)
        exp = self._eval(args[1], scope)
        if exp < 0:
            raise RuntimeError_("pow: negative exponent not supported", node.line)
        return int(base ** exp)

    def _bi_sqrt(self, node, args, scope):
        x = self._eval(args[0], scope)
        if x < 0:
            raise RuntimeError_("sqrt: argument must be non-negative", node.line)
        return int(math.isqrt(x))

    def _bi_rand(self, node, args, scope):
        return random.randint(0, 32767)

    def _bi_srand(self, node, args, scope):
        seed = self._eval(args[0], scope)
        random.seed(seed)
        return 0

    # Utility
    def _bi_memset(self, node, args, scope):
        ptr = self._eval(args[0], scope)
        val = self._eval(args[1], scope) & 0xFF
        size = self._eval(args[2], scope)
        for i in range(size):
            if self.mem.valid(ptr + i):
                self.mem.write(ptr + i, val)
        return ptr

    def _bi_sizeof(self, node, args, scope):
        # sizeof(expr) - evaluate to type size
        if not args:
            return 0
        arg = args[0]
        if isinstance(arg, Ident):
            info = scope.lookup(arg.name)
            if info:
                return 1 if info.type_ == 'char' else 4
        return 4  # default

    def _bi_isalpha(self, node, args, scope):
        c = self._eval(args[0], scope) & 0xFF
        return 1 if chr(c).isalpha() else 0

    def _bi_isdigit(self, node, args, scope):
        c = self._eval(args[0], scope) & 0xFF
        return 1 if chr(c).isdigit() else 0

    def _bi_isupper(self, node, args, scope):
        c = self._eval(args[0], scope) & 0xFF
        return 1 if chr(c).isupper() else 0

    def _bi_islower(self, node, args, scope):
        c = self._eval(args[0], scope) & 0xFF
        return 1 if chr(c).islower() else 0

    def _bi_toupper(self, node, args, scope):
        c = self._eval(args[0], scope) & 0xFF
        return ord(chr(c).upper())

    def _bi_tolower(self, node, args, scope):
        c = self._eval(args[0], scope) & 0xFF
        return ord(chr(c).lower())

    def _bi_isspace(self, node, args, scope):
        c = self._eval(args[0], scope) & 0xFF
        return 1 if chr(c).isspace() else 0

    def _bi_exit(self, node, args, scope):
        code = self._eval(args[0], scope) if args else 0
        raise ExitSignal(code)

    def _bi_strrev(self, node, args, scope):
        """strrev(dst, src) — reverse src into dst; also returns dst addr."""
        if len(args) < 2:
            raise RuntimeError_("strrev: expected 2 arguments", node.line)
        dst_addr = self._eval(args[0], scope)
        src_addr = self._eval(args[1], scope)
        s = self.mem.read_string(src_addr)
        self.mem.write_string(dst_addr, s[::-1])
        return dst_addr

    # strtok state
    _strtok_str  = ""
    _strtok_pos  = 0

    def _bi_strtok(self, node, args, scope):
        """strtok(str, delim) — C-style tokenizer; pass 0/NULL for continuation."""
        if len(args) < 2:
            raise RuntimeError_("strtok: expected 2 arguments", node.line)
        str_val  = self._eval(args[0], scope)
        delim_addr = self._eval(args[1], scope)
        delim = self.mem.read_string(delim_addr)
        if str_val != 0:
            self._strtok_str = self.mem.read_string(str_val)
            self._strtok_pos = 0
        s   = self._strtok_str
        pos = self._strtok_pos
        # skip leading delimiters
        while pos < len(s) and s[pos] in delim:
            pos += 1
        if pos >= len(s):
            return 0  # NULL
        start = pos
        while pos < len(s) and s[pos] not in delim:
            pos += 1
        token = s[start:pos]
        self._strtok_pos = pos + 1
        addr = self.alloc_string(token)
        return addr

    # ── VARS display ───────────────────────────────────────────────────────

    def show_vars(self, scope=None):
        if scope is None:
            scope = self.global_scope
        all_vars = scope.all_vars()
        if not all_vars:
            print("(no variables)")
            return
        for name, info in sorted(all_vars.items()):
            if info.is_array:
                elements = []
                for i in range(info.size):
                    try:
                        elements.append(str(self.mem.read(info.addr + i)))
                    except Exception:
                        elements.append('?')
                print(f"  {info.type_} {name}[{info.size}] = {{{', '.join(elements)}}}")
            else:
                try:
                    val = self.mem.read(info.addr)
                except Exception:
                    val = '?'
                type_str = info.type_
                if info.is_pointer:
                    type_str += '*'
                if info.type_ == 'char' and isinstance(val, int) and 32 <= val <= 126:
                    print(f"  {type_str} {name} = {val} ('{chr(val)}')")
                else:
                    print(f"  {type_str} {name} = {val}")

    # ── MEMSHOW display ────────────────────────────────────────────────────

    def show_memory(self, scope=None):
        """Display memory layout: named variables + string literals."""
        if scope is None:
            scope = self.global_scope

        all_vars = scope.all_vars()

        if not self.mem.cells:
            print("(memory is empty)")
            return

        total   = len(self.mem.cells)
        lo      = min(self.mem.cells)
        hi      = max(self.mem.cells)
        W_TYPE  = 10
        W_NAME  = 18

        print(f"Memory Layout  ({total} cells allocated, "
              f"0x{lo:04x} – 0x{hi:04x})")
        print("─" * 62)
        print(f"  {'Address':8}  {'Type':{W_TYPE}}  {'Variable':{W_NAME}}  Value")
        print("─" * 62)

        printed = set()

        # ── Named variables (sorted by address) ──────────────────────────
        for name, info in sorted(all_vars.items(), key=lambda kv: kv[1].addr):
            a = info.addr

            if info.is_array:
                if info.type_ == 'char':
                    # Read as C-string
                    try:
                        s = self.mem.read_string(a)
                        val_str = f'"{s}"'
                    except Exception:
                        val_str = '?'
                    tlabel = f"char[{info.size}]"
                else:
                    # Show up to 8 elements
                    elems = []
                    for j in range(min(info.size, 8)):
                        try:
                            elems.append(str(self.mem.read(a + j)))
                        except Exception:
                            elems.append('?')
                    if info.size > 8:
                        elems.append(f'...+{info.size - 8}')
                    val_str = '{' + ', '.join(elems) + '}'
                    tlabel = f"int[{info.size}]"
                print(f"  0x{a:04x}    {tlabel:{W_TYPE}}  {name:{W_NAME}}  {val_str}")
                for j in range(info.size):
                    printed.add(a + j)

            elif info.is_pointer:
                try:
                    val = self.mem.read(a)
                    val_str = f"→ 0x{val:04x}"
                except Exception:
                    val_str = '?'
                tlabel = f"{info.type_}*"
                print(f"  0x{a:04x}    {tlabel:{W_TYPE}}  {name:{W_NAME}}  {val_str}")
                printed.add(a)

            else:
                try:
                    val = self.mem.read(a)
                except Exception:
                    val = '?'
                tlabel = info.type_
                if info.type_ == 'char' and isinstance(val, int) and 32 <= val <= 126:
                    val_str = f"{val}  ('{chr(val)}')"
                else:
                    val_str = str(val)
                print(f"  0x{a:04x}    {tlabel:{W_TYPE}}  {name:{W_NAME}}  {val_str}")
                printed.add(a)

        # ── String literals ───────────────────────────────────────────────
        if self._string_cache:
            print("─" * 62)
            print(f"  {'String literals':}")
            for s, addr in sorted(self._string_cache.items(), key=lambda x: x[1]):
                preview = (s[:28] + '…') if len(s) > 28 else s
                print(f"  0x{addr:04x}    {'literal':{W_TYPE}}  "
                      f"{'[str]':{W_NAME}}  {preview!r}")
                for j in range(len(s) + 1):
                    printed.add(addr + j)

        # ── Untracked cells ───────────────────────────────────────────────
        hidden = len(self.mem.cells) - len(printed & self.mem.cells.keys())
        if hidden > 0:
            print(f"  ... ({hidden} internal cells not shown)")
        print("─" * 62)

    # ── FUNCS display ──────────────────────────────────────────────────────

    def show_funcs(self):
        print("User-defined functions:")
        if not self.user_funcs:
            print("  (none)")
        else:
            for fname, fdef in sorted(self.user_funcs.items()):
                params_parts = []
                for p in fdef.params:
                    if p.is_pointer:
                        params_parts.append(f"{p.type_} *{p.name}")
                    else:
                        params_parts.append(f"{p.type_} {p.name}")
                params_str = ', '.join(params_parts)
                print(f"  {fdef.return_type} {fname}({params_str})   line {fdef.line}")

        print("Built-in functions:")
        builtins_list = [
            "  -- I/O --",
            "  void printf(char *fmt, ...)                        [built-in]",
            "  int  scanf(char *fmt, ...)                         [built-in]",
            "  int  putchar(int c)                                [built-in]",
            "  int  getchar()                                     [built-in]",
            "  void puts(char *s)                                 [built-in]",
            "  -- String --",
            "  int  strlen(char *s)                               [built-in]",
            "  void strcpy(char *dst, char *src)                  [built-in]",
            "  void strcat(char *dst, char *src)                  [built-in]",
            "  int  strcmp(char *s1, char *s2)                    [built-in]",
            "  void strncpy(char *dst, char *src, int n)          [built-in]",
            "  void substr(char *dst, char *src, int pos, int n)  [built-in]",
            "  void strrev(char *dst, char *src)                  [built-in]",
            "  char *strtok(char *str, char *delim)               [built-in]",
            "  int  atoi(char *s)                                 [built-in]",
            "  void itoa(int n, char *buf)                        [built-in]",
            "  -- Math --",
            "  int  abs(int x)                                    [built-in]",
            "  int  max(int a, int b)                             [built-in]",
            "  int  min(int a, int b)                             [built-in]",
            "  int  pow(int base, int exp)                        [built-in]",
            "  int  sqrt(int x)                                   [built-in]",
            "  int  rand()                                        [built-in]",
            "  void srand(int seed)                               [built-in]",
            "  -- Char --",
            "  int  isalpha(int c)                                [built-in]",
            "  int  isdigit(int c)                                [built-in]",
            "  int  isspace(int c)                                [built-in]",
            "  int  isupper(int c)                                [built-in]",
            "  int  islower(int c)                                [built-in]",
            "  int  toupper(int c)                                [built-in]",
            "  int  tolower(int c)                                [built-in]",
            "  -- Memory / Misc --",
            "  void memset(void *ptr, int val, int n)             [built-in]",
            "  void exit(int code)                                [built-in]",
        ]
        for line in builtins_list:
            print(line)
