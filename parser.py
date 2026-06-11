# parser.py - Small-C 的「語法分析器 (Parser)」
#
# 【這個檔案的核心任務】
#   把 Lexer 吐出的 Token 串列，組成一棵語法樹 (AST)。
#   採用「遞迴下降 (Recursive Descent)」：每種語法寫一個 parse_xxx 函式，
#   彼此呼叫的「層次」剛好對應運算子的「優先順序」（見下方運算式區塊）。

from lexer import Lexer, TT, Token, LexError
from nodes import *

class ParseError(Exception):
    """語法錯誤；帶行號，方便回報是哪一行寫錯。"""
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
    """【語法分析器】拿著 Token 串列，用一個游標 pos 由前往後組成語法樹。"""
    def __init__(self, tokens):
        self.tokens = tokens   # Lexer 產生的 Token 串列
        self.pos = 0          # 目前看到第幾顆 token（核心游標）

    # ── Token 工具 ──────────────────────────────────────────────────────────

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
        """【斷言並前進】要求目前 token 必須是 tt，否則丟語法錯誤（如少了分號）。"""
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
        """【總入口】一直解析最上層項目，直到 EOF，全部裝進 Program。"""
        items = []
        while self.cur_type() != TT.EOF:
            item = self.parse_top_level()
            if item is not None:
                items.append(item)
        return Program(items)

    def parse_top_level(self):
        """判斷最上層這一段是 #define、函式/全域變數、還是直接的陳述句。"""
        tok = self.cur()
        # #define 常數
        if tok.type == TT.DEFINE:
            return self.parse_define()
        # 型別開頭 → 函式定義或全域變數宣告
        if tok.type in TYPE_TOKENS:
            return self.parse_func_or_global_var()
        # 其他 → 互動模式的頂層陳述句（for / while / if / 運算式…，免 main() 也能跑）
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
        """讀完「型別 + 名字」後，用下一顆 token 區分：( → 函式，其他 → 變數。"""
        line = self.cur().line
        type_tok = self.advance()
        base_type = type_tok.value   # 'int' | 'char' | 'void'

        is_pointer = False
        if self.cur_type() == TT.STAR:
            self.advance()
            is_pointer = True

        name_tok = self.expect(TT.IDENT, "Expected name")
        name = name_tok.value

        # 核心判斷：名字後面接 '(' → 是函式定義
        if self.cur_type() == TT.LPAREN:
            return self.parse_func_def(base_type, name, line)

        # 否則 → 全域變數宣告
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
        """【陳述句分派中心】看開頭 token，決定要解析成哪種陳述句。"""
        tok = self.cur()
        line = tok.line

        if tok.type == TT.SEMI:          # 空陳述句 ;
            self.advance()
            return None

        if tok.type == TT.LBRACE:        # { ... } 區塊
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

        # 以上都不是 → 當作「運算式 + 分號」（如 x = 5; 或 printf(...);）
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
        """【switch 解析｜加分功能】把每個 case 的值與其底下的陳述句收集成清單。"""
        line = self.cur().line
        self.advance()                          # 吃掉 'switch'
        self.expect(TT.LPAREN, "Expected '(' after switch")
        expr = self.parse_expr()
        self.expect(TT.RPAREN, "Expected ')' after switch expression")
        self.expect(TT.LBRACE, "Expected '{' to open switch body")

        cases = []          # 每項：(case 值節點, [該分支的陳述句])
        default_stmts = None

        # 核心：一直讀，直到 } 收尾；碰到 case / default 就開一個新分支
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

    # ── 運算式：用「函式呼叫層次」表達運算子優先順序 ─────────────────────────
    #
    # 【整個 parser 最精華的設計】
    #   越「晚」呼叫到的函式 = 越「高」優先順序（越先算）。呼叫鏈由低到高：
    #     parse_assign  (=  +=)     ← 優先順序最低
    #       parse_or    (||)
    #       parse_and   (&&)
    #       parse_bor / bxor / band (|  ^  &)
    #       parse_equality   (==  !=)
    #       parse_relational (<  <=  >  >=)
    #       parse_shift      (<<  >>)
    #       parse_additive   (+  -)
    #       parse_multiplicative (*  /  %)
    #       parse_unary  (-x  !x  *p  &x  ++x)
    #       parse_postfix (a[i]  f()  i++)
    #         parse_primary (數字 變數 (...))  ← 優先順序最高
    #   所以 1 + 2 * 3 會自動讓 * 先結合，不必另寫優先順序表。

    def parse_expr(self):
        return self.parse_assign()       # 從最低優先順序開始往下鑽

    def parse_assign(self):
        """指定 =、+= …（右結合：a = b = c 先算右邊）。"""
        line = self.cur().line
        left = self.parse_or()
        op_tok = self.cur()
        if op_tok.type in (TT.ASSIGN, TT.PLUS_ASSIGN, TT.MINUS_ASSIGN,
                           TT.STAR_ASSIGN, TT.SLASH_ASSIGN, TT.PERCENT_ASSIGN):
            self.advance()
            right = self.parse_assign()   # 遞迴自己 → 右結合
            return Assign(op_tok.value, left, right, line)
        return left

    def parse_or(self):
        # 【這以下每個二元運算函式都是同一個模式】
        #   1. 先向「更高優先順序」要左運算元
        #   2. 只要看到屬於本層的運算子，就再要右運算元，組成 BinaryOp
        #   3. 用 while + left=... 達成左結合（a-b-c = (a-b)-c）
        line = self.cur().line
        left = self.parse_and()                 # 左運算元（更高優先順序先算）
        while self.cur_type() == TT.OR:         # 本層運算子是 ||
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
        """【前置一元運算】-x、!x、~x、*p（取值）、&x（取址）、++x/--x。"""
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
        """【後置運算】處理緊跟在運算元後面的 a[i]（陣列）、f()（呼叫）、i++。"""
        line = self.cur().line
        expr = self.parse_primary()
        while True:
            tok = self.cur()
            if tok.type == TT.LBRACKET:           # a[i] 陣列存取
                self.advance()
                idx = self.parse_expr()
                self.expect(TT.RBRACKET)
                expr = ArrayAccess(expr, idx, line)
            elif tok.type == TT.INC:              # i++ 後置遞增
                self.advance()
                expr = PostfixOp('++', expr, line)
            elif tok.type == TT.DEC:              # i-- 後置遞減
                self.advance()
                expr = PostfixOp('--', expr, line)
            elif tok.type == TT.LPAREN and isinstance(expr, Ident):
                # 名字後面接 '(' → 函式呼叫 f(...)
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
        """【最高優先順序｜最基本單位】數字、字元、字串、變數名，或 ( 運算式 )。"""
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

        if tok.type == TT.LPAREN:        # 括號：強制提升優先順序，裡面重新從頭解析
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
    """【完整程式入口】原始碼字串 → Lexer 切 token → Parser 組樹 → 回傳 Program。"""
    lexer = Lexer(source, start_line)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse_program()

def parse_stmts(source, start_line=1):
    """【互動模式入口】解析 0 到多個陳述句（給 sc> 直接輸入用），回傳節點清單。"""
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
