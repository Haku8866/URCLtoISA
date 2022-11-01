from operand import Operand, OpType
from instruction import Instruction
from enum import Enum
from colorama import init
from copy import deepcopy

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
        regList = []
        for i,ins in enumerate(self.code):
            for o,opr in enumerate(ins.operands):
                if opr.type == OpType.REGISTER and opr.value != "0":
                    if opr.value not in regList:
                        regList.append(opr.value)
                    self.code[i].operands[o].value = str(1+regList.index(opr.value))
        for r,reg in enumerate(regList):
            regList[r] = str(r+1)
        self.regs = regList

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

    def insertSub(self, program, index=-1, limit=128):
        self.uid = program.uniqueLabels(self.uid)
        self.replace(program, index, limit)

    def replace(self, program, index=-1, limit=128):
        program = Program.useLessRegisters(self, program, limit)
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
                        self.code[i].operands[o] = deepcopy(opr.extra[opr.value])

    def relativesToLabels(self):
        for i,ins in enumerate(self.code):
            for o,opr in enumerate(ins.operands):
                if opr.type == OpType.RELATIVE:
                    self.code[i + int(opr.value)].labels.append(f"{ins.opcode}_{self.uid}")
                    self.code[i].operands[o] = Operand.parse(f".{ins.opcode}_{self.uid}")
                    self.uid += 1

    def removeDW(self):
        count = 0
        # Find out how much memory is going to be required
        for ins in self.code:
            if ins.opcode == "DW":
                count += 1
        # Free up the required memory slots
        for i, ins in enumerate(self.code):
            for o, opr in enumerate(ins.operands):
                if opr.type == OpType.ADDRESS:
                    self.code[i].operands[o].value += count
        # Move the values in 'DW's to memory with 'STR's
        insert = []
        count = 0
        labelDict = {}
        for i, ins in enumerate(self.code):
            if ins.opcode == "DW":
                for lbl in ins.labels:
                    labelDict[lbl[1:]] = count
                opr = ins.operands[0]
                insert.append(f"STR #{count} {opr.toString()}")
                count += 1
                self.code[i] = Instruction()
        insert = Program.parse(insert)
        self.code[0:0] = insert.code
        for i, ins in enumerate(self.code):
            for o, opr in enumerate(self.code[i].operands):
                if opr.type == OpType.LABEL and labelDict.get(opr.value) is not None:
                    self.code[i].operands[o].type = OpType.ADDRESS
                    self.code[i].operands[o].value = labelDict[opr.value]
        self.optimise()

    def translate(self, trans, superTrans=None, limit=128):
        done = False
        while not done:
            done = True
            for l,ins in enumerate(self.code):
                if superTrans is not None:
                    if superTrans.substitute(ins) is not None:
                        continue
                sub: Program = trans.substituteURCL(ins)
                if sub is not None:
                    while len(set(sub.regs + self.regs)) != len(sub.regs + self.regs):
                        sub.primeRegs()
                    sub.unpackPlaceholders()
                    sub.translate(trans, superTrans)
                    self.insertSub(sub, l, limit)
                    done = False
                    break

    def optimise(self, optimisations=None, limit=128):
        if optimisations is not None:
            self.translate(optimisations, limit=limit)
        for i, ins in enumerate(self.code):
            if i > 0:
                prins = self.code[i-1]
                if prins.opcode in ("PSH", "POP") and \
                   ins.opcode in ("PSH", "POP") and \
                   prins.opcode != ins.opcode and \
                   prins.operands[0].equals(ins.operands[0]):
                    self.code[i-1].opcode = "NOP"
                    self.code[i].opcode = "NOP"

        self.code = list(filter(lambda i: i.opcode != "NOP", self.code))

    def foldRegisters(self, amount):
        self.makeRegsNumeric()
        if len(self.regs) <= amount: return
        for r in range(amount, len(self.regs)):
            self.code[0:0] = [Instruction.parse(f".R{r+1} DW 0")]
        done = False
        while not done:
            done = True
            for i, ins in enumerate(self.code):
                used = []
                for o, opr in enumerate(ins.operands):
                    if opr.type == OpType.REGISTER and int(opr.value) <= amount:
                        used.append(int(opr.value))
                a = set(self.regs[:amount+1]).difference(used)
                head = []
                tail = []
                subbed = {}
                for o, opr in enumerate(ins.operands):
                    if opr.type == OpType.REGISTER and subbed.get(int(opr.value)) is not None:
                        self.code[i].operands[o].value = subbed[int(opr.value)]
                        continue
                    if opr.type == OpType.REGISTER and int(opr.value) > amount:
                        done = False
                        r = a.pop()
                        subbed[int(opr.value)] = r
                        head += [Instruction.parse(x) for x in [
                            f"PSH R{r}",
                            f"LOD R{r} .R{opr.value}",
                        ]]
                        tail += [Instruction.parse(x) for x in [
                            f"STR .R{opr.value} R{r}",
                            f"POP R{r}"
                        ]]
                        self.code[i].operands[o].value = f"{r}"
                if not done:
                    self.code[i+1:i+1] = tail
                    lab = ins.labels
                    self.code[i].labels = []
                    self.code[i:i] = head
                    self.code[i].labels = lab
                    break

    @staticmethod
    def useLessRegisters(mainProg: "Program", insert: "Program", amount=128):
        """ This is for when you are merging a subprogram into a main program.
            This is not to simply reduce the number of registers used in a
            standalone program. """
        totalregs = list(set(mainProg.regs + insert.regs))
        if len(totalregs) > amount:
            head = []
            tail = []
            reuse = mainProg.regs[:len(totalregs)-amount]
            for r,reg in enumerate(reuse):
                head.append(Instruction("PSH", [Operand(OpType.REGISTER, value=reg)]))
                tail[0:0] = [Instruction("POP", [Operand(OpType.REGISTER, value=reg)])]
                old = insert.regs[-1]
                insert.rename(old, reg)
                insert.regs = [reg] + insert.regs[:-1]
                totalregs.remove(old)
            insert.code[0:0] = head
            insert.code += tail
        return insert

    @staticmethod
    # The program is a list of strings
    def parse(program: list[str], wordSize: int=8):
        headers: dict[int, str] = {}
        code: list[Instruction] = []
        regs: list[str] = []
        skip = False

        for l,line in enumerate(program):
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
            ls = line.split()
            if len(ls) == 3:
                if ls[0] == "@DEFINE":
                    old, new = ls[1:]
                    for s,subline in enumerate(program[l:]):
                        program[l+s] = subline.replace(f"{old}", f"{new}")
                    continue

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
            for o,operand in enumerate(ins.operands):
                if operand.type == OpType.REGISTER:
                    if operand.value not in regs and operand.value != "0":
                        regs.append(operand.value)
                if operand.type == OpType.OTHER:
                    v = operand.value
                    if v == "MAX":
                        v = 2**(wordSize)-1
                    elif v == "SMAX":
                        v = 2**(wordSize)-1 - 2**(wordSize-1)
                    elif v == "MSB":
                        v = 2**(wordSize-1)
                    elif v == "SMSB":
                        v = 2**(wordSize-2)
                    elif v == "UHALF":
                        v = 2**(wordSize) - 2**(wordSize/2)
                    elif v == "LHALF":
                        v = 2**(wordSize/2)-1
                    elif v == "BITS":
                        v = wordSize
                    else:
                        continue
                    ins.operands[o].value = int(v)
                    ins.operands[o].type = OpType.NUMBER
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