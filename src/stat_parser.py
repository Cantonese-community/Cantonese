from can_lexer import *
from Ast import can_ast
from parser_base import *
from can_utils import ParserUtil, exp_type
from exp_parser import ExpParser, ClassBlockExpParser

class StatParser(ParserBase):
    def __init__(self, token_list : list, expParser = ExpParser) -> None:
        super(StatParser, self).__init__(token_list)
        self.pos = 0
        self.tokens = token_list

        # Function address type:
        # We can choose the class `ExpParser` Or `ClassBlockExpParser`
        self.ExpParser = expParser

    def getExpParser(self):
        return self.ExpParser(self.tokens[self.pos : ])

    def parse(self):
        tk = self.current()
        kind = ParserUtil.get_type(tk)
        tk_value = ParserUtil.get_token_value(tk)
        if kind == TokenType.KEYWORD:
            if tk_value in [kw_print]:
                return self.parse_print_stat()
            
            elif tk_value in [kw_exit, kw_exit_1, kw_exit_2]:
                return self.parse_exit_stat()
            
            elif tk_value in [kw_assign]:
                return self.parse_assign_stat()
            
            elif tk_value in [kw_if]:
                return self.parse_if_stat()
            
            elif tk_value in [kw_import]:
                return self.parse_import_stat()
            
            elif tk_value == kw_global_set:
                return self.parse_global_stat()
            
            elif tk_value in [kw_break]:
                return self.parse_break_stat()

            elif tk_value in [kw_continue]:
                return self.parse_continue_stat()
            
            elif tk_value in [kw_while_do]:
                return self.parse_while_stat()
            
            elif tk_value == '|':
                self.skip(1)
                if ParserUtil.get_token_value(self.current()) == '|':
                    prefix_exps = []
                    skip_step = 0
                else:
                    exp_parser = self.ExpParser(self.tokens[self.pos : ])
                    prefix_exps = exp_parser.parse_exp_list()
                    skip_step = exp_parser.pos # we will skip it in parse_for_stat
                    del exp_parser
                
                self.get_next_token_of('|', skip_step)

                if ParserUtil.get_token_value(self.look_ahead(skip_step)) in [kw_from]:
                    return self.parse_for_stat(prefix_exps, skip_step)
                
                elif ParserUtil.get_token_value(self.look_ahead(skip_step)) in [kw_call_begin]:
                    return self.parse_func_call_stat(prefix_exps, skip_step)
                
                elif ParserUtil.get_token_value(self.look_ahead(skip_step)) in [kw_lst_assign]:
                    return self.parse_list_assign_stat(prefix_exps, skip_step)

                elif ParserUtil.get_token_value(self.look_ahead(skip_step)) in [kw_set_assign]:
                    return self.parse_set_assign_stat(prefix_exps, skip_step)
                
                elif ParserUtil.get_token_value(self.look_ahead(skip_step)) in [kw_do]:
                    return self.parse_class_method_call_stat(prefix_exps, skip_step) 

            elif tk_value == kw_func_ty_define:
                return self.parse_func_def_with_type_stat()

            elif tk_value == '<$>':
                return self.parse_match_mode_func_def_stat()

            elif tk_value == kw_function:
                return self.parse_func_def_stat()

            elif tk_value == '$$':
                return self.parse_lambda_def_stat()

            elif tk_value == kw_pass:
                return self.parse_pass_stat()
            
            elif tk_value == kw_return:
                return self.parse_return_stat()
            
            elif tk_value == kw_del:
                return self.parse_del_stat()

            elif tk_value == kw_type:
                return self.exp_type_stat()

            elif tk_value == kw_assert:
                return self.parse_assert_stat()

            elif tk_value == kw_try:
                return self.parse_try_stat()

            elif tk_value == kw_raise:
                return self.parse_raise_stat()

            elif tk_value == kw_cmd:
                return self.parse_cmd_stat()

            elif tk_value == kw_class_def:
                return self.parse_class_def()

            elif tk_value == kw_call:
                return self.parse_call_stat()

            elif tk_value == kw_stackinit:
                return self.parse_stack_init_stat()

            elif tk_value == kw_push:
                return self.parse_stack_push_stat()

            elif tk_value == kw_pop:
                return self.parse_stack_pop_stat()

            elif tk_value == kw_match:
                return self.parse_match_stat()

            elif tk_value == '@@@':
                return self.parse_extend_stat()

            elif tk_value == '&&':
                return self.parse_for_each_stat()

            elif tk_value == kw_model:
                return self.parse_model_new_stat()

            elif tk_value == kw_turtle_beg:
                return self.parse_turtle_stat()

        elif kind == TokenType.IDENTIFIER:
            if ParserUtil.get_token_value(self.look_ahead(1)) in [kw_from]:
                return self.parse_for_stat()
            
            elif ParserUtil.get_token_value(self.look_ahead(1)) in [kw_call_begin]:
                return self.parse_func_call_stat()

            elif ParserUtil.get_token_value(self.look_ahead(1)) in [kw_do]:
                return self.parse_class_method_call_stat()

        elif kind == TokenType.EOF:
            return
        
        else:
            raise Exception("Unknown grammer in %s" % (str(self.get_line())))
            
    def parse_stats(self):
        stats = []
        while True:
            stat = self.parse()
            if stat is not None:
                stats.append(stat)
            else:
                break
        return stats

    def parse_print_stat(self):
        self.skip(1) # skip the kw_print
        args = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_args)
        self.get_next_token_of([kw_endprint], step = 0)
        return can_ast.PrintStat(args)

    # Parser for muti-assign
    def parse_assign_block(self):
        # Nothing in assignment block
        if ParserUtil.get_type(self.current()) == TokenType.SEP_RCURLY:
            self.skip(1)
            return can_ast.AssignStat(can_ast.AST, can_ast.AST)
        var_list : list = []
        exp_list : list= []
        while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
            var_list.append(self.parse_var_list()[0])
            self.get_next_token_of([kw_is, kw_is_2, kw_is_3], 0)
            exp_list.append(ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp_list)[0])
        
        # Skip the SEP_RCURLY
        self.skip(1)
        return can_ast.AssignBlockStat(var_list, exp_list)

    def parse_assign_stat(self):
        self.skip(1)
        if ParserUtil.get_token_value(self.current()) != kw_do:
            var_list = self.parse_var_list()
            self.get_next_token_of([kw_is, kw_is_2, kw_is_3], 0)
            exp_list = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp_list)
            last_line = self.get_line()
            return can_ast.AssignStat(var_list, exp_list)
        else:
            # Skip the kw_do
            self.skip(1)
            self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)
            return self.parse_assign_block()
            # The SEP_RCURLY will be checked in self.parse_assign_block()

    def parse_var_list(self):
        exp = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_prefixexp)
        var_list : list = [self.check_var(exp)]
    
        while ParserUtil.get_type(self.current()) == TokenType.SEP_COMMA:
            self.skip(1)
            exp = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_prefixexp)
            var_list.append(self.check_var(exp))

        return var_list

    def check_var(self, exp : can_ast.AST):
        if isinstance(exp, (can_ast.IdExp, can_ast.ObjectAccessExp, 
                            can_ast.ListAccessExp, can_ast.MappingExp,
                            can_ast.ClassSelfExp)):
           return exp
        else:
            raise Exception('unreachable!')

    def parse_exit_stat(self):
        tk = self.look_ahead(0)
        self.skip(1)
        return can_ast.ExitStat()

    def parse_if_stat(self):
        # Skip the keyword if
        self.skip(1)
        if_blocks : list = []
        elif_exps : list = []
        elif_blocks : list = []
        else_blocks : list = []

        if_exps = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp)
        self.get_next_token_of([kw_then], 0)
        self.get_next_token_of(kw_do, 0)
        self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

        while (ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY):
            block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
            if_blocks.append(block_parser.parse())
            self.skip(block_parser.pos)
            del block_parser # free the memory
        self.skip(1) # Skip the SEP_RCURLY '}'

        while ParserUtil.get_token_value(self.current()) in [kw_elif]:
            self.skip(1) # skip and try to get the next token
            elif_exps.append(ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp))
            self.get_next_token_of([kw_then], 0)
            self.get_next_token_of(kw_do, 0)
            self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)
            
            elif_block : list = []
            
            while (ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY):
                block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
                elif_block.append(block_parser.parse())
                self.skip(block_parser.pos)
                del block_parser # free the memory
            elif_blocks.append(elif_block)

            self.skip(1) # Skip the SEP_RCURLY '}'

        if ParserUtil.get_token_value(self.current()) == kw_else_or_not:
            self.skip(1) # Skip and try yo get the next token
            self.get_next_token_of([kw_then], 0)
            self.get_next_token_of(kw_do, 0)
            self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)
            while (ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY):
                block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
                else_blocks.append(block_parser.parse())
                self.skip(block_parser.pos)
                del block_parser # free the memory
            self.skip(1) # Skip the SEP_RCURLY '}'

        return can_ast.IfStat(if_exps, if_blocks, elif_exps, elif_blocks, else_blocks)


    def parse_import_stat(self):
        self.skip(1) # Skip the kw_import
        idlist = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_idlist)
        return can_ast.ImportStat(idlist)

    def parse_global_stat(self):
        self.skip(1) # Skip the kw_global
        idlist = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_idlist)
        return can_ast.GlobalStat(idlist)

    def parse_break_stat(self):
        self.skip(1) # Skip the kw_break
        return can_ast.BreakStat()

    def parse_continue_stat(self):
        self.skip(1) # Skip the kw_continue
        return can_ast.ContinueStat()

    def parse_while_stat(self):
        self.skip(1) # Skip the kw_while_do
        blocks : list = []
        while (ParserUtil.get_token_value(self.current()) != kw_while):
            block_parser =  StatParser(self.tokens[self.pos : ], self.ExpParser)
            blocks.append(block_parser.parse())
            self.skip(block_parser.pos)
            del block_parser # free the memory

        self.skip(1) # Skip the kw_while
       
        cond_exps = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp)
        self.get_next_token_of([kw_whi_end], 0)

        return can_ast.WhileStat(can_ast.UnopExp('not', cond_exps), blocks)

    def parse_for_stat(self, prefix_exp : ExpParser = None, skip_prefix_exp : int = 0):
        blocks : list = []

        if prefix_exp == None:
            id = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp)

        else:
            id = prefix_exp[0]
            self.skip(skip_prefix_exp)
        
        self.get_next_token_of([kw_from], 0)

        from_exp = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp)
        self.get_next_token_of([kw_to], 0)

        to_exp = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp)

        while (ParserUtil.get_token_value(self.current()) not in [kw_endfor]):
            block_parse = StatParser(self.tokens[self.pos : ], self.ExpParser)
            blocks.append(block_parse.parse())
            self.skip(block_parse.pos)
            del block_parse # free the memory

        self.skip(1)

        return can_ast.ForStat(id, from_exp, to_exp, blocks)

    def parse_func_def_with_type_stat(self):
        self.get_next_token_of(kw_func_ty_define, 0)

        args_type : list = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_parlist)
        args_type = [] if args_type == None else args_type

        self.get_next_token_of(kw_do, 0)
        
        rets_type = None
        if (ParserUtil.get_token_value(self.current())) != kw_func_ty_end:
            rets_type = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_idlist)

        rets_type = [] if rets_type == None else rets_type

        self.get_next_token_of(kw_func_ty_end, 0)

        return self.parse_func_def_stat(decl_args_type=args_type, decl_ret_type=rets_type)

    def parse_match_mode_func_def_stat(self):
        args_list : list = []
        block_list : list = []
        while (ParserUtil.get_token_value(self.current()) == '<$>'):
            self.skip(1)

            name = ParserUtil.get_token_value(self.get_next_token_of_kind(TokenType.IDENTIFIER, 0))            
            args : list = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp_list)
            args = [] if args == None else args

            args_list.append(args)

            self.get_next_token_of("即係", 0)
            self.get_next_token_of([kw_do], 0)
            body = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp)

            block_list.append(body)

            self.get_next_token_of([kw_func_end], 0)
        
        return can_ast.MatchModeFuncDefStat(can_ast.IdExp(name), args_list, block_list)

    def parse_func_def_stat(self, decl_args_type = [], decl_ret_type = []):
        self.get_next_token_of(kw_function, 0)
        
        name = ParserUtil.get_token_value(self.get_next_token_of_kind(TokenType.IDENTIFIER, 0))            
        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        args : list = exp_parser.parse_parlist()
        args = [] if args == None else args
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of([kw_func_begin, kw_do], 0)

        blocks : list = []
        while (ParserUtil.get_token_value(self.current()) not in [kw_func_end]):
            block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
            blocks.append(block_parser.parse())
            self.skip(block_parser.pos)
            del block_parser

        self.skip(1)
        return can_ast.FunctionDefStat(can_ast.IdExp(name), args, blocks, 
                                    decl_args_type, decl_ret_type)

    def parse_func_call_stat(self, prefix_exps : can_ast.AST = None, skip_step : int = 0):
        if prefix_exps == None:
            func_name = can_ast.IdExp(ParserUtil.get_token_value(self.current()))
            self.skip(1)
        else:
            func_name = prefix_exps[0]
            self.skip(skip_step)

        self.get_next_token_of([kw_call_begin], 0)
        self.get_next_token_of(kw_do, 0)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        args = exp_parser.parse_args()
        self.skip(exp_parser.pos)
        del exp_parser

        if ParserUtil.get_token_value(self.current()) == kw_get_value:
            self.skip(1)
            var_list = self.parse_var_list()
            return can_ast.AssignStat(var_list,
                    [can_ast.FuncCallExp(func_name, args)])
        else:
            return can_ast.FuncCallStat(func_name, args)

    def parse_class_method_call_stat(self, prefix_exps : can_ast.AST = None, skip_step : int = 0):
        if prefix_exps == None:
            name_exp = can_ast.IdExp(ParserUtil.get_token_value(self.current()))
            self.skip(1)
        else:
            self.skip(skip_step)
            name_exp = prefix_exps[0]

        self.get_next_token_of(kw_do, 0)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        method : can_ast.AST = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        args : list = exp_parser.parse_args()
        self.skip(exp_parser.pos)
        del exp_parser # free thr memory
    
        return can_ast.MethodCallStat(name_exp, method, args)
    
    def parse_list_assign_stat(self, prefix_exp : can_ast.AST, skip_step : int):
        self.skip(skip_step)
        self.get_next_token_of([kw_lst_assign], 0)
        self.get_next_token_of(kw_do, 0)
        varlist = self.parse_var_list()

        return can_ast.AssignStat(varlist, 
                [can_ast.ListExp(prefix_exp)])

    def parse_set_assign_stat(self, prefix_exp : can_ast.AST, skip_step : int):
        self.skip(skip_step)
        self.get_next_token_of([kw_set_assign], 0)
        self.get_next_token_of(kw_do, 0)
        varlist = self.parse_var_list()

        return can_ast.AssignStat(varlist, 
                [can_ast.MapExp(prefix_exp)])


    def parse_pass_stat(self):
        self.skip(1)
        return can_ast.PassStat()

    def parse_assert_stat(self):
        self.skip(1)
        exp = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp)
        return can_ast.AssertStat(exp)

    def parse_return_stat(self):
        self.skip(1)
        exps = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp_list)
        return can_ast.ReturnStat(exps)

    def parse_del_stat(self):
        self.skip(1)
        exps = ParserUtil.parse_exp(self, self.getExpParser(), by=self.ExpParser.parse_exp_list)
        return can_ast.DelStat(exps)

    def parse_try_stat(self):
        self.skip(1)
        self.get_next_token_of(kw_do, 0)
        self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

        try_blocks : list = []
        except_exps : list = []
        except_blocks : list = []
        finally_blocks : list = []

        while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
            block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
            try_blocks.append(block_parser.parse())
            self.skip(block_parser.pos)
            del block_parser

        self.skip(1)
        self.get_next_token_of([kw_except], 0)
        
        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        except_exps.append(exp_parser.parse_exp())
        self.skip(exp_parser.pos)
        del exp_parser

        self.get_next_token_of([kw_then], 0)
        self.get_next_token_of([kw_do], 0)
        self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

        # a temp list to save the block
        except_block = []
        while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
            block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
            except_block.append(block_parser.parse())
            self.skip(block_parser.pos)
            del block_parser
        
        self.skip(1)
        except_blocks.append(except_block)

        while ParserUtil.get_token_value(self.current()) in [kw_except]:
            self.get_next_token_of([kw_then], 0)

            exp_parser = self.ExpParser(self.tokens[self.pos : ])
            except_exps.append(exp_parser.parse_exp())
            self.skip(exp_parser.pos)
            del exp_parser

            self.get_next_token_of(kw_do, 0)
            self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

            # clear the list
            except_block = []
            while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
                block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
                except_block.append(block_parser.parse())
                self.skip(block_parser.pos)
                del block_parser
            
            except_blocks.append(except_block)

        if ParserUtil.get_token_value(self.current()) in [kw_finally]:
            self.skip(1)
            self.get_next_token_of(kw_do, 0)
            self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

            while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
                block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
                finally_blocks.append(block_parser.parse())
                self.skip(block_parser.pos)
                del block_parser

            self.skip(1)

        return can_ast.TryStat(try_blocks, except_exps, except_blocks, finally_blocks)

    def parse_raise_stat(self):
        self.skip(1)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        name_exp = exp_parser.parse_exp()
        self.skip(exp_parser.pos) # free the memory
        del exp_parser

        self.get_next_token_of([kw_raise_end], 0)
        return can_ast.RaiseStat(name_exp)

    def exp_type_stat(self):
        self.skip(1)
        name_exp = ParserUtil.parse_exp(self, self.getExpParser(), self.ExpParser.parse_exp)

        return can_ast.TypeStat(name_exp)

    def parse_cmd_stat(self):
        self.skip(1)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        args = exp_parser.parse_args()
        self.skip(exp_parser.pos) # free the memory
        del exp_parser

        return can_ast.CmdStat(args)

    def parse_class_def(self):
        self.skip(1)
        
        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        class_name : can_ast.AST = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of([kw_extend], 0)
        
        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        extend_name : list = exp_parser.parse_exp_list()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        class_blocks = []
        
        while ParserUtil.get_token_value(self.current()) not in [kw_endclass]:
            class_block_parser = ClassBlockStatParser(self.tokens[self.pos : ])
            class_blocks.append(class_block_parser.parse())
            self.skip(class_block_parser.pos)

        self.skip(1)

        return can_ast.ClassDefStat(class_name, extend_name, class_blocks)

    def parse_call_stat(self):
        self.skip(1)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        exps = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        return can_ast.CallStat(exps)

    def parse_stack_init_stat(self):
        self.skip(1)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        exps = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        return can_ast.AssignStat([exps], [
            can_ast.FuncCallExp(can_ast.IdExp('stack'), [])
        ])

    def parse_stack_push_stat(self):
        self.skip(1) # skip the kw_push

        self.get_next_token_of(kw_do, 0)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        exps = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        args = exp_parser.parse_args()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        return can_ast.MethodCallStat(exps, can_ast.IdExp('push'), 
                    args)

    def parse_stack_pop_stat(self):
        self.skip(1) # skip the kw_pop

        self.get_next_token_of(kw_do, 0)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        exps = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        return can_ast.MethodCallStat(exps, can_ast.IdExp('pop'), 
                    [])

    def parse_lambda_def_stat(self):
        exp_parse = self.ExpParser(self.tokens[self.pos : ])
        lambda_exp = [exp_parse.parse_functiondef_expr()]
        self.skip(exp_parse.pos)
        del exp_parse # free the memory

        self.get_next_token_of(kw_get_value, 0)
        exp_parse = self.ExpParser(self.tokens[self.pos : ])
        id_exp = exp_parse.parse_idlist()
        self.skip(exp_parse.pos)
        del exp_parse # free the memory

        return can_ast.AssignStat(id_exp, lambda_exp)

    def parse_match_stat(self):
        self.skip(1)
        match_val : list = []
        match_block : list = []
        default_match_block : list = []
        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        match_id = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of(kw_do, 0)
        self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

        while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
            while ParserUtil.get_token_value(self.current()) in [kw_case]:
                self.skip(1)
                exp_parser = self.ExpParser(self.tokens[self.pos : ])
                match_val.append(exp_parser.parse_exp())
                self.skip(exp_parser.pos)
                del exp_parser # free the memory

                self.get_next_token_of(kw_do, 0)
                self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

                block : list = []

                while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
                    stat_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
                    block.append(stat_parser.parse())
                    self.skip(stat_parser.pos)
                    del stat_parser # free the memory

                self.skip(1)
                match_block.append(block)
            
            if ParserUtil.get_token_value(self.current()) == kw_else_or_not:
                self.skip(1)
                self.get_next_token_of([kw_then], 0)
                self.get_next_token_of(kw_do, 0)
                self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

                while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
                    stat_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
                    default_match_block.append(stat_parser.parse())
                    self.skip(stat_parser.pos)
                    del stat_parser # free the memory

                self.skip(1)
        
        self.skip(1)

        return can_ast.MatchStat(match_id, match_val, match_block, default_match_block)

    def parse_for_each_stat(self):
        self.skip(1)

        id_list : list = []
        exp_list : list = []
        blocks : list = []

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        id_list = exp_parser.parse_idlist()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of([kw_in], 0)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        exp_list = exp_parser.parse_exp_list()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of(kw_do, 0)
        self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

        while (ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY):
            stat_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
            blocks.append(stat_parser.parse())
            self.skip(stat_parser.pos)
            del stat_parser # free the memory
        
        self.skip(1)

        return can_ast.ForEachStat(id_list, exp_list, blocks)

    def parse_extend_stat(self):
        self.skip(1)
        tk = self.get_next_token_of_kind(TokenType.EXTEND_EXPR, 0)
        return can_ast.ExtendStat(ParserUtil.get_token_value(tk)[1 : -1])

    def parse_model_new_stat(self):
        self.skip(1)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        model_name = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of([kw_mod_new], 0)
        self.get_next_token_of(kw_do, 0)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        dataset = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        return can_ast.ModelNewStat(model_name, dataset)

    def parse_turtle_stat(self):
        self.skip(1)

        instruction_ident : list = ["首先", "跟住", "最尾"]
        self.get_next_token_of(kw_do, 0)
        self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

        exp_blocks : list = []

        while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
            if ParserUtil.get_token_value(self.current()) in instruction_ident and \
                ParserUtil.get_type(self.current()) == TokenType.IDENTIFIER:
                self.skip(1)
            else:
                exp_parser = self.ExpParser(self.tokens[self.pos : ])
                exp_blocks.append(exp_parser.parse_exp())
                self.skip(exp_parser.pos)
                del exp_parser # free the memory

        self.skip(1)

        return can_ast.TurtleStat(exp_blocks)


class ClassBlockStatParser(StatParser):
    def __init__(self, token_list: list, ExpParser = ClassBlockExpParser) -> None:
        super().__init__(token_list, ExpParser)

    def parse_method_block(self):
        
        self.skip(1) # Skip the kw_method

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        name_exp = exp_parser.parse_exp()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        args : list = exp_parser.parse_parlist()
        args = [] if args == None else args
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of([kw_func_begin, kw_do], 0)
        
        blocks : list = []
        # '{' ... '}'
        if ParserUtil.get_type(self.current()) == TokenType.SEP_LCURLY:
            self.skip(1)
            while ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY:
                block_parser = ClassBlockStatParser(self.tokens[self.pos : ], self.ExpParser)
                blocks.append(block_parser.parse())
                self.skip(block_parser.pos)
                del block_parser
        
        # '=> ... '%%'
        else:
            while (ParserUtil.get_token_value(self.current()) not in [kw_func_end]):
                block_parser = ClassBlockStatParser(self.tokens[self.pos : ], self.ExpParser)
                blocks.append(block_parser.parse())
                self.skip(block_parser.pos)
                del block_parser        

        self.skip(1)
        
        return can_ast.MethodDefStat(name_exp, args, blocks)

    def parse_class_init_stat(self):
        self.skip(1)

        exp_parser = self.ExpParser(self.tokens[self.pos : ])
        args = exp_parser.parse_parlist()
        self.skip(exp_parser.pos)
        del exp_parser # free the memory

        self.get_next_token_of(kw_do, 0)
        self.get_next_token_of_kind(TokenType.SEP_LCURLY, 0)

        blocks : list = []
        while (ParserUtil.get_type(self.current()) != TokenType.SEP_RCURLY):
            block_parser = StatParser(self.tokens[self.pos : ], self.ExpParser)
            blocks.append(block_parser.parse())
            self.skip(block_parser.pos)
            del block_parser # free the memory

        self.skip(1)

        return can_ast.MethodDefStat(can_ast.IdExp('__init__'), args, blocks)
        
    def parse_class_assign_stat(self):
        return self.parse_assign_stat()

    def parse(self):
        tk = self.current()
        kind = ParserUtil.get_type(tk)
        tk_value = ParserUtil.get_token_value(tk)
        if tk_value == kw_method:
            return self.parse_method_block()
        elif tk_value == kw_class_assign:
            return self.parse_class_assign_stat()
        elif tk_value == kw_class_init:
            return self.parse_class_init_stat()
        else:
            return super().parse()