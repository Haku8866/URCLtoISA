# About URCL
URCL is a "Universal Redstone Computer Language", it's an intermediate language, so it isn't designed to be run on CPUs directly.
URCL compiles to a specified ISA, documented in a config file.

## URCL Documentation
The URCL documentation can be found here: https://docs.google.com/spreadsheets/d/1YAVlzYkib-YHJEu_x28qC4iXJDnM_YTvCKMBYrJXIT0

--------------------

# What this compiler does
You can think of this is a framework to help you easily compile URCL to your ISA without starting from the ground up.
It does the vast majority of the work, and only leaves you to do CPU-specific parts.

# How to get URCL -> your ISA working
There's an example.utrx config file provided, this is roughly what a config file will look like.
There is also a template.utrx config file provided, this is a blank config file ready to be filled in.
Here's a list of things you need to do to support URCL:
 . Add translations written in your ISA for the 7 core URCL instructions.
 . Fill in the CPU stats section with your CPU's specs.
If your CPU is more complex, you may also need to:
 . Make a custom function for replacing labels with absolute memory addresses. (For variable length instructions)
 . Make adjustments to the URCL / ISA code at different intervals to better suit your ISA with custom functions.

--------------------

# Usage
The following command will translate the source code `YOURCODE.urcl` stored in the folder `prog` to
an assembly language called `YOURISA.utrx` stored in the `isa` folder.
```
py urcl2isa -f prog/YOURCODE.urcl -t isa/YOURISA.utrx
```
Note that these file names and folders are just examples, you may store either files anywhere as
long as you give the right path.

You may also convert from high-level URCL to low-level URCL:
```
py urcl2isa -f prog/YOURCODE.urcl -t urcl/core.utrx
```
You may also use `basic.utrx` and `complex.utrx`.

There are a number of flags you may provide too:
```
-f : File   : URCL file to be translated
-t : Target : UTRX file containing translations
-o : Output : File to store output in
-s : Silent : Hide terminal output
-b : Boring : Remove colour from terminal output :(
```