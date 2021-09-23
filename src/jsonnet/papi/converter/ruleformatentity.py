import os, json
from .base import BaseConverter

class RuleFormatEntityConverter(BaseConverter):
  def __init__(self, ruleFormat):
    super(RuleFormatEntityConverter, self).__init__()
    self.ruleFormat = ruleFormat

  def convert_papi_import_statement(self, writer):
    writer.writeln("local papi = import 'papi/{}/{}.libsonnet';".format(self.ruleFormat.product, self.ruleFormat.ruleFormat))

  def convert(self, writer):
    writer.writeln("[")
    for variable in self.variables:
      writer.writeln("{")
      for (name, value) in variable.items():
        writer.writeln("{}: {},".format(name, json.dumps(value)))
      writer.writeln("},")
    writer.writeln("]")
    self.convert_to(self.path)
