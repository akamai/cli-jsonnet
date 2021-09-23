import os, json
from .ruleformatentity import RuleFormatEntityConverter

class VariablesConverter(RuleFormatEntityConverter):
  def __init__(self, ruleFormat, variables):
    super(VariablesConverter, self).__init__(ruleFormat)
    self.variables = variables

  def convert(self, writer):
    writer.writeln("[")
    for variable in self.variables:
      writer.writeln("{")
      for (name, value) in variable.items():
        writer.writeln("{}: {},".format(name, json.dumps(value)))
      writer.writeln("},")
    writer.writeln("]")
