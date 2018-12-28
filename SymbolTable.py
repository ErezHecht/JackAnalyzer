STATIC = "static"
FIELD = "field"
ARGUMENT = "argument"
VAR = "var"
LOCAL = "local"
THIS = "this"
TYPE_INDEX = 0
KIND_INDEX = 1
NUMBER_INDEX = 2


class SymbolTable:
    def __init__(self):
        """
        Creates a new empty symbol table
        """
        self.class_scope_table = {}
        self.subroutine_scope_table = {}
        self.static_index = 0
        self.field_index = 0
        self.arg_index = 0
        self.var_index = 0

    def start_subroutine(self):
        """
        Starts a new subroutine scope (erases all names of the previous scope)
        """
        self.subroutine_scope_table = {}
        self.arg_index = 0
        self.var_index = 0

    def define(self, name, var_type, kind):
        """
        Defines a new identifier of the given parameters, and assigns it a
        running index.
        :param name: The name of the identifier
        :param var_type: the type of the variable
        :param kind: Static, Field, arg or var
        """
        if name not in self.class_scope_table and name not in \
                self.subroutine_scope_table:
            if kind == STATIC:
                self.class_scope_table.update({name:
                                                   [var_type, STATIC,
                                                    self.static_index]})
                self.static_index += 1
            elif kind == FIELD:
                self.class_scope_table.update({name:
                                                   [var_type, THIS,
                                                    self.field_index]})
                self.field_index += 1
            elif kind == ARGUMENT:
                self.subroutine_scope_table.update({name:
                                                        [var_type, ARGUMENT,
                                                         self.arg_index]})
                self.arg_index += 1
            elif kind == VAR:
                self.subroutine_scope_table.update({name:
                                                        [var_type, LOCAL,
                                                         self.var_index]})
                self.var_index += 1

    def var_count(self, kind):
        """
        Returns the number of variables of the given kind already defined in
        the current scope.
        :param kind: The kind to count.
        :return: the number of variables of the given kind.
        """
        if kind == STATIC or kind == THIS:
            return self.__count(kind, self.class_scope_table.values())

        else:
            return self.__count(kind, self.subroutine_scope_table.values())

    def __count(self, kind, where):
        counter = 0
        for var_list in where:
            if var_list[KIND_INDEX] == kind:
                counter += 1
        return counter

    def kind_of(self, name):
        """
        :param name: The name of the variable
        :return: The kind of the named identifier in the current scope. If
        not in the scope returns NONE.
        """
        if name in self.subroutine_scope_table:
            return self.subroutine_scope_table[name][KIND_INDEX]
        if name in self.class_scope_table:
            return self.class_scope_table[name][KIND_INDEX]
        return None

    def type_of(self, name):
        """
        :param name: The name of the variable
        :return: the type of the named identifier in the current scope.
        """
        if name in self.subroutine_scope_table:
            return self.subroutine_scope_table[name][TYPE_INDEX]
        if name in self.class_scope_table:
            return self.class_scope_table[name][TYPE_INDEX]

    def index_of(self, name):
        if name in self.subroutine_scope_table:
            return self.subroutine_scope_table[name][NUMBER_INDEX]
        if name in self.class_scope_table:
            return self.class_scope_table[name][NUMBER_INDEX]
