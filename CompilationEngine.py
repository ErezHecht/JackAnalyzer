from JackTokenizer import Tokenizer
from TokenTypes import KEYWORD, INT_CONST, STRING_CONST, IDENTIFIER
from TokenTypes import IDENTIFIER_REGEX as NAME_REG
import re
from SymbolTable import SymbolTable
from VMWriter import VMWriter

CONSTANT = "constant"


class CompilationEngine:
    _OPEN_PARENTHESIS = "\("
    _CLOSE_PARENTHESIS = "\)"
    _OPEN_BRACKET = "\["
    _CLOSE_BRACKET = "\]"
    _DOT = "\."
    _OPS = "\+|-|\*|\/|&|\||<|>|="

    def __init__(self, in_address):
        self.tokenizer = Tokenizer(in_address)
        self.symbol_table = SymbolTable()
        self.vm_writer = VMWriter(in_address.replace(".jack", ".vm"))
        self.curr_token = self.tokenizer.get_current_token()
        self.out_address = in_address.replace(".jack", ".xml")
        self.output = ""
        self.indent = 0
        self.label_count = -1
        self.class_name = ""
        self.compile_class()

    def write_file(self):
        # with open(self.out_address, 'w') as f:
        #     f.write(self.output)
        self.vm_writer.write_file()

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
            self.class_name = self.eat(NAME_REG)
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
        kind = self.eat(var_type_reg)
        # type
        var_type = self.__compile_type(False)
        # Compile varName combo until no more ","
        self.__var_declare(var_type, kind)
        self.eat(";")

    def __var_declare(self, var_type, kind):
        name = self.eat(NAME_REG)
        self.symbol_table.define(name, var_type, kind)
        if self.peek_token(","):
            self.eat(",")
            self.__var_declare(var_type, kind)

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
        return self.eat(type_reg)

    def compile_subroutine(self):
        """
        Compiles a complete method, function or constructor.
        :return:
        """
        sub_regex = "(constructor|function|method)"
        self.symbol_table.start_subroutine()

        def subroutine_dec():
            kind = self.eat(sub_regex)
            sub_type = self.__compile_type(True)
            # subroutine name
            name = self.__compile_name()
            self.eat(CompilationEngine._OPEN_PARENTHESIS)
            para_num = self.compile_parameter_list(kind)
            self.vm_writer.write_function("{}.{}".format(self.class_name,
                                                         name), para_num)
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            subroutine_body(sub_type)
            # self.wrap("subroutineBody", subroutine_body)

        def subroutine_body(sub_type):
            self.eat("{")
            if self.peek_token("var"):
                self.compile_var_dec()
            self.compile_statements()
            # if sub_type == "void":
            #     self.vm_writer.write_push("constant", 0)
            self.eat("}")

        if self.peek_token(sub_regex):
            # self.wrap("subroutineDec", subroutine_dec)
            subroutine_dec()
            # Handle next subroutine if there is one
            self.compile_subroutine()

    def __handle_constructor(self):
        # Allocate memory for the new object
        var_num = self.symbol_table.var_count(
            "static") + self.symbol_table.var_count(
            "field")
        self.vm_writer.write_push(CONSTANT, var_num)
        self.vm_writer.write_call("Memory.alloc", 1)
        # Set the new memory spot to this
        self.vm_writer.write_pop("pointer", 0)

    def __compile_name(self):
        if self.peek_type() == IDENTIFIER:
            return self.eat(NAME_REG)
        else:
            print("ERROR: Identifier Expected")
            exit(-1)

    def compile_parameter_list(self, kind):
        """
        Compiles a possibly empty parameter list, not including the
        enclosing ()
        :return:
        """
        # self.wrap("parameterList", self.__params)
        if kind == "method":
            self.symbol_table.define("this", self.class_name, "argument")
        elif kind == "constructor":
            self.__handle_constructor()
        type_reg = r"int|char|boolean|[A-Za-z_]\w*"
        para_num = 0
        if self.peek_token(type_reg):
            para_num += self.__params()
        return para_num

    def __params(self):
        var_type = self.__compile_type(False)
        name = self.eat(NAME_REG)
        self.symbol_table.define(name, var_type, "argument")
        if self.peek_token(","):
            self.eat(",")
            return 1 + self.__params()
        else:
            return 1

    def compile_var_dec(self):
        """
        Compiles a var declaration.
        :return:
        """
        # self.wrap("varDec", self.__comp_var_dec)
        kind = self.eat("var")
        var_type = self.__compile_type(False)
        self.__var_declare(var_type, kind)
        self.eat(";")
        if self.peek_token("var"):
            self.compile_var_dec()

    def compile_statements(self):
        """
        Compiles a sequence of statements, not including the enclosing {}
        :return:
        """
        statement_reg = "let|if|while|do|return"
        if self.peek_token(statement_reg):
            if self.peek_token("let"):
                self.compile_let()
            elif self.peek_token("if"):
                self.compile_if()
            elif self.peek_token("while"):
                self.compile_while()
            elif self.peek_token("do"):
                self.compile_do()
            elif self.peek_token("return"):
                self.compile_return()
            self.compile_statements()

    def compile_do(self):
        """
        Compiles a do statement
        :return:
        """

        def do():
            self.eat("do")
            self.__subroutine_call()
            # Since we don't use the return value, we pop it to temp
            self.vm_writer.write_pop("temp", 0)
            self.eat(";")

        self.wrap("doStatement", do)

    def compile_let(self):
        """
        Compiles a let statement
        :return:
        """
        # self.wrap("letStatement", self.__comp_let)
        self.__comp_let()

    def __comp_let(self):
        self.eat("let")
        name = self.__compile_name()
        is_array = False
        self.__write_push(name)
        # Determine [expression]
        if self.peek_token(CompilationEngine._OPEN_BRACKET):
            is_array = True
            self.__handle_array()
        self.eat("=")
        self.compile_expression()
        # Pop the value to the spot in the memory
        if is_array:
            self.vm_writer.write_pop("that", 0)
        else:
            self.__write_pop(name)
        self.eat(";")

    def __handle_array(self):
        self.eat(CompilationEngine._OPEN_BRACKET)
        self.compile_expression()
        self.vm_writer.write_arithmetic("add")
        # Store the new address in that segment
        self.vm_writer.write_pop("pointer", 1)
        self.eat(CompilationEngine._CLOSE_BRACKET)

    def compile_while(self):
        """
        Compiles a while statement.
        :return:
        """

        def comp_while():
            self.eat("while")
            loop_label = self.__get_label()
            exit_label = self.__get_label()
            self.vm_writer.write_label(loop_label)
            self.eat(CompilationEngine._OPEN_PARENTHESIS)
            # Compute ~condition
            self.compile_expression()
            self.vm_writer.write_arithmetic("neg")
            # if ~condition exit loop
            self.vm_writer.write_if(exit_label)
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            self.eat("{")
            self.compile_statements()
            self.vm_writer.write_goto(loop_label)
            self.vm_writer.write_label(exit_label)
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
            else:
                # Void function - push 0
                self.vm_writer.write_push(CONSTANT, 0)
            self.vm_writer.write_return()
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
            self.vm_writer.write_arithmetic("neg")
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            self.eat("{")
            l_one = self.__get_label()
            self.vm_writer.write_if(l_one)
            self.compile_statements()
            l_two = self.__get_label()
            self.vm_writer.write_goto(l_two)
            self.eat("}")
            # Handle else:
            self.vm_writer.write_label(l_one)
            if self.peek_token("else"):
                self.eat("else")
                self.eat("{")
                self.compile_statements()
                self.eat("}")
            self.vm_writer.write_label(l_two)

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
                operation = self.eat(CompilationEngine._OPS)
                self.compile_term()
                self.vm_writer.write_arithmetic(operation)

        self.wrap("expression", comp_expression)

    def compile_term(self):
        """
        Compiles a term.
        :return:
        """

        def term():
            curr_type = self.peek_type()
            val = self.curr_token.get_token()
            # Handle integer constant
            if curr_type == INT_CONST:
                self.vm_writer.write_push(CONSTANT, int(val))
                self.__advance_token()
            # Handle String constant
            elif curr_type == STRING_CONST:
                self.__handle_string_constant(val)
            # Handle Keyword constant
            elif curr_type == KEYWORD:
                self.__handle_keyword_constant(val)
            # Case: token is a varName or a subroutineName
            elif curr_type == IDENTIFIER:
                self.__handle_identifier()
            # Case: ( expression )
            elif self.peek_token(CompilationEngine._OPEN_PARENTHESIS):
                self.eat(CompilationEngine._OPEN_PARENTHESIS)
                self.compile_expression()
                self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            # Case: unaryOp term
            elif self.peek_token("-|~"):
                command = self.eat("-|~")
                self.compile_term()
                if command == "-":
                    self.vm_writer.write_arithmetic("neg")
                else:
                    self.vm_writer.write_arithmetic(command)
            else:
                print("Error: Incorrect Term")
                exit(-1)

        term()
        # self.wrap("term", term)

    def __handle_identifier(self):
        """
        Handles the case of an identifier given as a term
        """
        # Case: varName [ expression ]
        if self.peek_next(CompilationEngine._OPEN_BRACKET):
            self.__var_name_array()
        # Case: subroutineCall:
        elif self.peek_next(CompilationEngine._OPEN_PARENTHESIS) or \
                self.peek_next(CompilationEngine._DOT):
            self.__subroutine_call()
        else:
            name = self.eat(NAME_REG)
            self.__write_push(name)

    def __handle_string_constant(self, string):
        """
        Handles the case of a string constant in a term
        :param string: the constant
        """
        self.vm_writer.write_push(CONSTANT, len(string))
        self.vm_writer.write_call("String.new", 1)
        for char in string:
            self.vm_writer.write_push(CONSTANT, ord(char))
            self.vm_writer.write_call("String.appendChar", 2)

    def __handle_keyword_constant(self, word):
        """
        Handles the case of a keyword constant given in a term.
        If the word is not valid the program prints a relevant message and
        exits.
        :param word: The keyword
        """
        if word == "this":
            self.vm_writer.write_push("pointer", 0)
        elif word == "false" or word == "null":
            self.vm_writer.write_push(CONSTANT, 0)
        elif word == "true":
            self.vm_writer.write_push(CONSTANT, 1)
            self.vm_writer.write_arithmetic("neg")
        else:
            print("Error: Unsupported Keyword constant: {}. Use this,null,"
                  "true, false only.")
            exit(-1)

    def __var_name_array(self):
        """
        Handles the case of varName[expression]
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
            if self.peek_next(CompilationEngine._OPEN_PARENTHESIS):
                self.__subroutine_name("")
            elif self.peek_next(CompilationEngine._DOT):
                self.__object_subroutine_call()
            else:
                print("Error: ( or . expected")
                exit(-1)

    def __object_subroutine_call(self):
        name = self.eat(NAME_REG)
        # Push the object reference to the stack
        if self.symbol_table.kind_of(name):
            self.__write_push(name)
        self.eat(CompilationEngine._DOT)
        self.__subroutine_name(name + ".")

    def __subroutine_name(self, obj_name):
        """
        Handles the case of subroutineName(expressionList)
        :return:
        """
        if self.curr_token.get_type() == IDENTIFIER:
            name = self.eat(NAME_REG)
            self.eat(CompilationEngine._OPEN_PARENTHESIS)
            nargs = self.compile_expression_list()
            self.eat(CompilationEngine._CLOSE_PARENTHESIS)
            self.vm_writer.write_call(obj_name + name, nargs)

    def compile_expression_list(self):
        """
        Compiles a possibly empty list of comma separated expressions
        :return:
        """

        def exp_list():
            count = 0
            if self.is_term():
                self.compile_expression()
                count += 1
                while self.peek_token(","):
                    self.eat(",")
                    self.compile_expression()
                    count += 1
            return count

        return exp_list()
        # self.wrap("expressionList", exp_list)

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
        ctoken = self.curr_token.get_token()
        if re.match(token, self.curr_token.get_token()):
            # self.write(self.curr_token.get_xml_wrap())
            self.__advance_token()
            return ctoken
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

    def __get_label(self):
        self.label_count += 1
        return "L{}".format(str(self.label_count))

    def __write_pop(self, name):
        self.vm_writer.write_pop(self.symbol_table.kind_of(name),
                                 self.symbol_table.index_of(name))

    def __write_push(self, name):
        self.vm_writer.write_push(self.symbol_table.kind_of(name),
                                  self.symbol_table.index_of(name))
