from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from operand import Operand
  from translator import Translation
import copy

class Case():
  alphabet = "QWERTYUIOPASDFGHJKLZXCVBNM"
  prefixes = ["!", "$", ">", "<"]
  typeClasses = {
    "A": ["RVSNGZPIMLCO"],
    "R": ["VSNGZP"],
    "I": ["MLCZO"],
    "G": ["VSNP"],
    "P": ["S"]
  }
  types = "ARVSNGZPIMLCO"

  def __init__(self, params: str, body: list[str], language="URCL"):
    self.params = copy.deepcopy(params).split()
    self.string = copy.deepcopy(params)
    self.code = copy.deepcopy(body)
    self.language = copy.deepcopy(language)

  @staticmethod
  def match(operand: "Operand", param: str):
    invert = False
    typeMatch = False
    readNum = False
    readStr = False
    num = ""
    s = ""
    sym = ""

    for c,char in enumerate(param):
      if char == "$" and not readStr:
        readStr = True
        continue
      if readStr and char not in "$":
        s += char
      if readStr and (c == len(param)-1 or char in "$"):
        if char not in "$":
          readStr = False
        if (str(operand.value) != s) != invert:
          return False
        s = ""
        continue
      if readStr:
        continue
      if readNum and char.isnumeric() or char in "+-.":
        num += char
      if readNum and (c == len(param)-1 or not param[c+1].isnumeric()):
        readNum = False
        if sym == ">":
          if (int(operand.value) <= int(num)) != invert:
            return False
        if sym == "<":
          if (int(operand.value) >= int(num)) != invert:
            return False
        num = ""
        continue
      if readNum:
        continue
      if char == "!":
        invert = not invert
      if char in Case.types and not typeMatch:
        if (char in operand.typeClass) != invert:
          typeMatch = True
          continue
      if char in "<>":
        sym = char
        readNum = True
        continue

    return typeMatch


class Translation():
  def __init__(self, opcode: str, language="URCL", description:list[str]=[], cases:list[Case]=[]):
    self.opcode = opcode
    self.description = description
    self.cases = cases
    self.language = language

  def toString(self):
    m = max(map(lambda a: len(a), self.description)) + 4
    out = "┌" + "─"*(m-2) + "┐"
    out += "\n│ " + f"{self.opcode:^{m-4}}" + " │"
    out += "\n│ " + f"{'Language: ' + self.language:^{m-4}}" + " │"
    out += "\n├" + "─"*(m-2) + "┤"
    for line in self.description:
      out += "\n│ " + f"{line:<{m-4}}" + " │"
    out += "\n├" + "─"*(m-2) + "┤"
    for case in self.cases:
      out += "\n│ " + f"{self.opcode + ' :: ' + case.string:^{m-4}}" + " │"
      for line in case.code:
        out += "\n│ " + f"{line:<{m-4}}" + " │"
      out += "\n├" + "─"*(m-2) + "┤"
    out += "\n└" + "─"*(m-2) + "┘"
    return out

  @staticmethod
  def parseDescriptions(unparsed: str):
    translations: dict[str, "Translation"] = {}
    desc = False
    for l, line in enumerate(unparsed):
      if line.startswith("/*"):
        if len(line.split()) > 2:
          lang = " ".join(line.split()[2:])
        else:
          lang = "URCL"
        translation = copy.deepcopy(Translation(line.split()[1], lang))
        desc = True
        unparsed[l] = None
        continue
      if desc:
        if line.startswith("*/"):
          desc = False
          translations[translation.opcode] = translation
        else:
          translation.description.append(line)
        unparsed[l] = None
      elif " :: " in line and line[-1] == "{":
        if translations.get(line.split(" :: ")[0]) is None:
          translations[line.split(" :: ")[0]] = copy.deepcopy(Translation(line.split(" :: ")[0], "URCL", "This instruction is undocumented. :("))
    unparsed = list(filter(None, unparsed))
    return translations, unparsed

  @staticmethod
  def readFile(filename: str):
    lines: list[str] = []
    with open(filename, "r") as f:
      for line in f:
        lines.append(line.rstrip("\n"))
    return lines

  @staticmethod
  def readCases(translations: dict[str, "Translation"], unparsed: str):
    body: list[str] = []
    opcode = ""
    params = ""
    bits = -1
    mappings = {}
    for line in unparsed:
      if opcode:
        if line == "}":
          newcase = Case(params, body, translations[opcode].language)
          translations[opcode].cases.append(copy.deepcopy(newcase))
          opcode = ""
          body = []
        else:
          body.append(line)
      elif " :: " in line and line[-1] == "{":
        opcode, params = line.split(" :: ")
        if params == ["{"]:
          params = ""
        else:
          params = params.rstrip("{")
      else:
        if line.startswith("@BITS "):
          bits = int(line.split()[1])
        elif line.startswith("@DEFINE "):
          mappings[line.split()[1]] = line.split()[2]
    return translations, bits, mappings

  @staticmethod
  def parseFile(filename):
    unparsed = Translation.readFile(filename)
    translations, unparsed = Translation.parseDescriptions(unparsed)
    translations, bits, mappings = Translation.readCases(translations, unparsed)
    return translations, bits, mappings