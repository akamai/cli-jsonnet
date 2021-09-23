import json
from .ruleformatentity import RuleFormatEntityConverter
from .rule import RuleConverter

class RuleTreeConverter(RuleFormatEntityConverter):
  def __init__(self, ruleFormat, ruleTree):
    super(RuleTreeConverter, self).__init__(ruleFormat)
    self.ruleTree = ruleTree

  def convert(self, writer):
    self.convert_papi_import_statement(writer)
    writer.writeln('{')
    writer.writeln('productId: {},'.format(json.dumps(self.ruleFormat.product)))
    writer.writeln('ruleFormat: {},'.format(json.dumps(self.ruleFormat.ruleFormat)))
    if 'contractId' in self.ruleTree:
      writer.writeln('contractId: {},'.format(json.dumps(self.ruleTree.get('contractId'))))
    if 'groupId' in self.ruleTree:
      writer.writeln('groupId: {},'.format(json.dumps(self.ruleTree.get('groupId'))))
    writer.write('rules: ')
    defaultRule = RuleConverter(self.ruleFormat, self.ruleTree.get("rules"), self)
    defaultRule.convert(writer)
    writer.writeln('}')
