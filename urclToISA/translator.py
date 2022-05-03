from urclToISA.UTRX import Translation, Case
from urclToISA.instruction import Instruction
from urclToISA.program import Program
from urclToISA.operand import OpType

class Translator():
    def __init__(self, translations):
        self.translations = translations

    def substitute(self, ins):
        translation = self.translations.get(ins.opcode)
        if translation is None:
            return ""
        body = ins.match(translation)
        if body is None:
            return ""
        for l,line in enumerate(body):
            for i in range(len(ins.operands)):
                body[l] = body[l].replace(f"@{chr(65+i)}", ins.operands[i].toString())
        return body

    def substituteURCL(self, ins):
        translation = self.translations.get(ins.opcode)
        if translation is None:
            return ""
        body = ins.match(translation)
        if body is None:
            return ""
        sub = Program.parse(body)
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