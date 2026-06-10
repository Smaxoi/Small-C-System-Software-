# lexer.py - Tokenizer for Small-C interpreter

import re

# ── Token types ────────────────────────────────────────────────────────────

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

KEYWORDS = {
    'int': TT.INT, 'char': TT.CHAR, 'void': TT.VOID,
    'if': TT.IF, 'else': TT.ELSE, 'while': TT.WHILE,
    'for': TT.FOR, 'do': TT.DO, 'break': TT.BREAK,
    'continue': TT.CONTINUE, 'return': TT.RETURN,
    'switch': TT.SWITCH, 'case': TT.CASE, 'default': TT.DEFAULT,
}

class Token:
    def __init__(self, type_, value, line=1):
        self.type = type_
        self.value = value
        self.line = line
    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, L{self.line})'

class LexError(Exception):
    def __init__(self, msg, line=0):
        super().__init__(msg)
        self.line = line

# ── Escape sequence decoder ────────────────────────────────────────────────

def decode_escape(s):
    """Decode a C escape sequence string (content between quotes)."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
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
    def __init__(self, text, start_line=1):
        self.text = text
        self.pos = 0
        self.line = start_line

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
        while self.pos < len(self.text):
            ch = self.peek()
            # Single-line comment
            if ch == '/' and self.peek(1) == '/':
                while self.pos < len(self.text) and self.peek() != '\n':
                    self.advance()
            # Block comment
            elif ch == '/' and self.peek(1) == '*':
                self.advance(); self.advance()  # consume /*
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
        """Read a double-quoted string literal."""
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
        """Read a single-quoted char literal, return integer value."""
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
        self.skip_whitespace_and_comments()
        if self.pos >= len(self.text):
            return Token(TT.EOF, None, self.line)

        line = self.line
        ch = self.peek()

        # Preprocessor directive
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

        # Number (decimal or hex)
        if ch.isdigit():
            start = self.pos
            if ch == '0' and self.peek(1) in ('x', 'X'):
                self.advance(); self.advance()  # skip 0x
                while self.pos < len(self.text) and (self.peek() in '0123456789abcdefABCDEF'):
                    self.advance()
                val = int(self.text[start:self.pos], 16)
            else:
                while self.pos < len(self.text) and self.peek().isdigit():
                    self.advance()
                val = int(self.text[start:self.pos])
            return Token(TT.INTLIT, val, line)

        # Identifier or keyword
        if ch.isalpha() or ch == '_':
            word = []
            while self.pos < len(self.text) and (self.peek().isalnum() or self.peek() == '_'):
                word.append(self.advance())
            name = ''.join(word)
            tt = KEYWORDS.get(name, TT.IDENT)
            return Token(tt, name, line)

        # Two-character operators
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

        # Skip unknown / non-ASCII characters (e.g. emoji, Chinese punctuation)
        if ord(ch) > 127:
            return None
        self.error(f"Unexpected character: {ch!r}")

    def tokenize(self):
        """Return list of all tokens."""
        tokens = []
        while True:
            tok = self.next_token()
            if tok is None:      # skip unknown non-ASCII chars (emoji etc.)
                continue
            tokens.append(tok)
            if tok.type == TT.EOF:
                break
        return tokens
