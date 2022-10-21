from urclToISA.operand import Operand
from urclToISA.UTRX import Case
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from urclToISA.translator import Translation
from enum import Enum
from colorama import Fore, Back, Style
import copy

# === Opcodes ===
opcodes = \
"""
ADD
RSH
LOD
STR
BGE
NOR
IMM
SUB
JMP
MOV
NOP
LSH
INC
DEC
NEG
AND
OR
NOT
XNOR
XOR
NAND
BRL
BRG
BRE
BNE
BOD
BEV
BLE
BRZ
BNZ
BRN
BRP
PSH
POP
CAL
RET
HLT
CPY
BRC
BNC
MLT
DIV
MOD
BSR
BSL
SRS
BSS
SETE
SETNE
SETG
SETL
SETGE
SETLE
SETC
SETNC
LLOD
LSTR
IN
OUT
""".splitlines()

class Instruction():
    # ======== Static variables ========
    # There are none

    def __init__(self, opcode="NOP", operands:list["Operand"]=[], labels:list["Operand"]=[]):
        # A unique ID to differentiate instructions with identical attribute values
        self.opcode = opcode
        self.operands = operands
        self.labels = labels

    @staticmethod
    def parse(instruction: str):
        # Split the instruction based on spaces, stripping comments
        words = instruction.split()
        # Can't parse nothing
        if len(words) == 0:
            return None
        # Collect any labels
        labels: list["Operand"] = []
        while words[0][0] == ".":
            labels.append(words[0])
            if len(words) == 1:
                return Instruction(labels=labels)
            words.pop()
        # Attempt to recognise an opcode, if can't then assume NOP
        opcode = None
        for opc in opcodes:
            if opc == words[0]:
                opcode = opc
        if not opcode:
            raise ValueError(f"Cannot parse instruction '{instruction}', unknown opcode.")
        if len(words) == 1:
            return Instruction(opcode)
        words = words[1:]
        operands: list[Operand] = []
        for word in words:
            operands.append(Operand.parse(word))
        return Instruction(opcode, operands, labels)

    # ======== Instruction methods ========

    def match(self, translation: "Translation"):
        for case in translation.cases:
            backup = self.operands
            match = True
            opNum = 0
            infixes = ["==", "~~", "<>", "!=", "!~"]
            for p,param in enumerate(case.params):
                if param in infixes:
                    op1 = self.operands[opNum]
                    op2 = self.operands[(opNum + 1) % len(self.operands)]
                    if param == "==" and (op1.value != op2.value or  op1.type != op2.type) \
                    or param == "!=" and (op1.value == op2.value and op1.type == op2.type) \
                    or param == "~~" and (op1.type != op2.type) \
                    or param == "!~" and (op1.type == op2.type):
                        match = False
                        break
                    if param == "<>":
                        if not (Case.match(op1, case.params[p-1]) and Case.match(op2, case.params[(p+1) % len(case.params)])):
                            if (Case.match(op2, case.params[p-1]) and Case.match(op1, case.params[(p+1) % len(case.params)])):
                                self.operands[opNum] = op2
                                self.operands[(opNum+1)%len(self.operands)] = op1
                            else:
                                match = False
                                break
                        opNum += 1
                        continue
                else:
                    if param != case.params[-1]:
                        if case.params[p+1] == "<>":
                            continue
                    if not Case.match(self.operands[opNum], param):
                        match = False
                        break
                    opNum += 1
            if match:
                return copy.deepcopy(case.code)
            self.operands = backup
        return None

    def toString(self, indent=0):
        out = "" if not self.labels else f"{' '.join(self.labels):>{indent}} "
        out += f"{self.opcode}" + " ".join(op.toString() for op in self.operands)
        return out

    def toColour(self, indent=0):
        out = Style.BRIGHT
        out += " "*(indent+1) if not self.labels else f"{Fore.YELLOW}{' '.join(self.labels):>{indent}} {Fore.RESET}"
        out += f"{Fore.BLUE}{self.opcode} {Style.RESET_ALL}" + " ".join(op.toColour() for op in self.operands)
        return out