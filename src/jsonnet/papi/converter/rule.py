import os, json
from ...writer import JsonnetWriter
from .ruleformatentity import RuleFormatEntityConverter
from .variables import VariablesConverter
from ....utils import get_valid_filename, pushd

class RuleConverter(RuleFormatEntityConverter):
  def __init__(self, ruleFormat, rule, parent=None):
    super(RuleConverter, self).__init__(ruleFormat)
    self.rule = rule
    self.parent = parent

  @property
  def template(self):
    return "papi.root" if self.ruleName == "default" else "papi.rule"

  @property
  def ruleName(self):
    return self.rule.get("name")

  @property
  def normalizedName(self):
    name = "rules" if self.ruleName == "default" else self.ruleName
    return get_valid_filename(name)

  @property
  def filename(self):
    return "{}.jsonnet".format(self.normalizedName)

  def convert(self, writer):
    if self.ruleName != "default":
      self.convert_papi_import_statement(writer)

    writer.writeln('{} {{'.format(self.template))
    writer.writeln('name: {},'.format(json.dumps(self.ruleName)))

    if len(self.rule.get("comments", "")) > 0:
      writer.write('comments: ')
      writer.writeMultilineString(self.rule.get("comments", ""))
      writer.writeln(',')

    if "uuid" in self.rule:
      writer.writeln('uuid: {},'.format(json.dumps(self.rule.get('uuid'))))

    if "options" in self.rule:
      if len(self.rule.get("options")):
        writer.writeln("options: {")
        for (name, option) in self.rule.get("options").items():
          writer.writeln("{}: {},".format(name, json.dumps(option)))
        writer.writeln("},")

    if "variables" in self.rule:
      variablesWriter = JsonnetWriter()
      variablesConverter = VariablesConverter(self.ruleFormat, self.rule.get("variables"))
      variablesConverter.convert(variablesWriter)
      variablesWriter.dump('pmvariables.jsonnet')
      writer.writeln("variables: import 'pmvariables.jsonnet',")

    self.convert_criteria(writer)
    self.convert_behaviors(writer)
    self.convert_children(writer)

    if "customOverride" in self.rule:
      customOverride = self.rule.get("customOverride", {})
      if len(customOverride) > 0:
        writer.writeln("customOverride: {")
        for (k, v) in customOverride.items():
          writer.writeln("{}: {},".format(k, json.dumps(v)))
        writer.writeln("},")

    if "advancedOverride" in self.rule:
      xml = self.rule.get("advancedOverride")
      advancedOverridePath = "advancedOverride.xml"
      with open(advancedOverridePath, "w") as fd:
        print(advancedOverridePath)
        fd.write(xml)
      writer.writeln("advancedOverride: importstr 'advancedOverride.xml',")

    writer.writeln('}')

  def convert_criteria(self, writer):
    self.convert_criteria_or_behaviors("criteria", writer)
    if len(self.rule.get("criteria", [])):
      criteriaMustSatisfy = self.rule.get("criteriaMustSatisfy", "all")
      if criteriaMustSatisfy != "all":
        writer.writeln("criteriaMustSatisfy: {},".format(json.dumps(criteriaMustSatisfy)))

  def convert_behaviors(self, writer):
    self.convert_criteria_or_behaviors("behaviors", writer)

  def convert_children(self, writer):
    children = []
    from collections import Counter
    nameCounter = Counter()
    for child in self.rule.get("children", []):
      name_key = child["name"].lower()
      nameCounter[name_key] += 1
      if nameCounter[name_key] > 1:
        child["name"] = "{} {}".format(child["name"], nameCounter[name_key])
      children.append(RuleConverter(self.ruleFormat, child, self))
    if len(children):
      with pushd(self.normalizedName):
        writer.writeln("children: [")
        for child in children:
          childWriter = JsonnetWriter()
          child.convert(childWriter)
          childWriter.dump(child.filename)
          writer.writeln("import '{}',".format(os.path.join(self.normalizedName, child.filename)))
        writer.writeln("],")

  def convert_criteria_or_behaviors(self, ns, writer):
    results = []
    for atom in self.rule.get(ns, []):
      options_ruleFormat_ptr = "/definitions/catalog/{}/{}/properties/options/properties".format(ns, atom.get("name"))
      options_ruleFormat = self.ruleFormat.resolve_pointer(options_ruleFormat_ptr)
      converted = dict(name=atom.get("name"), options=dict())
      for (name, option) in atom.get("options", {}).items():
        if name in options_ruleFormat:
          # only include fields that are actually defined in the ruleFormat;
          # PAPI **will** return extraneous fields, which will then cause
          # trouble when we try to render the template back to json
          converted["options"][name] = option
      results.append(converted)
    if len(results):
      writer.writeln("{}: [".format(ns))
      for atom in results:
        writer.write("papi.{}.{}".format(ns, atom.get("name")))
        # The uuid is normally stored at the root of the atom, e.g. {name: 'caching', uuid: 'xyz', options: {...}}
        # Because we are generated simplified syntax, we output it as part of the body along with the options
        # e.g. papi.behaviors.caching { uuid: 'xyz', ... }
        if "uuid" in atom:
          if not "options" in atom:
            atom["options"] = {}
          atom["options"]["uuid"] = atom.get("uuid")
        if len(atom.get("options")):
          writer.write(" ")
          writer.write(json.dumps(atom.get("options"), indent="  "))
        writer.writeln(",")
      writer.writeln("],")
