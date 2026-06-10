# parser.py - Recursive-descent parser for Small-C

from lexer import Lexer, TT, Token, LexError
from nodes import *

class ParseError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.line = line

TYPE_TOKENS = (TT.INT, TT.CHAR, TT.VOID)

# ── 人類可讀的 token 標籤（用於錯誤訊息）──────────────────────────────────────
_TT_LABEL = {
    TT.SEMI:      "';'",  TT.COMMA:    "','",  TT.COLON:    "':'",
    TT.LPAREN:    "'('",  TT.RPAREN:   "')'",
    TT.LBRACE:   "'{'",   TT.RBRACE:   "'}'",
    TT.LBRACKET: "'['",   TT.RBRACKET: "']'",
    TT.ASSIGN:    "'='",
    TT.PLUS:      "'+'",  TT.MINUS:    "'-'",
    TT.STAR:      "'*'",  TT.SLASH:    "'/'",  TT.PERCENT: "'%'",
    TT.LT:        "'<'",  TT.GT:       "'>'",
    TT.EQ:        "'=='", TT.NEQ:      "'!='",
    TT.LE:        "'<='", TT.GE:       "'>='",
    TT.AND:       "'&&'", TT.OR:       "'||'", TT.NOT:     "'!'",
    TT.BAND:      "'&'",  TT.BOR:      "'|'",  TT.BXOR:   "'^'",
    TT.BNOT:      "'~'",  TT.SHL:      "'<<'", TT.SHR:    "'>>'",
    TT.INC:       "'++'", TT.DEC:      "'--'",
    TT.EOF:       'end of file',
}

def _tt_label(tt):
    """回傳 token type 的人類可讀標籤，用於錯誤訊息。"""
    if tt in _TT_LABEL:
        return _TT_LABEL[tt]
    return f"'{tt.lower()}'"   # 關鍵字：RETURN → 'return'

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ── Token utilities ────────────────────────────────────────────────────

    def peek(self, offset=0):
        p = self.pos + offset
        if p < len(self.tokens):
            return self.tokens[p]
        return self.tokens[-1]  # EOF

    def cur(self):
        return self.peek(0)

    def cur_type(self):
        return self.cur().type

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, tt, msg=None):
        if self.cur_type() != tt:
            tok = self.cur()
            raise ParseError(
                msg or f"expected {_tt_label(tt)}, got {tok.value!r}",
                tok.line)
        return self.advance()

    def match(self, *types):
        if self.cur_type() in types:
            return self.advance()
        return None

    def error(self, msg=None):
        tok = self.cur()
        raise ParseError(msg or f"unexpected token {tok.value!r}", tok.line)

    # ── Top-level program ──────────────────────────────────────────────────

    def parse_program(self):
        items = []
        while self.cur_type() != TT.EOF:
            item = self.parse_top_level()
            if item is not None:
                items.append(item)
        return Program(items)

    def parse_top_level(self):
        tok = self.cur()
        # #define constant
        if tok.type == TT.DEFINE:
            return self.parse_define()
        # Function definition or global variable declaration
        if tok.type in TYPE_TOKENS:
            return self.parse_func_or_global_var()
        # Interactive / top-level statements (for, while, if, expr, ...)
        stmt = self.parse_stmt()
        return stmt

    def parse_define(self):
        line = self.cur().line
        self.advance()  # consume DEFINE
        name_tok = self.expect(TT.IDENT, "Expected identifier after #define")
        # Value: integer literal, hex literal, or identifier
        val_tok = self.cur()
        if val_tok.type == TT.INTLIT:
            value = self.advance().value
        elif val_tok.type == TT.MINUS:
            self.advance()
            value = -self.expect(TT.INTLIT, "Expected number after -").value
        elif val_tok.type == TT.IDENT:
            value = self.advance().value  # will be resolved at runtime
        else:
            value = 0
        return Define(name_tok.value, value, line)

    def parse_func_or_global_var(self):
        line = self.cur().line
        type_tok = self.advance()
        base_type = type_tok.value   # 'int' | 'char' | 'void'

        is_pointer = False
        if self.cur_type() == TT.STAR:
            self.advance()
            is_pointer = True

        name_tok = self.expect(TT.IDENT, "Expected name")
        name = name_tok.value

        # Function definition
        if self.cur_type() == TT.LPAREN:
            return self.parse_func_def(base_type, name, line)

        # Global variable declaration
        return self.parse_var_decl_tail(base_type, name, is_pointer, line)

    def parse_func_def(self, return_type, name, line):
        self.expect(TT.LPAREN)
        params = self.parse_params()
        self.expect(TT.RPAREN)
        body = self.parse_block()
        return FuncDef(return_type, name, params, body, line)

    def parse_params(self):
        params = []
        if self.cur_type() == TT.RPAREN:
            return params
        if self.cur_type() == TT.VOID and self.peek(1).type == TT.RPAREN:
            self.advance()
            return params
        while True:
            if self.cur_type() not in TYPE_TOKENS:
                break
            ptype_tok = self.advance()
            ptype = ptype_tok.value
            is_ptr = False
            is_arr = False
            if self.cur_type() == TT.STAR:
                self.advance()
                is_ptr = True
            pname_tok = self.expect(TT.IDENT, "Expected parameter name")
            pname = pname_tok.value
            # Handle arr[] parameter syntax
            if self.cur_type() == TT.LBRACKET:
                self.advance()
                self.expect(TT.RBRACKET)
                is_arr = True
                is_ptr = True
            params.append(Param(ptype, pname, is_ptr, is_arr))
            if self.cur_type() != TT.COMMA:
                break
            self.advance()  # consume comma
        return params

    # ── Statements ─────────────────────────────────────────────────────────

    def parse_block(self):
        line = self.cur().line
        self.expect(TT.LBRACE)
        stmts = []
        while self.cur_type() not in (TT.RBRACE, TT.EOF):
            stmt = self.parse_stmt()
            if stmt is not None:
                stmts.append(stmt)
        self.expect(TT.RBRACE)
        return Block(stmts, line)

    def parse_stmt(self):
        tok = self.cur()
        line = tok.line

        if tok.type == TT.SEMI:
            self.advance()
            return None

        if tok.type == TT.LBRACE:
            return self.parse_block()

        if tok.type == TT.DEFINE:
            return self.parse_define()

        if tok.type in TYPE_TOKENS:
            return self.parse_var_decl_stmt()

        if tok.type == TT.IF:
            return self.parse_if()

        if tok.type == TT.WHILE:
            return self.parse_while()

        if tok.type == TT.FOR:
            return self.parse_for()

        if tok.type == TT.DO:
            return self.parse_do_while()

        if tok.type == TT.SWITCH:
            return self.parse_switch()

        if tok.type == TT.BREAK:
            self.advance()
            self.expect(TT.SEMI)
            return Break(line)

        if tok.type == TT.CONTINUE:
            self.advance()
            self.expect(TT.SEMI)
            return Continue(line)

        if tok.type == TT.RETURN:
            self.advance()
            if self.cur_type() == TT.SEMI:
                self.advance()
                return Return(None, line)
            expr = self.parse_expr()
            self.expect(TT.SEMI)
            return Return(expr, line)

        # Expression statement
        expr = self.parse_expr()
        self.expect(TT.SEMI)
        return ExprStmt(expr, line)

    def parse_var_decl_stmt(self):
        line = self.cur().line
        type_tok = self.advance()
        base_type = type_tok.value

        is_pointer = False
        if self.cur_type() == TT.STAR:
            self.advance()
            is_pointer = True

        name_tok = self.expect(TT.IDENT, "Expected variable name")
        name = name_tok.value

        decl = self.parse_var_decl_tail(base_type, name, is_pointer, line)
        return decl

    def parse_var_decl_tail(self, base_type, name, is_pointer, line):
        # Array: int arr[SIZE] or int arr[10]
        is_array = False
        array_size = None
        if self.cur_type() == TT.LBRACKET:
            self.advance()
            is_array = True
            if self.cur_type() != TT.RBRACKET:
                array_size = self.parse_expr()
            self.expect(TT.RBRACKET)

        # Optional initializer
        init = None
        if self.cur_type() == TT.ASSIGN:
            self.advance()
            init = self.parse_expr()

        self.expect(TT.SEMI)
        return VarDecl(base_type, name, init, is_array, array_size, is_pointer, line)

    def parse_if(self):
        line = self.cur().line
        self.advance()  # consume 'if'
        self.expect(TT.LPAREN)
        cond = self.parse_expr()
        self.expect(TT.RPAREN)
        then_body = self.parse_stmt_or_block()
        else_body = None
        if self.cur_type() == TT.ELSE:
            self.advance()
            else_body = self.parse_stmt_or_block()
        return If(cond, then_body, else_body, line)

    def parse_while(self):
        line = self.cur().line
        self.advance()
        self.expect(TT.LPAREN)
        cond = self.parse_expr()
        self.expect(TT.RPAREN)
        body = self.parse_stmt_or_block()
        return While(cond, body, line)

    def parse_for(self):
        line = self.cur().line
        self.advance()
        self.expect(TT.LPAREN)

        # Init
        init = None
        if self.cur_type() != TT.SEMI:
            if self.cur_type() in TYPE_TOKENS:
                init = self.parse_var_decl_stmt()
            else:
                init = ExprStmt(self.parse_expr(), self.cur().line)
                self.expect(TT.SEMI)
        else:
            self.advance()

        # Condition
        cond = None
        if self.cur_type() != TT.SEMI:
            cond = self.parse_expr()
        self.expect(TT.SEMI)

        # Increment
        incr = None
        if self.cur_type() != TT.RPAREN:
            incr = self.parse_expr()
        self.expect(TT.RPAREN)

        body = self.parse_stmt_or_block()
        return For(init, cond, incr, body, line)

    def parse_do_while(self):
        line = self.cur().line
        self.advance()  # consume 'do'
        body = self.parse_stmt_or_block()
        self.expect(TT.WHILE)
        self.expect(TT.LPAREN)
        cond = self.parse_expr()
        self.expect(TT.RPAREN)
        self.expect(TT.SEMI)
        return DoWhile(body, cond, line)

    def parse_switch(self):
        line = self.cur().line
        self.advance()                          # consume 'switch'
        self.expect(TT.LPAREN, "Expected '(' after switch")
        expr = self.parse_expr()
        self.expect(TT.RPAREN, "Expected ')' after switch expression")
        self.expect(TT.LBRACE, "Expected '{' to open switch body")

        cases = []          # list of (value_node, [stmts])
        default_stmts = None

        while self.cur_type() not in (TT.RBRACE, TT.EOF):
            if self.cur_type() == TT.CASE:
                self.advance()
                val = self.parse_expr()
                self.expect(TT.COLON, "Expected ':' after case value")
                stmts = []
                while self.cur_type() not in (TT.CASE, TT.DEFAULT, TT.RBRACE, TT.EOF):
                    s = self.parse_stmt()
                    if s is not None:
                        stmts.append(s)
                cases.append((val, stmts))
            elif self.cur_type() == TT.DEFAULT:
                self.advance()
                self.expect(TT.COLON, "Expected ':' after default")
                stmts = []
                while self.cur_type() not in (TT.CASE, TT.RBRACE, TT.EOF):
                    s = self.parse_stmt()
                    if s is not None:
                        stmts.append(s)
                default_stmts = stmts
            else:
                self.advance()   # skip unexpected token

        self.expect(TT.RBRACE, "Expected '}' to close switch body")
        return SwitchStmt(expr, cases, default_stmts, line)

    def parse_stmt_or_block(self):
        if self.cur_type() == TT.LBRACE:
            return self.parse_block()
        return self.parse_stmt()

    # ── Expressions (precedence climbing) ─────────────────────────────────

    def parse_expr(self):
        return self.parse_assign()

    def parse_assign(self):
        line = self.cur().line
        left = self.parse_or()
        op_tok = self.cur()
        if op_tok.type in (TT.ASSIGN, TT.PLUS_ASSIGN, TT.MINUS_ASSIGN,
                           TT.STAR_ASSIGN, TT.SLASH_ASSIGN, TT.PERCENT_ASSIGN):
            self.advance()
            right = self.parse_assign()
            return Assign(op_tok.value, left, right, line)
        return left

    def parse_or(self):
        line = self.cur().line
        left = self.parse_and()
        while self.cur_type() == TT.OR:
            op = self.advance().value
            right = self.parse_and()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_and(self):
        line = self.cur().line
        left = self.parse_bor()
        while self.cur_type() == TT.AND:
            op = self.advance().value
            right = self.parse_bor()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_bor(self):
        line = self.cur().line
        left = self.parse_bxor()
        while self.cur_type() == TT.BOR:
            op = self.advance().value
            right = self.parse_bxor()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_bxor(self):
        line = self.cur().line
        left = self.parse_band()
        while self.cur_type() == TT.BXOR:
            op = self.advance().value
            right = self.parse_band()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_band(self):
        line = self.cur().line
        left = self.parse_equality()
        while self.cur_type() == TT.BAND:
            op = self.advance().value
            right = self.parse_equality()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_equality(self):
        line = self.cur().line
        left = self.parse_relational()
        while self.cur_type() in (TT.EQ, TT.NEQ):
            op = self.advance().value
            right = self.parse_relational()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_relational(self):
        line = self.cur().line
        left = self.parse_shift()
        while self.cur_type() in (TT.LT, TT.LE, TT.GT, TT.GE):
            op = self.advance().value
            right = self.parse_shift()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_shift(self):
        line = self.cur().line
        left = self.parse_additive()
        while self.cur_type() in (TT.SHL, TT.SHR):
            op = self.advance().value
            right = self.parse_additive()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_additive(self):
        line = self.cur().line
        left = self.parse_multiplicative()
        while self.cur_type() in (TT.PLUS, TT.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_multiplicative(self):
        line = self.cur().line
        left = self.parse_unary()
        while self.cur_type() in (TT.STAR, TT.SLASH, TT.PERCENT):
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOp(op, left, right, line)
        return left

    def parse_unary(self):
        line = self.cur().line
        tok = self.cur()
        if tok.type == TT.MINUS:
            self.advance()
            expr = self.parse_unary()
            return UnaryOp('-', expr, line)
        if tok.type == TT.NOT:
            self.advance()
            expr = self.parse_unary()
            return UnaryOp('!', expr, line)
        if tok.type == TT.BNOT:
            self.advance()
            expr = self.parse_unary()
            return UnaryOp('~', expr, line)
        if tok.type == TT.STAR:
            self.advance()
            expr = self.parse_unary()
            return UnaryOp('*', expr, line)
        if tok.type == TT.BAND:
            self.advance()
            expr = self.parse_unary()
            return UnaryOp('&', expr, line)
        if tok.type == TT.INC:
            self.advance()
            expr = self.parse_unary()
            return UnaryOp('++pre', expr, line)
        if tok.type == TT.DEC:
            self.advance()
            expr = self.parse_unary()
            return UnaryOp('--pre', expr, line)
        return self.parse_postfix()

    def parse_postfix(self):
        line = self.cur().line
        expr = self.parse_primary()
        while True:
            tok = self.cur()
            if tok.type == TT.LBRACKET:
                self.advance()
                idx = self.parse_expr()
                self.expect(TT.RBRACKET)
                expr = ArrayAccess(expr, idx, line)
            elif tok.type == TT.INC:
                self.advance()
                expr = PostfixOp('++', expr, line)
            elif tok.type == TT.DEC:
                self.advance()
                expr = PostfixOp('--', expr, line)
            elif tok.type == TT.LPAREN and isinstance(expr, Ident):
                # Function call
                self.advance()
                args = self.parse_args()
                self.expect(TT.RPAREN)
                expr = FuncCall(expr.name, args, line)
            else:
                break
        return expr

    def parse_args(self):
        args = []
        if self.cur_type() == TT.RPAREN:
            return args
        args.append(self.parse_expr())
        while self.cur_type() == TT.COMMA:
            self.advance()
            args.append(self.parse_expr())
        return args

    def parse_primary(self):
        tok = self.cur()
        line = tok.line

        if tok.type == TT.INTLIT:
            self.advance()
            return IntLit(tok.value, line)

        if tok.type == TT.CHARLIT:
            self.advance()
            return CharLit(tok.value, line)

        if tok.type == TT.STRLIT:
            self.advance()
            return StrLit(tok.value, line)

        if tok.type == TT.IDENT:
            self.advance()
            return Ident(tok.value, line)

        if tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TT.RPAREN)
            return expr

        # sizeof special form
        if tok.type == TT.IDENT and tok.value == 'sizeof':
            self.advance()
            self.expect(TT.LPAREN)
            inner = self.cur()
            if inner.type in TYPE_TOKENS:
                tname = self.advance().value
                # sizeof(int) = 4, sizeof(char) = 1
                val = 4 if tname == 'int' else 1
            else:
                var_expr = self.parse_expr()
                val = None  # resolved at runtime
            self.expect(TT.RPAREN)
            if val is not None:
                return IntLit(val, line)
            return FuncCall('sizeof', [var_expr], line)

        self.error(f"Expected expression, got {tok.type} ({tok.value!r})")


# ── Convenience functions ──────────────────────────────────────────────────

def parse_source(source, start_line=1):
    """Parse a complete Small-C program source string. Returns Program node."""
    lexer = Lexer(source, start_line)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse_program()

def parse_stmts(source, start_line=1):
    """Parse zero or more statements (for interactive mode). Returns list of nodes."""
    lexer = Lexer(source, start_line)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    stmts = []
    while parser.cur_type() != TT.EOF:
        tok = parser.cur()
        # Could be a #define, type decl, or statement
        if tok.type == TT.DEFINE:
            stmts.append(parser.parse_define())
        elif tok.type in TYPE_TOKENS:
            # Peek: if it's a function definition, parse as func def
            # otherwise parse as variable declaration
            saved_pos = parser.pos
            try:
                item = parser.parse_func_or_global_var()
                stmts.append(item)
            except Exception:
                parser.pos = saved_pos
                stmts.append(parser.parse_stmt())
        else:
            stmt = parser.parse_stmt()
            if stmt is not None:
                stmts.append(stmt)
    return stmts
