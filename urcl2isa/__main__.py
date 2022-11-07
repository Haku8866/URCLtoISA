def main():
    from program import Program
    from translator import Translator
    from instruction import Instruction
    from isa import Block
    import colorama
    from timeit import default_timer as timer
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("-f", "--File", help="URCL file to be translated")
    p.add_argument("-t", "--Target", help="UTRX file containing translations")
    p.add_argument("-o", "--Output", help="File to store output in")
    p.add_argument("-s", "--Silent", help="Hide terminal output")
    p.add_argument("-b", "--Boring", help="Give uncoloured output")
    p.add_argument("-w", "--WordSize", help="The size of a word")
    p.add_argument("-r", "--Minreg", help="Set the MINREG of the output")

    argv = p.parse_args()

    colorama.init(autoreset=True)
    filename = "mycode.urcl"
    if argv.File:
        filename = argv.File
    ISAtranslations = "urcl/complex.utrx"
    if argv.Target:
        ISAtranslations = argv.Target
    wordSize = 8
    if argv.WordSize:
        wordSize = int(argv.WordSize)

    URCLtranslations = "urcl2isa/instructions/urcl.utrx"
    URCLoptimisations = "urcl2isa/instructions/optimise.utrx"
    URCLextra = "urcl2isa/instructions/custom.utrx"

    start = timer()

    main = Program.parseFile(filename)

    minreg = len(main.regs)
    if argv.Minreg:
        minreg = int(argv.Minreg)

    translator = Translator.fromFile(URCLtranslations)
    translatorISA = Translator.fromFile(ISAtranslations)
    if translatorISA.bits > 0:
        wordSize = translatorISA.bits
    optimisations = Translator.fromFile(URCLoptimisations)
    extra = Translator.fromFile(URCLextra)
    translator.merge(extra)

    def translateISA(program: Program, trans: Translator):
        out: list[Block] = []
        for i,ins in enumerate(program.code):
            sub: list[str] = trans.substitute(ins)
            if sub is None:
                print(f"*** Warning: No translation for: {ins.toString()} ***")
                sub = []
            else:
                for l, line in enumerate(sub):
                    for old in trans.mappings:
                        new = trans.mappings[old]
                        sub[l] = line.replace(old, new)
            out.append(Block(ins.labels, sub))
        return out

    main.foldRegisters(minreg)
    rmDW = (translatorISA.substitute(Instruction.parse("DW 0")) is None)
    if rmDW:
        main.removeDW()
    main.translate(translator, translatorISA, minreg)
    main.makeRegsNumeric()
    main.relativesToLabels()
    if rmDW:
        main.removeDW()
    main.optimise(optimisations, limit=minreg)

    end = timer()
    txturcl = f" {filename} translated to {URCLtranslations} "
    txtisa = f" {filename} translated to {ISAtranslations} "
    size = max(len(txturcl), len(txtisa))
    if not argv.Silent:
        print("+"+f"-"*size+"+")
        print("|"+ f"{txturcl:<{size}}" +"|")
        print("+"+f"-"*size+"+")
        if argv.Boring:
            print(main.toString(indent=20))
        else:
            print(main.toColour(indent=20))
        print("+"+f"-"*size+"+")
        print("|"+f"{' @MINREG '+str(len(main.regs))+' ':<{size}}|")
        print("+"+f"-"*size+"+")

    start = timer()
    out = translateISA(main, translatorISA)
    end = timer()

    if not argv.Silent:
        print("+"+f"-"*size+"+")
        print("│"+ f"{txtisa:<{size}}" + "│")
        print("+"+f"-"*size+"+")
        for block in out:
            block.print(indent=20)
        print("+"+f"-"*size+"+")
        time = f" In {end-start:.10f} seconds. "
        print("│"+f"{time:<{size}}│")
        print("+"+f"-"*size+"+")

    if argv.Output:
        with open(argv.Output, "w+") as f:
            if ISAtranslations not in ["urcl/core.utrx", "urcl/basic.utrx", "urcl/complex.utrx"]:
                for block in out:
                    f.write(block.toString() + "\n")
            else:
                for block in out:
                    lines = block.URCL_labels + block.code
                    for l in lines:
                        f.write(l + "\n")

if __name__ == "__main__":
    main()