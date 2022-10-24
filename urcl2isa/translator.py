from typing import TYPE_CHECKING
from operand import OpType
from UTRX import Translation
from program import Program
from copy import deepcopy
if TYPE_CHECKING: from instruction import Instruction
class Translator():
    def __init__(self, translations: dict[str, Translation]):
        self.translations = translations

    def substitute(self, ins: "Instruction"):
        translation = self.translations.get(ins.opcode)
        if translation is None:
            return None
        body = ins.match(translation)
        if body is None:
            return None
        for l,line in enumerate(body):
            for i in range(len(ins.operands)):
                body[l] = body[l].replace(f"@{chr(65+i)}", ins.operands[i].toString())
        return body

    def substituteURCL(self, ins: "Instruction", wordSize: int=8):
        translation = self.translations.get(ins.opcode)
        if translation is None:
            return None
        body = ins.match(translation)
        if body is None:
            return None
        sub = Program.parse(body, wordSize)
        for i,instr in enumerate(sub.code):
            for o,opr in enumerate(instr.operands):
                if opr.type == OpType.OTHER:
                    if opr.value.isalpha() and len(opr.value) == 1:
                        placeholder = ins.operands[ord(opr.value)-65]
                        opr.extra[opr.value] = placeholder
        return sub

    @staticmethod
    def fromFile(filename):
        translations = Translation.parseFile(filename)
        return Translator(translations)