# lexer.py - Small-C 的「詞法分析器 (Lexer / Tokenizer)」
#
# 【這個檔案的核心任務】
#   把原始碼字串  "int x = 5;"  切成一顆顆 Token：
#   [INT 'int'] [IDENT 'x'] [ASSIGN '='] [INTLIT 5] [SEMI ';']
#   這是編譯流程的第一步，產物交給 parser.py 組成語法樹。

import re

# ── Token 類型 ──────────────────────────────────────────────────────────────
# 把每種「最小語法單位」給一個代號（關鍵字、運算子、括號、數字…）

class TT:
    # Type keywords
    INT = 'INT'; CHAR = 'CHAR'; VOID = 'VOID'
    # Control flow
    IF = 'IF'; ELSE = 'ELSE'; WHILE = 'WHILE'; FOR = 'FOR'; DO = 'DO'
    BREAK = 'BREAK'; CONTINUE = 'CONTINUE'; RETURN = 'RETURN'
    SWITCH = 'SWITCH'; CASE = 'CASE'; DEFAULT = 'DEFAULT'; COLON = 'COLON'
    # Literals & identifier
    IDENT = 'IDENT'; INTLIT = 'INTLIT'; CHARLIT = 'CHARLIT'; STRLIT = 'STRLIT'
    # Arithmetic
    PLUS = 'PLUS'; MINUS = 'MINUS'; STAR = 'STAR'
    SLASH = 'SLASH'; PERCENT = 'PERCENT'
    # Comparison
    EQ = 'EQ'; NEQ = 'NEQ'; LT = 'LT'; LE = 'LE'; GT = 'GT'; GE = 'GE'
    # Logical
    AND = 'AND'; OR = 'OR'; NOT = 'NOT'
    # Bitwise
    BAND = 'BAND'; BOR = 'BOR'; BXOR = 'BXOR'; BNOT = 'BNOT'
    SHL = 'SHL'; SHR = 'SHR'
    # Assignment
    ASSIGN = 'ASSIGN'
    PLUS_ASSIGN = 'PLUS_ASSIGN'; MINUS_ASSIGN = 'MINUS_ASSIGN'
    STAR_ASSIGN = 'STAR_ASSIGN'; SLASH_ASSIGN = 'SLASH_ASSIGN'
    PERCENT_ASSIGN = 'PERCENT_ASSIGN'
    INC = 'INC'; DEC = 'DEC'
    # Delimiters
    LPAREN = 'LPAREN'; RPAREN = 'RPAREN'
    LBRACE = 'LBRACE'; RBRACE = 'RBRACE'
    LBRACKET = 'LBRACKET'; RBRACKET = 'RBRACKET'
    SEMI = 'SEMI'; COMMA = 'COMMA'
    # Preprocessor
    DEFINE = 'DEFINE'
    # Special
    EOF = 'EOF'

# 【保留字表】這些字長得像識別符，但其實是關鍵字 —— 查到就標成對應 token
KEYWORDS = {
    'int': TT.INT, 'char': TT.CHAR, 'void': TT.VOID,
    'if': TT.IF, 'else': TT.ELSE, 'while': TT.WHILE,
    'for': TT.FOR, 'do': TT.DO, 'break': TT.BREAK,
    'continue': TT.CONTINUE, 'return': TT.RETURN,
    'switch': TT.SWITCH, 'case': TT.CASE, 'default': TT.DEFAULT,  # switch/case 為加分功能
}

class Token:
    """一顆 Token：類型、值、在第幾行（行號用於錯誤訊息定位）。"""
    def __init__(self, type_, value, line=1):
        self.type = type_      # 是哪種 token（TT.INT、TT.PLUS…）
        self.value = value     # 實際內容（'int'、5、'+'…）
        self.line = line       # 出現在原始碼第幾行
    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, L{self.line})'

class LexError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.line = line

# ── Escape sequence decoder ────────────────────────────────────────────────

def decode_escape(s):
    """【跳脫字元解碼】把字面上的兩個字元 \\ + n 轉成真正的換行字元等。"""
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):   # 核心：遇到反斜線，看下一個字決定意義
            c = s[i + 1]
            i += 2
            if   c == 'n':  result.append('\n')
            elif c == 't':  result.append('\t')
            elif c == 'r':  result.append('\r')
            elif c == '0':  result.append('\0')
            elif c == '\\': result.append('\\')
            elif c == "'":  result.append("'")
            elif c == '"':  result.append('"')
            elif c == 'a':  result.append('\a')
            elif c == 'b':  result.append('\b')
            elif c == 'f':  result.append('\f')
            elif c == 'v':  result.append('\v')
            else:           result.append(c)
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)

# ── Tokenizer ──────────────────────────────────────────────────────────────

class Lexer:
    """【詞法分析器】掃過整段原始碼字串，吐出 Token 串列。"""
    def __init__(self, text, start_line=1):
        self.text = text          # 要掃描的原始碼
        self.pos = 0              # 目前掃到第幾個字元（核心游標）
        self.line = start_line    # 目前在第幾行（遇到 \n 就 +1）

    def error(self, msg):
        raise LexError(msg, self.line)

    def peek(self, offset=0):
        p = self.pos + offset
        return self.text[p] if p < len(self.text) else ''

    def advance(self):
        ch = self.text[self.pos]
        if ch == '\n':
            self.line += 1
        self.pos += 1
        return ch

    def skip_whitespace_and_comments(self):
        """【跳過空白與註解】這些東西不產生 Token，掃描時直接略過。"""
        while self.pos < len(self.text):
            ch = self.peek()
            # 單行註解 //：吃到行尾
            if ch == '/' and self.peek(1) == '/':
                while self.pos < len(self.text) and self.peek() != '\n':
                    self.advance()
            # 區塊註解 /* */：吃到 */ 為止
            elif ch == '/' and self.peek(1) == '*':
                self.advance(); self.advance()  # 吃掉 /*
                while self.pos < len(self.text):
                    if self.peek() == '*' and self.peek(1) == '/':
                        self.advance(); self.advance()
                        break
                    self.advance()
            elif ch in ' \t\r\n':
                self.advance()
            else:
                break

    def read_string(self):
        """【讀字串常數】吃到收尾的 " 為止；遇到換行未收尾就報錯。"""
        raw = []
        while self.pos < len(self.text):
            ch = self.peek()
            if ch == '"':
                self.advance()
                break
            if ch == '\\':
                raw.append(self.advance())
                if self.pos < len(self.text):
                    raw.append(self.advance())
            elif ch == '\n':
                self.error("Unterminated string literal")
            else:
                raw.append(self.advance())
        return decode_escape(''.join(raw))

    def read_char_literal(self):
        """【讀字元常數】'A' → 回傳 ASCII 整數 65（C 裡 char 就是小整數）。"""
        raw = []
        while self.pos < len(self.text):
            ch = self.peek()
            if ch == "'":
                self.advance()
                break
            if ch == '\\':
                raw.append(self.advance())
                if self.pos < len(self.text):
                    raw.append(self.advance())
            else:
                raw.append(self.advance())
        decoded = decode_escape(''.join(raw))
        if len(decoded) != 1:
            self.error(f"Invalid char literal")
        return ord(decoded)

    def next_token(self):
        """【整個 Lexer 的心臟】看目前字元，判斷它是哪種 token 並回傳一顆。"""
        self.skip_whitespace_and_comments()
        if self.pos >= len(self.text):
            return Token(TT.EOF, None, self.line)   # 掃完了 → 結束記號

        line = self.line
        ch = self.peek()        # 用「第一個字元」決定接下來怎麼讀

        # # 開頭 → 前置處理指令（目前只支援 #define）
        if ch == '#':
            self.advance()
            self.skip_whitespace_and_comments()
            word = []
            while self.pos < len(self.text) and (self.peek().isalnum() or self.peek() == '_'):
                word.append(self.advance())
            directive = ''.join(word)
            if directive == 'define':
                return Token(TT.DEFINE, 'define', line)
            self.error(f"Unknown preprocessor directive: #{directive}")

        # String literal
        if ch == '"':
            self.advance()
            s = self.read_string()
            return Token(TT.STRLIT, s, line)

        # Char literal
        if ch == "'":
            self.advance()
            v = self.read_char_literal()
            return Token(TT.CHARLIT, v, line)

        # 數字（十進位或 0x 十六進位）
        if ch.isdigit():
            start = self.pos
            if ch == '0' and self.peek(1) in ('x', 'X'):   # 核心：0x 開頭走 16 進位
                self.advance(); self.advance()  # 跳過 0x
                while self.pos < len(self.text) and (self.peek() in '0123456789abcdefABCDEF'):
                    self.advance()
                val = int(self.text[start:self.pos], 16)
            else:
                while self.pos < len(self.text) and self.peek().isdigit():
                    self.advance()
                val = int(self.text[start:self.pos])
            return Token(TT.INTLIT, val, line)

        # 識別符或關鍵字（字母/底線開頭）
        if ch.isalpha() or ch == '_':
            word = []
            while self.pos < len(self.text) and (self.peek().isalnum() or self.peek() == '_'):
                word.append(self.advance())
            name = ''.join(word)
            # 核心：查保留字表，是關鍵字就用關鍵字 token，否則當變數名 IDENT
            tt = KEYWORDS.get(name, TT.IDENT)
            return Token(tt, name, line)

        # 運算子與符號：先吃一個字，再看下一個字判斷是不是雙字元運算子（如 ++ == <=）
        self.advance()
        nch = self.peek()

        if ch == '+':
            if nch == '+': self.advance(); return Token(TT.INC, '++', line)
            if nch == '=': self.advance(); return Token(TT.PLUS_ASSIGN, '+=', line)
            return Token(TT.PLUS, '+', line)
        if ch == '-':
            if nch == '-': self.advance(); return Token(TT.DEC, '--', line)
            if nch == '=': self.advance(); return Token(TT.MINUS_ASSIGN, '-=', line)
            return Token(TT.MINUS, '-', line)
        if ch == '*':
            if nch == '=': self.advance(); return Token(TT.STAR_ASSIGN, '*=', line)
            return Token(TT.STAR, '*', line)
        if ch == '/':
            if nch == '=': self.advance(); return Token(TT.SLASH_ASSIGN, '/=', line)
            return Token(TT.SLASH, '/', line)
        if ch == '%':
            if nch == '=': self.advance(); return Token(TT.PERCENT_ASSIGN, '%=', line)
            return Token(TT.PERCENT, '%', line)
        if ch == '=':
            if nch == '=': self.advance(); return Token(TT.EQ, '==', line)
            return Token(TT.ASSIGN, '=', line)
        if ch == '!':
            if nch == '=': self.advance(); return Token(TT.NEQ, '!=', line)
            return Token(TT.NOT, '!', line)
        if ch == '<':
            if nch == '=': self.advance(); return Token(TT.LE, '<=', line)
            if nch == '<': self.advance(); return Token(TT.SHL, '<<', line)
            return Token(TT.LT, '<', line)
        if ch == '>':
            if nch == '=': self.advance(); return Token(TT.GE, '>=', line)
            if nch == '>': self.advance(); return Token(TT.SHR, '>>', line)
            return Token(TT.GT, '>', line)
        if ch == '&':
            if nch == '&': self.advance(); return Token(TT.AND, '&&', line)
            return Token(TT.BAND, '&', line)
        if ch == '|':
            if nch == '|': self.advance(); return Token(TT.OR, '||', line)
            return Token(TT.BOR, '|', line)
        if ch == '^': return Token(TT.BXOR, '^', line)
        if ch == '~': return Token(TT.BNOT, '~', line)
        if ch == '(': return Token(TT.LPAREN, '(', line)
        if ch == ')': return Token(TT.RPAREN, ')', line)
        if ch == '{': return Token(TT.LBRACE, '{', line)
        if ch == '}': return Token(TT.RBRACE, '}', line)
        if ch == '[': return Token(TT.LBRACKET, '[', line)
        if ch == ']': return Token(TT.RBRACKET, ']', line)
        if ch == ';': return Token(TT.SEMI, ';', line)
        if ch == ',': return Token(TT.COMMA, ',', line)
        if ch == ':': return Token(TT.COLON, ':', line)

        # 【容錯】非 ASCII 字元（emoji、中文標點）回傳 None → 由 tokenize() 略過，避免整個崩潰
        if ord(ch) > 127:
            return None
        self.error(f"Unexpected character: {ch!r}")

    def tokenize(self):
        """【對外入口】重複呼叫 next_token，直到 EOF，回傳整串 Token。"""
        tokens = []
        while True:
            tok = self.next_token()
            if tok is None:      # 略過無法辨識的非 ASCII 字元（emoji 等）
                continue
            tokens.append(tok)
            if tok.type == TT.EOF:   # 讀到結束記號就收工
                break
        return tokens
