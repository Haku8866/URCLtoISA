from urclToISA.instruction import Instruction, Opcode
from urclToISA.operand import Operand, OpType
from enum import Enum
from colorama import init

init(autoreset=True)

headers = \
"""
BITS
MINREG
MINHEAP
RUN
MINSTACK
""".splitlines()

Header = Enum("Header", " ".join(headers))

class Program():
    def __init__(self, code=[], headers={}):
        self.code = code
        self.headers = headers

    @staticmethod
    # The program is a list of strings
    def parse(program):
        headers = {}
        code = []
        skip = False
        for line in program:
            if "*/" in line:
                skip = False
                continue
            elif skip:
                continue
            elif "/*" in line:
                skip = True
                continue
            while "  " in line:
                line = line.replace("  "," ")
            line = line.split("//")[0]
            header = Program.parseHeader(line)
            if header is not None:
                headers[header[0]] = header[1]
                continue
            ins = Instruction.parse(line)
            if ins is None:
                continue
            if len(code) > 0:
                if code[-1].opcode == Opcode.NOP:
                    if code[-1].labels is not None:
                        ins.labels += code[-1].labels
                    code = code[:-1]
            code.append(ins)
        return Program(code, headers)

    @staticmethod
    def parseFile(filename):
        with open(filename, "r") as f:
            lines = [l.strip() for l in f]
        return Program.parse(lines)

    @staticmethod
    def parseHeader(line):
        line = line.split()
        if len(line) < 2 or line[0] not in headers:
            return None
        try:
            return (headers.index(line[0]), line[1:])
        except:
            return None

    def toString(self, indent=0):
        return "\n".join(l.toString(indent=indent) for l in self.code)
    
    def toColour(self, indent=0):
        return "\n".join(l.toColour(indent=indent) for l in self.code)