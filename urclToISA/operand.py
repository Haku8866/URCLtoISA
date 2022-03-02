from enum import Enum
from colorama import Fore, Back, Style

# === Operand types ===
optypes = \
"""
REGISTER
NUMBER
ADDRESS
LABEL
PORT
RELATIVE
NEGATIVE
STACKPTR
OTHER
""".splitlines()

OpType = Enum("OpType", " ".join(optypes))

class Operand():
    # ======== Static variables ========

    # === Get symbol from type ===
    prefixes = {
        OpType.REGISTER: "$",
        OpType.ADDRESS:  "#",
        OpType.LABEL:    ".",
        OpType.PORT:     "%",
        OpType.RELATIVE: "~",
        OpType.NEGATIVE: "-",
        OpType.OTHER:    "@",
    }

    colours = {
        OpType.REGISTER: Fore.LIGHTCYAN_EX,
        OpType.ADDRESS:  Fore.GREEN,
        OpType.LABEL:    Fore.YELLOW,
        OpType.PORT:     Fore.GREEN,
        OpType.RELATIVE: Fore.YELLOW,
        OpType.NEGATIVE: Fore.RESET,
        OpType.OTHER:    Fore.RED,
    }

    # === Get type from symbol ===
    reverse_prefixes = dict((v,k) for k,v in prefixes.items())

    # === Define special parsing methods for types ===
    special_types = [
        # If special_types[n][0](operand_string) returns True, then operand_string's type is special_types[n][1]
        (lambda a: a[0].isnumeric(),                          OpType.NUMBER,   lambda a:a),
        (lambda a: a[0] == "0" and a[1].isalpha(),            OpType.NUMBER,   lambda a:str(int(a,base=0))),
        (lambda a: a[0].upper() == "M",                       OpType.ADDRESS,  lambda a:a[1:]),
        (lambda a: a[0].upper() == "R",                       OpType.REGISTER, lambda a:a[1:]),
        (lambda a: a == "SP",                                 OpType.STACKPTR, lambda :"SP"),
        (lambda a: a[0] == "+",                               OpType.NEGATIVE, lambda a: f"-{a}"),
    ]

    def __init__(self, type=OpType.NUMBER, value="", word=0, extra={}):
        # Type: OpType.REGISTER, OpType.ADDRESS, OpType.LABEL, ...
        self.type = type
        self.value = value
        # For multi-word processing
        self.word = word
        # Any extra information that may need to be stored
        self.extra = extra
        self.setTypeclass()

    # ======== Static methods ========
    @staticmethod
    def parse(operand):
        # Get the operand type
        typ = Operand.reverse_prefixes.get(operand[0])
        if typ is None:
            for sp_type in Operand.special_types:
                try:
                    if sp_type[0](operand):
                        typ = sp_type[1]
                        opr = sp_type[2](operand)
                except:
                    continue
        else:
            if typ in Operand.prefixes.keys():
                opr = operand[1:]
        if typ is None:
            raise ValueError(f"Cannot parse operand '{operand}', unknown type.")

        # Get word (for multiword code)
        if opr[-1] == "]" and "[" in opr:
            word = int(opr.split("[")[1][:-1])
        else:
            word = 0
        return Operand(typ, opr, word)

    # ======== Operand methods ========

    def setTypeclass(self):
        typeClass = "A"
        if self.type in [OpType.REGISTER]:
            typeClass += "R"
            if self.value == "0" and self.type == OpType.REGISTER:
                typeClass += "Z"
            if self.value == "SP":
                typeClass += "SP"
            if self.value.isnumeric():
                typeClass += "G"
        else:
            typeClass += "I"
            if self.value == "0" and self.type == OpType.NUMBER:
                typeClass += "Z"
            if self.type == OpType.NEGATIVE:
                typeClass += "C"
            if self.type == OpType.ADDRESS:
                typeClass += "M"
            if self.type == OpType.LABEL:
                typeClass += "L"
            if self.type == OpType.PORT:
                typeClass += "O"
        self.typeClass = typeClass

    def prefix(self):
        return Operand.prefixes.get(self.type, "")

    def toString(self):
        out = f"{self.prefix()}{self.value}"
        if self.word: out += f"[{self.word}]"
        return out

    def toColour(self):
        out = f"{Operand.colours.get(self.type, Fore.RESET)}{self.prefix()}{self.value}{Style.RESET_ALL}"
        if self.word: out += f"[{self.word}]"
        return out
