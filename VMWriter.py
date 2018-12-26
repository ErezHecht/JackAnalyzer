class VMWriter:
    _OP_DICT = {"+": "add", "-": "sub", "=": "eq", "&": "and", "|": "or",
                ">": "gt", "<": "lt", "~": "not"}

    def __init__(self, out_address):
        self.out_address = out_address
        self.output = ""

    def write_file(self):
        with open(self.out_address, 'w') as f:
            f.write(self.output)

    def write_push(self, segment, index):
        self.output += "push {} {}\n".format(segment, str(index))

    def write_pop(self, segment, index):
        self.output += "pop {} {}\n".format(segment, str(index))

    def write_arithmetic(self, command):
        if command == "*":
            self.write_call("Math.multiply", 2)
        elif command == "/":
            self.write_call("Math.divide", 2)
        elif command == "neg":
            self.output += "neg\n"
        else:
            self.output += "{}\n".format(VMWriter._OP_DICT[command])

    def write_label(self, label):
        self.output += "label {}\n".format(label)

    def write_goto(self, label):
        self.output += "goto {}\n".format(label)

    def write_if(self, label):
        self.output += "if-goto {}\n".format(label)

    def write_call(self, name, nArgs):
        self.output += "call {} {}\n".format(name, str(nArgs))

    def write_function(self, name, nLocals):
        self.output += "function {} {}\n".format(name, str(nLocals))

    def write_return(self):
        self.output += "return\n"
