from urclToISA.operand import Operand, OpType
from urclToISA.UTRX import Case, Translation
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

    def __init__(self, opcode="NOP", operands=[], labels=[]):
        # A unique ID to differentiate instructions with identical attribute values
        self.opcode = opcode
        self.operands = operands
        self.labels = labels

    @staticmethod
    def parse(instruction):
        # Split the instruction based on spaces, stripping comments
        words = instruction.split()
        # Can't parse nothing
        if len(words) == 0:
            return None
        # Collect any labels
        labels = []
        while words[0][0] == ".":
            labels.append(Operand.parse(words[0]))
            if len(words) == 1:
                return Instruction(labels=labels)
            words = words[1:]
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
        operands = []
        for word in words:
            operands.append(Operand.parse(word))
        return Instruction(opcode, operands, labels)

    # ======== Instruction methods ========

    def match(self, translation):
        for case in translation.cases:
            match = True
            for p,param in enumerate(case.params):
                if not Case.match(self.operands[p], param):
                    match = False
                    break
            if match:
                return copy.deepcopy(case.code)
        return None

    def toString(self, indent=0):
        out = "" if not self.labels else f"{' '.join(lab.toString() for lab in self.labels):>{indent}} "
        out += f"{self.opcode}" + " ".join(op.toString() for op in self.operands)
        return out

    def toColour(self, indent=0):
        out = Style.BRIGHT
        out += " "*(indent+1) if not self.labels else f"{Fore.YELLOW}{' '.join(lab.toString() for lab in self.labels):>{indent}} {Fore.RESET}"
        out += f"{Fore.BLUE}{self.opcode} {Style.RESET_ALL}" + " ".join(op.toColour() for op in self.operands)
        return out