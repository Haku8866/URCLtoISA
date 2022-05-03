from urclToISA.program import Program
from urclToISA.translator import Translator
import colorama
from timeit import default_timer as timer

colorama.init(autoreset=True)

filename = "mycode.urcl"
URCLtranslations = "urclToISA/urcl.utrx"
ISAtranslations = "python.utrx"

start = timer()

main = Program.parseFile(filename)
translator = Translator.fromFile(URCLtranslations)
translatorISA = Translator.fromFile(ISAtranslations)

def translate(program, trans):
    done = False
    while not done:
        done = True
        for l,ins in enumerate(program.code):
            sub = trans.substituteURCL(ins)
            if sub != "":
                while len(set(sub.regs + program.regs)) != len(sub.regs + program.regs):
                    sub.primeRegs()
                sub.unpackPlaceholders()
                sub = translate(sub, trans)
                program.insertSub(sub, l)
                done = False
                break
    return program

def translateISA(program, trans):
    out = []
    for l,ins in enumerate(program.code):
        out += trans.substitute(ins)
    return out

main = translate(main, translator)

main.makeRegsNumeric()

end = timer()
print(f"-"*30)
print(f"{filename} translated to {URCLtranslations}:")
print(f"-"*30)
print(main.toColour(indent=20))
print(f"-"*30)
print(f"In {end-start:.10f} seconds.")
print(f"Registers used: {len(main.regs)}")
print(f"-"*30)

start = timer()
out = translateISA(main, translatorISA)
end = timer()
print(f"-"*30)
print(f"{filename} translated to {ISAtranslations}:")
print(f"-"*30)
for line in out:
    print(line)
print(f"-"*30)
print(f"In {end-start:.10f} seconds.")
print(f"-"*30)