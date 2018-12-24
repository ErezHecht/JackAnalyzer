import re
from TokenTypes import KEYWORD, SYMBOL, INT_CONST, STRING_CONST, IDENTIFIER
from TokenTypes import IDENTIFIER_REGEX

JACK_SUFFIX = ".jack"
T_SUFFIX = "T.xml"


class Tokenizer:
    _KEYWORDS = ["class", "constructor", "function", "method", "field",
                 "static",
                 "var", "int", "char", "boolean", "void", "true", "false",
                 "null", "this", "let", "do", "if", "else", "while", "return"]
    _SYMBOLS = ["{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*",
                "/",
                "&", "|", "<", ">", "=", "~"]
    _INT_REGEX = "\d+"
    _STRING_REG = "\".*\""
    _KEYWORD_REGEX = "class|constructor|function|method|field|static|var" \
                     "|int|char|boolean|void|true|false|null|this|let|do" \
                     "|if|else|while|return"
    _SYMBOL_REGEX = "{|}|\[|\]|\(|\)|\.|,|;|\+|-|\*|\/|&|\||<|>|=|~"

    _COMMENT_BLOCK_REGEX = r"/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/"
    _SINGLE_COMMENT_REGEX = "//.*"

    def __init__(self, address):
        self.tokens = []
        self.tokenIndex = 0
        self.int_reg = re.compile(Tokenizer._INT_REGEX)
        self.str_reg = re.compile(Tokenizer._STRING_REG)
        self.iden_reg = re.compile(IDENTIFIER_REGEX)
        self.parse_file(address)
        # self.file_name = os.path.basename(os.path.splitext(address)[0])
        self.out_address = address.replace(JACK_SUFFIX, T_SUFFIX)

    def has_more_tokens(self):
        """
        :return: True if there are more tokens, false otherwise.
        """
        return self.tokenIndex < len(self.tokens)

    def advance(self):
        """
        Advances the current token.
        """
        if self.has_more_tokens():
            self.tokenIndex += 1

    def token_type(self):
        """
        :return: The type of the current token
        """
        return self.tokens[self.tokenIndex].get_type()

    def __determine_type(self, token):
        """
        :param token: The token to determine its type.
        :return: The typ of the token received.
        """
        if token in Tokenizer._KEYWORDS:
            return KEYWORD
        if token in Tokenizer._SYMBOLS:
            return SYMBOL
        if self.int_reg.match(token):
            return INT_CONST
        if self.iden_reg.match(token):
            return IDENTIFIER
        if self.str_reg.match(token):
            return STRING_CONST

    def keyword(self):
        """
        :return: Returns the token if it is a keyword.
        """
        if self.tokens[self.tokenIndex] in Tokenizer._KEYWORDS:
            return self.tokens[self.tokenIndex]

    def symbol(self):
        """
        :return: Returns the token if it is a symbol.
        """
        if self.token_type() == SYMBOL:
            return self.tokens[self.tokenIndex]

    def identifier(self):
        """
        :return: Returns the token if it is an identifier.
        """

        if self.token_type() == IDENTIFIER:
            return self.tokens[self.tokenIndex]

    def int_val(self):
        """
        :return: Returns the token if it is an integer constant.
        """

        if self.token_type() == INT_CONST:
            return self.tokens[self.tokenIndex]

    def string_val(self):
        """
        :return: Returns the token if it is a string constant
        """
        if self.token_type() == STRING_CONST:
            return self.tokens[self.tokenIndex]

    def parse_file(self, address):
        """
        Parses the commands of a given file, removing spaces and comments, and
        returns a list of the commands parsed and split.

        :param address: the address of the vm file to read
        :return: a list of all commands in the file
        """
        with open(address, "r") as f:
            # Get all lines ignoring whitespace lines or comment lines:
            clean_text = f.read()
            clean_regex = r"({}|{}|\b)".format(Tokenizer._COMMENT_BLOCK_REGEX,
                                               Tokenizer._SINGLE_COMMENT_REGEX)
            clean_text = re.sub(clean_regex, '',
                                clean_text)
            all_regex = "({}|{}|{}|{}|{})".format(Tokenizer._INT_REGEX,
                                                  Tokenizer._STRING_REG,
                                                  IDENTIFIER_REGEX,
                                                  Tokenizer._KEYWORD_REGEX,
                                                  Tokenizer._SYMBOL_REGEX)
            for element in re.finditer(all_regex, clean_text):
                token = element.group(0)
                token_type = self.__determine_type(token)
                self.tokens.append(Token(token_type, token))

    def get_current_token(self):
        """
        :return: Returns the current token.
        """
        return self.tokens[self.tokenIndex]

    def get_next_token(self):
        """
        :return: The next token if there is one.
        """
        if self.tokenIndex + 1 < len(self.tokens):
            return self.tokens[self.tokenIndex + 1]

    def write_file(self):
        """
        Writes the tokens to an xml file.
        """
        output = "<tokens>\n"
        while self.has_more_tokens():
            output += self.tokens[self.tokenIndex].get_xml_wrap()
            self.advance()
        output += "</tokens>"
        self.tokenIndex = 0
        with open(self.out_address, 'w') as f:
            f.write(output)


class Token:
    def __init__(self, token_type, token):
        self.token = token
        self.token_type = token_type
        if self.token_type == STRING_CONST:
            # Get rid of the ""
            self.token = self.token[1:-1]

    def get_token(self):
        return self.token

    def get_type(self):
        return self.token_type

    def get_xml_wrap(self):
        if self.token == "<":
            tok = "&lt;"
        elif self.token == ">":
            tok = "&gt;"
        elif self.token == "&":
            tok = "&amp;"
        elif self.token == "\"":
            tok = "&quot;"
        else:
            tok = self.token
        return "<{}> {} </{}>".format(self.token_type, tok,
                                      self.token_type)
