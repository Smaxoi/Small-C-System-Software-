# nodes.py - AST node definitions for Small-C interpreter

class Node:
    pass

# ── Top-level ──────────────────────────────────────────────────────────────

class Program(Node):
    def __init__(self, items):
        self.items = items  # list of FuncDef | VarDecl | Define

class FuncDef(Node):
    def __init__(self, return_type, name, params, body, line=0):
        self.return_type = return_type   # 'int' | 'char' | 'void'
        self.name = name
        self.params = params             # list of Param
        self.body = body                 # Block
        self.line = line

class Param(Node):
    def __init__(self, type_, name, is_pointer=False, is_array=False):
        self.type_ = type_
        self.name = name
        self.is_pointer = is_pointer
        self.is_array = is_array         # int arr[] parameter

class Define(Node):
    def __init__(self, name, value, line=0):
        self.name = name
        self.value = value               # integer or string

# ── Statements ─────────────────────────────────────────────────────────────

class Block(Node):
    def __init__(self, stmts, line=0):
        self.stmts = stmts
        self.line = line

class VarDecl(Node):
    def __init__(self, type_, name, init=None, is_array=False,
                 array_size=None, is_pointer=False, line=0):
        self.type_ = type_
        self.name = name
        self.init = init
        self.is_array = is_array
        self.array_size = array_size     # expression or None
        self.is_pointer = is_pointer
        self.line = line

class If(Node):
    def __init__(self, cond, then_body, else_body=None, line=0):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body
        self.line = line

class While(Node):
    def __init__(self, cond, body, line=0):
        self.cond = cond
        self.body = body
        self.line = line

class For(Node):
    def __init__(self, init, cond, incr, body, line=0):
        self.init = init    # VarDecl | ExprStmt | None
        self.cond = cond
        self.incr = incr
        self.body = body
        self.line = line

class DoWhile(Node):
    def __init__(self, body, cond, line=0):
        self.body = body
        self.cond = cond
        self.line = line

class Break(Node):
    def __init__(self, line=0):
        self.line = line

class Continue(Node):
    def __init__(self, line=0):
        self.line = line

class Return(Node):
    def __init__(self, expr=None, line=0):
        self.expr = expr
        self.line = line

class ExprStmt(Node):
    def __init__(self, expr, line=0):
        self.expr = expr
        self.line = line

# ── Expressions ────────────────────────────────────────────────────────────

class Assign(Node):
    def __init__(self, op, target, value, line=0):
        self.op = op         # '=' | '+=' | '-=' | '*=' | '/=' | '%='
        self.target = target
        self.value = value
        self.line = line

class BinaryOp(Node):
    def __init__(self, op, left, right, line=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line

class UnaryOp(Node):
    def __init__(self, op, expr, line=0):
        self.op = op         # '-' | '!' | '~' | '++' | '--' | '*' | '&'
        self.expr = expr
        self.line = line

class PostfixOp(Node):
    def __init__(self, op, expr, line=0):
        self.op = op         # '++' | '--'
        self.expr = expr
        self.line = line

class FuncCall(Node):
    def __init__(self, name, args, line=0):
        self.name = name
        self.args = args
        self.line = line

class ArrayAccess(Node):
    def __init__(self, base, index, line=0):
        self.base = base     # expression (Ident or pointer expr)
        self.index = index
        self.line = line

class Ident(Node):
    def __init__(self, name, line=0):
        self.name = name
        self.line = line

class IntLit(Node):
    def __init__(self, value, line=0):
        self.value = value
        self.line = line

class CharLit(Node):
    def __init__(self, value, line=0):
        self.value = value   # integer (ASCII code)
        self.line = line

class StrLit(Node):
    def __init__(self, value, line=0):
        self.value = value   # Python string (escape sequences already decoded)
        self.line = line

class SwitchStmt(Node):
    """switch (expr) { case v: stmts... [break;] ... default: stmts... }"""
    def __init__(self, expr, cases, default_stmts, line=0):
        self.expr          = expr           # expression to switch on
        self.cases         = cases          # list of (value_expr, [stmt, ...])
        self.default_stmts = default_stmts  # list of stmts or None
        self.line          = line
