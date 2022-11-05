# Overview
UTRX (URCL Translation RegeX) is a formal way to define implementations for URCL instructions. The implementation may be written in any language, provided that its syntax does not clash with the structure of UTRX files as described below.

# Structure

The structure of a UTRX implementation is shown here: 
```
INS :: Type1 Type2 Type3 {
    ... implementation code ...
}
```
`INS` is the opcode of the URCL instruction.

`Type1`, `Type2` and `Type3` specify the number of operands the instruction takes and importantly what type the operands should be. This is because, for example, adding a register and an immediate may be a different process to adding a register and a register.

# Operand types

The valid operand types are:
```
  A - any
  R - any register
  G - general purpose register (R1, R2, ...)
  V - volatile register
  Z - zero register and/or constant 0
  S - stack pointer (falls under R)
  P - pointer
  N - register containing signed integer
  I - any immediate
  M - immediate memory address
  L - immediate label
  O - immediate port
  C - signed immediate (denoted by +/-)
```
One operand can belong to many of these classes, for example, `R1` could match any of `A, R, G, V, P, N` under the right circumstances.

`V` means that the contents of the register do not need to be preserved after the instruction is executed. 

`P` means that the register contains any label or memory address.

There are also a handful of extra conditions you can apply to the operands with these affixes:
```
    Prefixes: // These go at the start of parameters: R R !Z
      ! - negate condition
      $ - match value as string (anything after this symbol is part of the string until a | or $ is reached)
      > - match value in range (>15 means greater than 15)
      < - match value in range (<20 means less than 20)
    Infixes: // These go between parameters: R R <> R
      <> - are interchangeable
      == - are equal
      != - are not equal
      ~~ - are of the same type (register or immediate)
      !~ - are not of the same type (register or immediate)
```
An infix on the end of a definition with no parameter on the right
will wrap around and compare to parameter `@A`.

# Using operands in implementation

Parameters from left to right are referenced in the code using `@A`, `@B`, `@C`, `@D` ...

# Examples

**UTRX:**
```
INS :: A A R !=
```
**English:**
```
INS takes 3 operands A, B, C where C is a register and C is not equal to A
```
#

**UTRX:**
```
INS :: R R <> I
```
**English:**
```
INS takes 3 operands A, B, C where either:
A and B are registers and C is an immediate
Or:
A and C are registers and B is an immediate.
```
It matches both of these URCL instructions:
```
INS R1 R2 .label
INS R1 .label R2
```
But not:
```
INS R1 R2 R3
```

#

**UTRX:**
```
INS :: A == A
```
**English:**
```
INS takes 2 operands A, B where A must equal B.
```
Matches both:
```
INS R1 R1
INS .label .label
```
But not:
```
INS R1 R2
INS .label .label2
```
# Advanced UTRX

Types can be OR'd together by adding more letters.
The ! prefix inverts the conditions applied by the type requirements.

**UTRX:**
```
INS :: R ZSI !ZSI
```
**English:**
```
INS takes 3 operands A, B, C where:
A is a register, 
B is the zero reg, the SP, or an immediate and
C is not the zero reg, not the SP, and not an immediate.
```
# Temporary registers

If the implementation is written in URCL (such as providing a complex to core translation or defining your own custom URCL instruction) then you may want to use temporary registers.

To do this, you can simply use `R1, R2, ..., Rn` as normal:
```
INS :: A A A {
    IMM R1 15 // Using a temp-reg
    ADD @A @B @C
    ADD @A @B R1
}
```
This will not actually use `R1` in the main program - `R1` will be swapped out for an unused register or the stack will be used instead.

# Ports and constants

You can specify specific operands by using $.

**UTRX:**
```
INS :: A A I$15
```
**English:**
```
INS takes 3 operands A, B, C where C is the number 15.
```
#
**UTRX:**
```
INS :: A R$1
```
**English:**
```
INS takes 2 operands A, B, where B is the register R1.
```
# Port example
**UTRX:**
```
OUT :: O$NUMB A
```
**English**:
```
Matches the URCL instruction OUT when the port is %NUMB
```
This is an important example, as you can have multiple implementations for `O$X`, `O$Y` and `O$BUFFER` and so on.

# Descriptions

A short description can be given by using `/* */`.
The opcode of the instruction must be stated after the opening `/*`.
Do not write on the same line as `*/`.

A custom language can be specified for the translation.
If no custom language is provided, URCL is the default.
Finally, do not use `/* */` for regular multiline comments. Use `//` instead.
```
/* INS language
This is a description of the INS instruction.
*/
INS :: A A A { 
    ...
}
```
# Overloading

You can define cases for overloads too:
```
INS :: A
INS :: A A
INS :: A A A
```
May all exist in the same file. However, the version with the least number of operands must come first.

# A real example
```
/* SGE URCL
Same as BGE except parameters B and C contain 2s complement signed values.
*/
SGE :: A A V {
    SUB @C @B @C
    BGE @A @C @MSB
}
SGE :: A V A {
    SUB @B @B @C
    BGE @A @B @MSB
}
SGE :: A A A {
    SUB R1 @B @C
    BGE @A R1 @MSB
}
```
# Another real example
```
/* AND URCL
Performs bitwise AND on paramters B and C, storing the result in A.
*/
AND :: A A == A {
    MOV @A @C
}
AND :: A A <> Z {
    IMM @A 0
}
AND :: A A R != {
    NOT @A @B
    NOT @C @C
    NOR @A @A @C
    NOT @C @C
}
AND :: A != R A {
    NOT @B @B
    NOT @A @C
    NOR @A @A @B
    NOT @B @B
}
```