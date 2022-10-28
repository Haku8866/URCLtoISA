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
    translator = Translator.fromFile(URCLtranslations)
    translatorISA = Translator.fromFile(ISAtranslations)
    optimisations = Translator.fromFile(URCLoptimisations)
    extra = Translator.fromFile(URCLextra)
    translator.merge(extra)

    def translateISA(program: Program, trans: Translator):
        out: list[Block] = []
        for l,ins in enumerate(program.code):
            sub: list[str] = trans.substitute(ins)
            if sub is None:
                print(f"*** Warning: No translation for: {ins.toString()} ***")
                sub = []
            out.append(Block(ins.labels, sub))
        return out

    regLimit = len(main.regs)
    rmDW = (translatorISA.substitute(Instruction.parse("DW 0")) is None)
    if rmDW:
        main.removeDW()
    main.translate(translator, translatorISA, regLimit)
    main.makeRegsNumeric()
    main.relativesToLabels()
    if rmDW:
        main.removeDW()
    main.optimise(optimisations, limit=regLimit)

    end = timer()

    if not argv.Silent:
        print(f"-"*30)
        print(f"{filename} translated to {URCLtranslations}:")
        print(f"-"*30)
        if argv.Boring:
            print(main.toString(indent=20))
        else:
            print(main.toColour(indent=20))
        print(f"-"*30)
        print(f"In {end-start:.10f} seconds.")
        print(f"Registers used ({len(main.regs)}): {main.regs}")
        print(f"-"*30)

    start = timer()
    out = translateISA(main, translatorISA)
    end = timer()

    if not argv.Silent:
        print(f"-"*30)
        print(f"{filename} translated to {ISAtranslations}:")
        print(f"-"*30)
        for block in out:
            block.print(indent=20)
        print(f"-"*30)
        print(f"In {end-start:.10f} seconds.")
        print(f"-"*30)

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