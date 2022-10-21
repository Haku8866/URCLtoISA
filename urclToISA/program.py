from urclToISA.operand import Operand, OpType
from urclToISA.instruction import Instruction
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
    def __init__(self, code:list[Instruction]=[], headers:dict[int, str]={}, regs:list[str]=[]):
        self.code = code
        self.headers = headers
        self.regs: list[str] = regs
        self.uid: int = 0

    def makeRegsNumeric(self):
        for i,ins in enumerate(self.code):
            for o,opr in enumerate(ins.operands):
                if opr.type == OpType.REGISTER and opr.value != "0":
                    self.code[i].operands[o].value = str(1+self.regs.index(opr.value))
        for r,reg in enumerate(self.regs):
            self.regs[r] = str(r+1)

    def primeRegs(self):
        for r,reg in enumerate(self.regs):
            if reg != "0":
                self.rename(reg, reg+"'")
            self.regs[r] = reg+"'"


    def uniqueLabels(self, uid=0):
        labels = {}
        # First pass update definitions
        for i,ins in enumerate(self.code):
            for l,label in enumerate(ins.labels):
                labels[label] = f"{label}_{uid}"
                self.code[i].labels[l] = labels[label]
                uid += 1
        # Second pass update references
        for i,ins in enumerate(self.code):
            for o,opr in enumerate(ins.operands):
                if opr.type == OpType.LABEL and labels.get(opr.value) is not None:
                    self.code[i].operands[o].value = labels[opr.value]
        return uid

    def insertSub(self, program, index=-1):
        self.uid = program.uniqueLabels(self.uid)
        self.replace(program, index)

    def replace(self, program, index=-1):
        labels = self.code[index].labels
        self.code[index:index+1] = program.code
        self.regs = list(set(self.regs + program.regs))
        self.code[index].labels += labels

    def insert(self, program, index=-1):
        self.code[index:index] = program.code
        self.regs = list(set(self.regs + program.regs))

    def rename(self, oldname: str, newname: str, type=OpType.REGISTER):
        for i,ins in enumerate(self.code):
            for o,opr in enumerate(ins.operands):
                if opr.type == type and opr.value == oldname:
                    self.code[i].operands[o].value = newname
        if opr.type == OpType.REGISTER:
            self.regs[self.regs.index(oldname)] = newname

    def unpackPlaceholders(self):
        for i,ins in enumerate(self.code):
            for o,opr in enumerate(ins.operands):
                if opr.type == OpType.OTHER:
                    if opr.value.isalpha() and len(opr.value) == 1:
                        self.code[i].operands[o] = opr.extra[opr.value]

    def relativesToLabels(self):
        for i,ins in enumerate(self.code):
            for o,opr in enumerate(ins.operands):
                if opr.type == OpType.RELATIVE:
                    self.code[i + int(opr.value)].labels.append(f"{ins.opcode}_{self.uid}")
                    self.code[i].operands[o] = Operand.parse(f".{ins.opcode}_{self.uid}")
                    self.uid += 1

    @staticmethod
    # The program is a list of strings
    def parse(program: list[str]):
        headers: dict[int, str] = {}
        code: list[Instruction] = []
        regs: list[str] = []
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
                if code[-1].opcode == "NOP":
                    if code[-1].labels is not None:
                        ins.labels += code[-1].labels
                    code = code[:-1]
            for operand in ins.operands:
                if operand.type == OpType.REGISTER:
                    if operand.value not in regs:
                        regs.append(operand.value)
            code.append(ins)
        return Program(code, headers, regs)

    @staticmethod
    def parseFile(filename: str):
        with open(filename, "r") as f:
            lines = [l.strip() for l in f]
        return Program.parse(lines)

    @staticmethod
    def parseHeader(line: str):
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