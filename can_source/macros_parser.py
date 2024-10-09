from can_source.can_lexer import *
import can_source.can_ast as can_ast


class MacroParser:

    @classmethod
    def from_ParserFn(cls, F):
        cls.Fn = F
        return cls

    @classmethod
    def parse_meta_var(cls):
        """
        解析宏规则里面嘅元变量 eg: `@v: str`
        """
        cls.Fn.skip_once()
        _id = cls.Fn.eat_tk_by_kind(TokenType.IDENTIFIER)
        cls.Fn.eat_tk_by_value(":")
        frag_spec = cls.Fn.eat_tk_by_kind(TokenType.IDENTIFIER)
        meta_exp = can_ast.MacroMetaId(_id, frag_spec)
        return meta_exp

    @classmethod
    def parse_meta_rep_exp(cls):
        """
        解析宏规则里面嘅表达式 eg: `$(...)+`
        """
        cls.Fn.skip_once()
        cls.Fn.eat_tk_by_kind(TokenType.SEP_LPAREN)
        tokentree = []
        while cls.Fn.try_look_ahead().typ != TokenType.SEP_RPAREN:
            tokentree.append(cls.parse_macro_rule())
        cls.Fn.eat_tk_by_kind(TokenType.SEP_RPAREN)
        return cls.finish_meta_exp(tokentree)

    @classmethod
    def parse_meta_rep_stmt(cls):
        """
        解析宏定义(`block`)里面嘅表达式 eg: `$(...)+`
        """
        cls.Fn.skip_once()
        tokentree = cls.parse_tokentrees()
        return cls.finish_meta_exp(tokentree)

    @classmethod
    def parse_macro_rule(cls) -> list:
        next_tk = cls.Fn.try_look_ahead()
        if next_tk.value == "$":
            return cls.parse_meta_rep_exp()
        elif next_tk.value == "@":
            return cls.parse_meta_var()
        else:
            cls.Fn.skip_once()
            return next_tk

    @classmethod
    def finish_meta_exp(cls, meta_exp):
        next_tk = cls.Fn.try_look_ahead()
        meta_exp = can_ast.MacroMetaRepExp(meta_exp, None, None)
        if next_tk.value not in ["*", "+", "?"]:
            cls.Fn.skip_once()
            meta_exp.rep_sep = next_tk.value
            next_tk = cls.Fn.try_look_ahead()

        op_tk = cls.Fn.eat_tk_by_value(["*", "+", "?"])
        meta_exp.rep_op = op_tk.value
        return meta_exp

    @classmethod
    def parse_tokentrees(cls) -> list:
        tokentrees = []
        cls.Fn.eat_tk_by_kind(TokenType.SEP_LCURLY)
        while cls.Fn.try_look_ahead().typ != TokenType.SEP_RCURLY:
            next_tk = cls.Fn.try_look_ahead()
            if next_tk.typ == TokenType.SEP_LCURLY:
                tokentrees.append(cls.parse_tokentrees())
            elif next_tk.value == "@":
                cls.Fn.skip_once()
                meta_var = cls.Fn.eat_tk_by_kind(TokenType.IDENTIFIER)
                tokentrees.append(can_ast.MetaIdExp(meta_var.value))
            else:
                cls.Fn.skip_once()
                tokentrees.append(next_tk)
        cls.Fn.eat_tk_by_kind(TokenType.SEP_RCURLY)
        return can_ast.TokenTree(tokentrees)