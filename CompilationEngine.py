from JackTokenizer import Tokenizer
from TokenTypes import KEYWORD, INT_CONST, STRING_CONST, IDENTIFIER
from TokenTypes import IDENTIFIER_REGEX as NAME_REG
import re
from SymbolTable import SymbolTable


class CompilationEngine:
    _OPEN_PARENTHESIS = "\("
    _CLOSE_PARENTHESIS = "\)"
    _OPEN_BRACKET = "\["
    _CLOSE_BRACKET = "\]"
    _DOT = "\."
    _OPS = "\+|-|\*|\/|&|\||<|>|="

    def __init__(self, in_address):
        self.tokenizer = Tokenizer(in_address)
        self.curr_token = self.tokenizer.get_current_token()
        self.out_address = in_address.replace(".jack", ".xml")
        self.output = ""
        self.indent = 0
        self.compile_class()

    def write_file(self):
        with open(self.out_address, 'w') as f:
            f.write(self.output)

    def write(self, to_write):
        """
        Writes to the output, with indentation.
        :param to_write: The string to write
        """
        self.output += (self.indent * " ") + to_write + "\n"

    def compile_class(self):
        """
        Compiles a complete class.
        """

        def comp_class():
            self.eat("class")
            #self.class_name = self.curr_token.get_token()
            self.eat(NAME_REG)
            self.eat("{")
            self.compile_class_var_dec()
            self.compile_subroutine()
            self.eat("}")

        self.wrap("class", comp_class)

    def compile_class_var_dec(self):
        """
        Compiles a static or field declaration.
        :return:
        """
        var_type_reg = "static|field"
        if self.peek_token(var_type_reg):
            self.wrap("classVarDec", self.__class_var_dec)
            self.compile_class_var_dec()

    def __class_var_dec(self):
        """
        Compiles a single class var declaration.
        """
        var_type_reg = "static|field"
        # (static|field)
        var_type = self.curr_token.get_token()
        self.eat(var_type_reg)
        # type
        self.__compile_type(False)
        # Compile varName combo until no more ","
        self.__single_var()
        self.eat(";")

    def __single_var(self):
        """
        Compiles a single set of variables separated by commas.
        """
        # varName
        self.eat(NAME_REG)
        if self.peek_token(","):
            self.eat(",")
            self.__single_var()

    def __compile_type(self, for_function):
        """
        Compiles a type for a function or variable, determined by
        a received boolean value.
        :param for_function: True if is type of function, false otherwise.
        :return:
        """
        type_reg = r"int|char|boolean|[A-Za-z_]\w*"
        if for_function:
            type_reg += "|void"
        self.eat(type_reg)

    def compile_subroutine(self):
        """
        Compiles a complete method, function or constructor.
        :return:
        """
        sub_regex = "(constructor|function|method)"

        def subroutine_dec():
            self.eat(sub_regex)
            self.__compile_type(True)
            # subroutine name
            self.__compile_name()
            self.eat(CompilationEngine._OPEN_PARENTHESIS)
            self.compile_parameter_list()
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            self.wrap("subroutineBody", subroutine_body)

        def subroutine_body():
            self.eat("{")
            if self.peek_token("var"):
                self.compile_var_dec()
            self.compile_statements()
            self.eat("}")

        if self.peek_token(sub_regex):
            self.wrap("subroutineDec", subroutine_dec)
            # Handle next subroutine if there is one
            self.compile_subroutine()

    def __compile_name(self):

        if self.peek_type() == IDENTIFIER:
            self.eat(NAME_REG)
        else:
            print("ERROR: Identifier Expected")
            exit(-1)

    def compile_parameter_list(self):
        """
        Compiles a possibly empty parameter list, not including the
        enclosing ()
        :return:
        """
        self.wrap("parameterList", self.__params)

    def __params(self):
        type_reg = r"int|char|boolean|[A-Za-z_]\w*"
        if self.peek_token(type_reg):
            self.__compile_type(False)
            self.eat(NAME_REG)
            if self.peek_token(","):
                self.eat(",")
                self.__params()

    def compile_var_dec(self):
        """
        Compiles a var declaration.
        :return:
        """
        self.wrap("varDec", self.__comp_var_dec)
        if self.peek_token("var"):
            self.compile_var_dec()

    def __comp_var_dec(self):
        self.eat("var")
        self.__compile_type(False)
        self.__single_var()
        self.eat(";")

    def compile_statements(self):
        """
        Compiles a sequence of statements, not including the enclosing {}
        :return:
        """

        def statement():
            """
            Determines the type of statement and compiles it. Calls itself
            afterwards to check for more statements.
            :return:
            """
            # statement_reg = "let|if|while|do|return"
            # if self.peek_token(statement_reg):
            if self.peek_token("let"):
                self.compile_let()
                statement()
            if self.peek_token("if"):
                self.compile_if()
                statement()
            if self.peek_token("while"):
                self.compile_while()
                statement()
            if self.peek_token("do"):
                self.compile_do()
                statement()
            if self.peek_token("return"):
                self.compile_return()
                statement()

        self.wrap("statements", statement)

    def compile_do(self):
        """
        Compiles a do statement
        :return:
        """

        def do():
            self.eat("do")
            self.__subroutine_call()
            self.eat(";")

        self.wrap("doStatement", do)

    def __comp_do(self):
        self.eat("do")
        self.__subroutine_call()
        self.eat(";")

    def compile_let(self):
        """
        Compiles a let statement
        :return:
        """
        self.wrap("letStatement", self.__comp_let)

    def __comp_let(self):
        self.eat("let")
        self.__compile_name()
        # Determine [expression]
        if self.peek_token(CompilationEngine._OPEN_BRACKET):
            self.eat(CompilationEngine._OPEN_BRACKET)
            self.compile_expression()
            self.eat(CompilationEngine._CLOSE_BRACKET)
        self.eat("=")
        self.compile_expression()
        self.eat(";")

    def compile_while(self):
        """
        Compiles a while statement.
        :return:
        """

        def comp_while():
            self.eat("while")
            self.eat(CompilationEngine._OPEN_PARENTHESIS)
            self.compile_expression()
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            self.eat("{")
            self.compile_statements()
            self.eat("}")

        self.wrap("whileStatement", comp_while)

    def compile_return(self):
        """
        Compiles a return statement.
        :return:
        """

        def comp_return():
            self.eat("return")
            # if next is expression:
            if self.is_term():
                self.compile_expression()
            self.eat(";")

        self.wrap("returnStatement", comp_return)

    def compile_if(self):
        """
        Compiles an if statement, possibly with a trailing else clause.
        :return:
        """

        def comp_if():
            self.eat("if")
            self.eat(CompilationEngine._OPEN_PARENTHESIS)
            self.compile_expression()
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            self.eat("{")
            # self.indent += 1
            self.compile_statements()
            self.eat("}")
            # Handle else:
            if self.peek_token("else"):
                self.eat("else")
                self.eat("{")
                self.compile_statements()
                self.eat("}")

        self.wrap("ifStatement", comp_if)

    def compile_expression(self):
        """
        Compiles an expression.
        :return:
        """

        def comp_expression():
            self.compile_term()
            # Case: term op term
            if self.peek_token(CompilationEngine._OPS):
                self.eat(CompilationEngine._OPS)
                self.compile_term()

        self.wrap("expression", comp_expression)

    def compile_term(self):
        """
        Compiles a term.
        :return:
        """

        def term():
            curr_type = self.peek_type()
            is_const = curr_type == STRING_CONST or \
                       curr_type == INT_CONST or \
                       curr_type == KEYWORD
            # Case: term is integerConstant or stringConstant or
            # keywordConstant
            if is_const:
                self.write(self.tokenizer.get_current_token().get_xml_wrap())
                self.__advance_token()
            # Case: token is a varName or a subroutineName
            elif curr_type == IDENTIFIER:
                # self.write(self.tokenizer.get_current_token().get_xml_wrap())
                # self.tokenizer.advance()
                # Case: varName [ expression ]
                if self.peek_next(CompilationEngine._OPEN_BRACKET):
                    self.__var_name_array()
                # Case: subroutineCall:
                elif self.peek_next(
                        CompilationEngine._OPEN_PARENTHESIS) or self.peek_next(
                    CompilationEngine._DOT):
                    self.__subroutine_call()
                else:
                    self.eat(NAME_REG)
            # Case: ( expression )
            elif self.peek_token(CompilationEngine._OPEN_PARENTHESIS):
                self.eat(CompilationEngine._OPEN_PARENTHESIS)
                self.compile_expression()
                self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            # Case: unaryOp term
            elif self.peek_token("-|~"):
                self.eat("-|~")
                self.compile_term()
            else:
                print("Error: Incorrect Term")
                exit(-1)

        self.wrap("term", term)

    def __var_name_array(self):
        """
        Handles the case of varName[expression]
        :return:
        """
        self.eat(NAME_REG)
        self.eat(CompilationEngine._OPEN_BRACKET)
        self.compile_expression()
        self.eat(CompilationEngine._CLOSE_BRACKET)

    def is_term(self):
        curr_type = self.peek_type()
        return curr_type == STRING_CONST or curr_type == INT_CONST or \
               curr_type == KEYWORD or curr_type == IDENTIFIER or \
               self.peek_token(CompilationEngine._OPEN_PARENTHESIS) or \
               self.peek_token(CompilationEngine._OPS)

    def __subroutine_call(self):
        if self.curr_token.get_type() == IDENTIFIER:
            # self.write(self.curr_token.get_xml_wrap())
            # self.__advance_token()
            if self.peek_next(CompilationEngine._OPEN_PARENTHESIS):
                self.__subroutine_name()
            elif self.peek_next(CompilationEngine._DOT):
                self.__object_subroutine_call()
            else:
                print("Error: ( or . expected")
                exit(-1)

    def __object_subroutine_call(self):
        self.eat(NAME_REG)
        self.eat(CompilationEngine._DOT)
        self.__subroutine_name()

    def __subroutine_name(self):
        """
        Handles the case of subroutineName(expressionList)
        :return:
        """
        if self.curr_token.get_type() == IDENTIFIER:
            self.eat(NAME_REG)
            self.eat(CompilationEngine._OPEN_PARENTHESIS)
            self.compile_expression_list()
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)

    def compile_expression_list(self):
        """
        Compiles a possibly empty list of comma separated expressions
        :return:
        """

        def exp_list():
            if self.is_term():
                self.compile_expression()
                while self.peek_token(","):
                    self.eat(",")
                    self.compile_expression()

        self.wrap("expressionList", exp_list)

    def wrap(self, section_name, func):
        """
        Wraps a program structure block with the section_name, and executes
        its function
        :param section_name: The name of the section
        :param func: The function to perform
        :return:
        """
        self.write("<{}>".format(section_name))
        self.indent += 2
        func()
        self.indent -= 2
        self.write("</{}>".format(section_name))

    def eat(self, token):
        """
        Handles advancing and writing terminal tokens.
        Will exit the program if an error occurs.
        :param token: The regex of the token to compare
        :return:
        """
        if re.match(token, self.curr_token.get_token()):
            # self.write(self.curr_token.get_xml_wrap())
            self.__advance_token()
        else:
            # if self.tokenizer.get_current_token() != token:
            print("Error: Expected " + token)
            exit(-1)

    def peek_token(self, compare_next):
        """
        :param compare_next: The regex to compare.
        :return: True if the current token matches the regex, False otherwise.
        """
        if self.curr_token:
            return re.match(compare_next,
                            self.curr_token.get_token())
        return False

    def peek_type(self):
        """
        :return: the type of the current token
        """
        return self.curr_token.get_type()

    def peek_next(self, comp):
        next_token = self.tokenizer.get_next_token()
        # Case: There actually is a next token
        if next_token:
            return re.match(comp, self.tokenizer.get_next_token().get_token())
        return False

    def __advance_token(self):
        self.tokenizer.advance()
        if self.tokenizer.has_more_tokens():
            self.curr_token = self.tokenizer.get_current_token()
