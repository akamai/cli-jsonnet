import json
from jsonpointer import resolve_pointer
from ...edgegrid import Session
from ..writer import JsonnetWriter
import os
import re

def get_valid_filename(filename):
  """
  Return the given string converted to a string that can be used for a clean
  filename. Remove leading and trailing spaces; convert other spaces to
  underscores; and remove anything that is not an alphanumeric, dash,
  underscore, or dot.
  >>> get_valid_filename("john's portrait in 2004.jpg")
  'johns_portrait_in_2004.jpg'

  (stolen from: https://github.com/django/django/blob/master/django/utils/text.py)
  """
  s = filename.strip().replace(' ', '_')
  return re.sub(r'(?u)[^-\w.]', '', s)

class Property:
  @staticmethod
  def get(edgerc, section, name, version="latest", ruleFormat=None, accountSwitchKey=None):
    print("retrieving property json for", name, version)
    session = Session(edgerc, section, accountSwitchKey)
    headers = {}
    response = session.post("/papi/v1/search/find-by-value", json={"propertyName": name})
    versions = response.json().get("versions").get("items")

    pid = next(version.get("propertyId") for version in versions)
    pv = max(version.get("propertyVersion") for version in versions)
    if version != "latest":
      pv = version

    if ruleFormat is not None:
      accept = "application/vnd.akamai.papirules.{}".format(ruleFormat)
      headers["Accept"] = accept
    url = "/papi/v1/properties/{}/versions/{}/rules".format(pid, pv)
    response = session.get(url, headers=headers, params=dict(validateRules=False, validateMode="fast"))
    data = response.json()
    return Property(name, data)

  def __init__(self, name, data):
    self.name = name
    self.data = data

class BaseConverter:
  def __init__(self, schema):
    self.schema = schema
    self.writer = JsonnetWriter()

  def write_papi_import_statement(self):
    self.writer.writeln("local papi = import 'papi/{}/{}.libsonnet';".format(self.schema.product, self.schema.ruleFormat))

  def write_to(self, path):
    data = self.writer.getvalue()
    dirname = os.path.dirname(path)
    if len(dirname):
      os.makedirs(dirname, exist_ok=True)
    with open(path, "w") as fd:
      fd.write(data)
    print(path)

class VariablesConverter(BaseConverter):
  def __init__(self, schema, variables, parent):
    super(VariablesConverter, self).__init__(schema)
    self.variables = variables
    self.parent = parent

  @property
  def path(self):
    return os.path.join(self.parent.pathPrefix, "variables.jsonnet")

  def convert(self):
    if len(self.variables):
      self.writer.writeln("[")
      for variable in self.variables:
        self.writer.writeln("{")
        for (name, value) in variable.items():
          self.writer.writeln("{}: {},".format(name, json.dumps(value)))
        self.writer.writeln("},")
      self.writer.writeln("]")
      self.write_to(self.path)

class RuleConverter(BaseConverter):
  def __init__(self, schema, rule, parent=None):
    super(RuleConverter, self).__init__(schema)
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

  @property
  def path(self):
    """
    Path to this rules jsonnet file.
    """
    return (self.filename
      if self.parent is None
      else os.path.join(self.parent.pathPrefix, self.filename))

  @property
  def pathPrefix(self):
    """
    Path to the directory containing this rules children jsonnet files.
    """
    return (self.normalizedName
      if self.parent is None
      else os.path.join(self.parent.pathPrefix, self.normalizedName))

  def convert(self):
    self.write_papi_import_statement()

    self.writer.writeln('{} {{'.format(self.template))
    self.writer.writeln('name: {},'.format(json.dumps(self.ruleName)))

    if len(self.rule.get("comments", "")) > 0:
      self.writer.write('comments: ')
      self.writer.writeMultilineString(self.rule.get("comments", ""))
      self.writer.writeln(',')

    if "options" in self.rule:
      if len(self.rule.get("options")):
        self.writer.writeln("options: {")
        for (name, option) in self.rule.get("options").items():
          self.writer.writeln("{}: {},".format(name, json.dumps(option)))
        self.writer.writeln("},")

    if "variables" in self.rule:
      variablesConverter = VariablesConverter(self.schema, self.rule.get("variables"), self.parent)
      variablesConverter.convert()
      self.writer.writeln("variables: import {},".format(json.dumps(os.path.basename(variablesConverter.path))))

    self.convert_criteria()
    self.convert_behaviors()
    self.convert_children()

    if "customOverride" in self.rule:
      customOverride = self.rule.get("customOverride", {})
      if len(customOverride) > 0:
        self.writer.writeln("customOverride: {")
        for (k, v) in customOverride.items():
          self.writer.writeln("{k}: {v},".format(k, json.dumps(v)))
        self.writer.writeln("},")

    if "advancedOverride" in self.rule:
      xml = self.rule.get("advancedOverride")
      advancedOverridePath = os.path.join(os.path.dirname(self.path), "advancedOverride.xml")
      with open(advancedOverridePath, "w") as fd:
        print(advancedOverridePath)
        fd.write(xml)
      self.writer.writeln("advancedOverride: importstr {},".format(json.dumps(os.path.basename(advancedOverridePath))))

    self.writer.writeln('}')
    self.write_to(self.path)

  def convert_criteria(self):
    self.convert_criteria_or_behaviors("criteria")
    if len(self.rule.get("criteria", [])):
      criteriaMustSatisfy = self.rule.get("criteriaMustSatisfy", "all")
      if criteriaMustSatisfy != "all":
        self.writer.writeln("criteriaMustSatisfy: {},".format(json.dumps(criteriaMustSatisfy)))

  def convert_behaviors(self):
    self.convert_criteria_or_behaviors("behaviors")

  def convert_children(self):
    children = []
    for child in self.rule.get("children", []):
      children.append(RuleConverter(self.schema, child, self))
    if len(children):
      self.writer.writeln("children: [")
      for child in children:
        child.convert()
        relPath = os.path.join(self.normalizedName, child.filename)
        self.writer.writeln("import '{}',".format(relPath))
      self.writer.writeln("],")

  def convert_criteria_or_behaviors(self, ns):
    results = []
    for atom in self.rule.get(ns, []):
      converted = dict(name=atom.get("name"), options=dict())
      for (name, option) in atom.get("options", {}).items():
        converted["options"][name] = option
      results.append(converted)
    if len(results):
      self.writer.writeln("{}: [".format(ns))
      for atom in results:
        self.writer.write("papi.{}.{}".format(ns, atom.get("name")))
        if len(atom.get("options")):
          self.writer.write(" ")
          self.writer.write(json.dumps(atom.get("options"), indent="  "))
        self.writer.writeln(",")
      self.writer.writeln("],")

class PropertyConverter(BaseConverter):
  def __init__(self, schema, property):
    super(PropertyConverter, self).__init__(schema)
    self.property = property

  @property
  def normalizedName(self):
    return get_valid_filename(self.property.name)

  @property
  def filename(self):
    return "{}.jsonnet".format(self.normalizedName)

  @property
  def path(self):
    """
    Path to this propertie's jsonnet file.
    """
    return self.filename

  @property
  def pathPrefix(self):
    """
    Path to the directory containing this rules children jsonnet files.
    """
    return self.normalizedName

  def convert(self):
    self.write_papi_import_statement()
    self.writer.writeln('{')
    self.writer.writeln('productId: {},'.format(json.dumps(self.schema.product)))
    self.writer.writeln('ruleFormat: {},'.format(json.dumps(self.schema.ruleFormat)))
    defaultRule = RuleConverter(self.schema, self.property.data.get("rules"), self)
    defaultRule.convert()
    self.writer.writeln('rules: import {},'.format(json.dumps(defaultRule.path)))
    self.writer.writeln('}')
    self.write_to(self.path)
