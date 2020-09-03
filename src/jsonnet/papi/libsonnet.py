import json
from jsonpointer import resolve_pointer
from ..writer import JsonnetWriter

class SchemaConverter:
  def __init__(self, schema, product, ruleFormat):
    self.schema = schema
    self.product = product
    self.ruleFormat = ruleFormat
    self.writer = JsonnetWriter()

  def convert(self):
    self.write_locals()
    self.writer.writeln("{")
    self.write_meta_fields()
    self.write_rule()
    self.write_default_rule()
    self.writer.writeln("behavior: {")
    self.convert_behaviors()
    self.writer.writeln("},")
    self.writer.writeln("criteria: {")
    self.convert_criteria()
    self.writer.writeln("},")
    self.writer.writeln("}")

  def write_locals(self):
    pass

  def write_meta_fields(self):
    self.writer.writeln("productId:: {product},".format(product=json.dumps(self.product)))
    self.writer.writeln("ruleFormat:: {ruleFormat},".format(ruleFormat=json.dumps(self.ruleFormat)))

  def write_rule(self):
    self.writer.write(
      """
      rule: {
        name: error "<name> is required",
        comments: error "<comments> is required",

        behaviors: [],
        children: [],
        criteria: [],
        criteriaMustSatisfy: "all",
      },
      """.strip()
    )

  def write_default_rule(self):
    self.writer.write(
      """
      root: {
        local _ = self,
        is_secure:: error "is_secure is required",
        // The name of the default rule MUST BE "default", otherwise
        // PAPI throws occassional random errors.
        name: "default",
        assert self.name == "default",
        comments: |||
          The behaviors in the Default Rule apply to all requests for the property hostname(s) unless
          another rule overrides the Default Rule settings.
        |||,
        behaviors: [],
        children: [],
        options: {
          is_secure: _.is_secure,
        },
        variables: [
        ]
      },
      """.strip()
    )

  def convert_behaviors(self):
    behaviors = self.resolve_pointer("/definitions/catalog/behaviors")
    self.convert_atoms(behaviors.items())

  def convert_criteria(self):
    criteria = self.resolve_pointer("/definitions/catalog/criteria")
    self.convert_atoms(criteria.items())

  def convert_atoms(self, atoms):
    for (name, atom) in atoms:
      self.convert_atom(name, atom)

  def convert_atom(self, name, atom):
    options = self.get_atom_options(atom)
    optionNames = [option.get("name") for option in options]

    self.writer.writeln("{name}: {{".format(name=name))
    self.writer.writeln("local _ = self,")
    self.writer.writeln("name: {name},".format(name=json.dumps(name)))

    self.writer.writeln()
    for option in options:
      self.writer.writeln("{name}:: {default},".format(
        name=option.get("name"),
        default=json.dumps(option.get("default"))
      ))
    self.writer.writeln()

    self.writer.writeln("options: {")
    self.writer.write(
      """
      [name]: _[name]
      for name in {optionNames}
      if std.objectHasAll(_, name) && _[name] != null
      """.format(optionNames=json.dumps(optionNames)).strip()
    )
    self.writer.writeln("},")

    # TODO: more validation
    # validNames = list(atom.get("properties").keys()) + optionNames
    # self.writer.write("assert std.length(std.setDiff(std.objectFieldsAll(_), {validNames})) == 0".format(validNames=json.dumps(validNames)))
    # self.writer.writeln(": 'unexpected fields {}',")

    self.writer.writeln("},")

  def get_atom_options(self, atom):
    options = atom.get("properties").get("options").get("properties")
    return list(map(lambda item: self.get_atom_option(atom, *item), options.items()))

  def get_atom_option(self, atom, name, option):
    if "$ref" in option:
      option.update(self.resolve_pointer(option.get("$ref")))
    return {
      "name": name,
      "default": option.get("default", None)
    }

  def resolve_pointer(self, ptr):
    return resolve_pointer(self.schema, ptr.lstrip("#"))



