import re
from can_keywords import *

class can_token:
    def __init__(self, lineno: int, typ: TokenType, value: str):
        self.lineno = lineno
        self.typ = typ
        self.value = value

    def __repr__(self) -> str:
        return f"{self.value} ({self.typ.name})"

"""
    Get the Cantonese Token List
"""
class lexer:
    def __init__(self, code: str, keywords: tuple):
        self.code = code
        self.keywords = keywords
        self.line = 1
        self.re_number = r"^0[xX][0-9a-fA-F]*(\.[0-9a-fA-F]*)?([pP][+\-]?[0-9]+)?|^[0-9]*(\.[0-9]*)?([eE][+\-]?[0-9]+)?"
        self.re_id = r"^[_\d\w]+|^[\u4e00-\u9fa5]+"
        self.re_str = r"(?s)(^'(\\\\|\\'|\\\n|\\z\s*|[^'\n])*')|(^\"(\\\\|\\\"|\\\n|\\z\s*|[^\"\n])*\")"
        self.re_expr = r"[|][\S\s]*?[|]"
        self.re_python_expr = r"[~][\S\s]*?[#]"
        self.re_callfunc = r"[&](.*?)[)]"

    def next(self, n: int):
        self.code = self.code[n:]

    def check(self, s: str):
        return self.code.startswith(s)

    @staticmethod
    def is_white_space(c: str):
        return c in ('\t', '\n', '\v', '\f', '\r', ' ')

    @staticmethod
    def is_new_line(c: str):
        return c in ('\r', '\n')

    @staticmethod
    def isChinese(word: str):
        for ch in word:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

    def skip_space(self):
        while len(self.code) > 0:
            if self.check('\r\n') or self.check('\n\r'):
                self.next(2)
                self.line += 1
            elif lexer.is_new_line(self.code[0]):
                self.next(1)
                self.line += 1
            elif self.check('?') or self.check(':') or self.check('：') or self.check('？'):
                self.next(1)
            elif self.check('「') or self.check('」'):
                self.next(1)
            elif lexer.is_white_space(self.code[0]):
                self.next(1)
            else:
                break

    def scan(self, pattern: str):
        m = re.match(pattern, self.code)
        if m:
            token = m.group()
            self.next(len(token))
            return token
    
    def scan_identifier(self):
        return self.scan(self.re_id)

    def scan_expr(self):
        return self.scan(self.re_expr)

    def scan_python_expr(self):
        return self.scan(self.re_python_expr)

    def scan_number(self):
        return self.scan(self.re_number)

    def scan_callfunc(self):
        return self.scan(self.re_callfunc)

    def scan_short_string(self):
        m = re.match(self.re_str, self.code)
        if m:
            s = m.group()
            self.next(len(s))
            return s
        self.error('unfinished string')

    def error(self, args: str):
        err = '{0}: {1}'.format(self.line, args)
        raise Exception(err)

    def get_token(self) -> can_token:
        self.skip_space()
        if len(self.code) == 0:
            return can_token(self.line, TokenType.EOF, 'EOF')

        c = self.code[0]
        
        if c == '&':
            if self.check('&&'):
                self.next(2)
                return can_token(self.line, TokenType.KEYWORD, '&&')
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_BAND, '&')

        if c == '|':
            if self.check('|>'):
                self.next(2)
                return can_token(self.line, TokenType.SEPICFIC_ID_END, '|>')
            else:
                self.next(1)
                return can_token(self.line, TokenType.KEYWORD, '|')

        if c == '%':
            if self.check('%%'):
                self.next(2)
                return can_token(self.line, TokenType.KEYWORD, kw_func_end)
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_MOD, '%')

        if c == '~':
            token = self.scan_python_expr()
            return can_token(self.line, TokenType.EXTEND_EXPR, token)

        if c == '-':
            if self.check('->'):
                self.next(2)
                return can_token(self.line, TokenType.KEYWORD, kw_do)
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_MINUS, '-')

        if c == '=':
            if self.check('=>'):
                self.next(2)
                return can_token(self.line, TokenType.KEYWORD, kw_do)
            elif self.check('==>'):
                self.next(3)
                return can_token(self.line, TokenType.KEYWORD, '==>')
            elif self.check('=='):
                self.next(2)
                return can_token(self.line, TokenType.OP_EQ, '==')
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_ASSIGN, '=')
            
        if c == '$':
            if self.check('$$'):
                self.next(2)
                return can_token(self.line, TokenType.KEYWORD, '$$')
            self.next(1)
            return can_token(self.line, TokenType.KEYWORD, '$')

        if c == '<':
            if self.check('<*>'):
                self.next(3)
                return can_token(self.line, TokenType.KEYWORD, '<*>')

            elif self.check('<|>'):
                self.next(3)
                return can_token(self.line, TokenType.OP_BOR, '<|>')

            elif self.check('<->'):
                self.next(3)
                return can_token(self.line, TokenType.OP_CONCAT, '<->')

            elif self.check('<<<'):
                self.next(3)
                return can_token(self.line, TokenType.KEYWORD, '<<<')

            elif self.check('<$>'):
                self.next(3)
                return can_token(self.line, TokenType.KEYWORD, '<$>')

            elif self.check('<='):
                self.next(2)
                return can_token(self.line, TokenType.OP_LE, '<=')
            
            elif self.check('<<'):
                self.next(2)
                return can_token(self.line, TokenType.OP_SHL, '<<')

            elif self.check('<|'):
                self.next(2)
                return can_token(self.line, TokenType.SEPCIFIC_ID_BEG, '<|')

            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_LT, '<')
        
        if c == '>':
            if self.check('>>>'):
                self.next(3)
                return can_token(self.line, TokenType.KEYWORD, '>>>')
            elif self.check('>='):
                self.next(2)
                return can_token(self.line, TokenType.OP_GE, '>=')
            elif self.check('>>'):
                self.next(2)
                return can_token(self.line, TokenType.OP_SHR, '>>')
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_GT, '>')

        if c == '!':
            if self.check('!='):
                self.next(2)
                return can_token(self.line, TokenType.OP_NE, '!=')
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_NOT, '!')

        if c == '@':
            if self.check('@@@'):
                self.next(3)
                return can_token(self.line, TokenType.KEYWORD, '@@@')
            elif self.check('@@'):
                self.next(2)
                return can_token(self.line, TokenType.KEYWORD, '@@')
            else:
                self.next(1)
                return can_token(self.line, TokenType.KEYWORD, '@')
        
        if c == '{':
            self.next(1)
            return can_token(self.line, TokenType.SEP_LCURLY, '{')
        
        if c == '}':
            self.next(1)
            return can_token(self.line, TokenType.SEP_RCURLY, '}')

        if c == '(':
            self.next(1)
            return can_token(self.line, TokenType.SEP_LPAREN, '(')

        if c == ')':
            self.next(1)
            return can_token(self.line, TokenType.SEP_RPAREN, ')')

        if c == '[':
            self.next(1)
            return can_token(self.line, TokenType.SEP_LBRACK, '[')

        if c == ']':
            self.next(1)
            return can_token(self.line, TokenType.SEP_RBRACK, ']')

        if c == '.':
            self.next(1)
            return can_token(self.line, TokenType.SEP_DOT, c)

        if lexer.isChinese(c) or c == '_' or c.isalpha():
            token = self.scan_identifier()
            if token in self.keywords:
                return can_token(self.line, TokenType.KEYWORD, token)
            return can_token(self.line, TokenType.IDENTIFIER, token)
        
        if c in ('\'', '"'):
            return can_token(self.line, TokenType.STRING, self.scan_short_string())
        
        if c.isdigit():
            token = self.scan_number()
            return can_token(self.line, TokenType.NUM, token)

        if c == '+':
            self.next(1)
            return can_token(self.line, TokenType.OP_ADD, c)

        if c == '-':
            self.next(1)
            return can_token(self.line, TokenType.OP_MINUS, c)

        if c == '*':
            if self.check('**'):
                self.next(2)
                return can_token(self.line, TokenType.OP_POW, c)
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_MUL, c)

        if c == '/':
            if self.check('//'):
                self.next(2)
                return can_token(self.line, TokenType.OP_IDIV, '//')
            else:
                self.next(1)
                return can_token(self.line, TokenType.OP_DIV, c)

        if c == '&':
            self.next(1)
            return can_token(self.line, TokenType.OP_BAND, c)

        if c == '^':
            self.next(1)
            return can_token(self.line, TokenType.OP_WAVE, c)

        if c == ',':
            self.next(1)
            return can_token(self.line, TokenType.SEP_COMMA, ',')

        if c == '#':
            if self.check('##'):
                self.next(2)
                return can_token(self.line, TokenType.KEYWORD, '##')

        self.error("睇唔明嘅Token: " + c)

def cantonese_token(code : str) -> list:
    lex: lexer = lexer(code, keywords)
    tokens: list = []
    
    while True:
        token = lex.get_token()
        tokens.append(token)
        if token.typ == TokenType.EOF:
            break
    return tokens