from urclToISA.program import Program
from urclToISA.instruction import Instruction
from urclToISA.UTRX import Translation, Case

myprog = Program.parseFile("mycode.urcl")
translations = Translation.parseFile("translations.utrx")

for line in myprog.code:
    if translations.get(line.opcodeString()) is not None:
        t = translations.get(line.opcodeString())
        body = line.match(t)
        if body is not None:
            print(f"{line.toColour()} becomes:\n {body}")
            continue
    print(f"{line.toColour()} has no translation. :(")