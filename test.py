import os

os.chdir("URCLtoISA")
os.system(f"python urcl2isa -f test.urcl -t urcl/complex.utrx -o output.urcl")