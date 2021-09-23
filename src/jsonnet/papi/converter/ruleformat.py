import json
from .base import BaseConverter

class RuleFormatConverter(BaseConverter):
  def __init__(self, ruleFormat):
    super(RuleFormatConverter, self).__init__()
    self.ruleFormat = ruleFormat

  def convert(self, writer):
    self.convert_locals(writer)
    writer.writeln("{")
    self.convert_meta_fields(writer)
    self.convert_rule(writer)
    self.convert_default_rule(writer)
    writer.writeln("behaviors: {")
    self.convert_behaviors(writer)
    writer.writeln("},")
    writer.writeln("criteria: {")
    self.convert_criteria(writer)
    writer.writeln("},")
    writer.writeln("}")

  def convert_locals(self, writer):
    pass

  def convert_meta_fields(self, writer):
    writer.writeln("productId:: {product},".format(product=json.dumps(self.ruleFormat.product)))
    writer.writeln("ruleFormat:: {ruleFormat},".format(ruleFormat=json.dumps(self.ruleFormat.ruleFormat)))

  def convert_rule(self, writer):
    writer.write(
      """
      rule: {
        name: error "<name> is required",
        comments: "",
        //comments: error "<comments> is required",

        behaviors: [],
        children: [],
        criteria: [],
        criteriaMustSatisfy: "all",
        options: {},
      },
      """.strip()
    )

  def convert_default_rule(self, writer):
    writer.write(
      """
      root: {
        local _ = self,
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
          //is_secure: false,
        },
        variables: [
        ]
      },
      """.strip()
    )

  def convert_behaviors(self, writer):
    behaviors = self.ruleFormat.resolve_pointer("/definitions/catalog/behaviors")
    self.convert_atoms(writer, behaviors.items())

  def convert_criteria(self, writer):
    criteria = self.ruleFormat.resolve_pointer("/definitions/catalog/criteria")
    self.convert_atoms(writer, criteria.items())

  def convert_atoms(self, writer, atoms):
    for (name, atom) in atoms:
      self.convert_atom(writer, name, atom)

  def convert_atom(self, writer, name, atom):
    options = self.get_atom_options(atom)
    optionNames = [option.get("name") for option in options]

    writer.writeln("{name}: {{".format(name=name))
    writer.writeln("local _ = self,")
    writer.writeln("name: {name},".format(name=json.dumps(name)))

    writer.writeln()
    for option in options:
      writer.writeln("{name}:: {default},".format(
        name=option.get("name"),
        # setting implicit default values from the ruleFormat is a bad idea,
        # because they can be incompatible with each other.
        default="null",
      ))
    writer.writeln()

    writer.writeln("options: {")
    writer.write(
      """
      [name]: _[name]
      for name in {optionNames}
      if std.objectHasAll(_, name) && _[name] != null
      """.format(optionNames=json.dumps(optionNames)).strip()
    )
    writer.writeln("},")

    # TODO: more validation
    # validNames = list(atom.get("properties").keys()) + optionNames
    # writer.write("assert std.length(std.setDiff(std.objectFieldsAll(_), {validNames})) == 0".format(validNames=json.dumps(validNames)))
    # writer.writeln(": 'unexpected fields {}',")

    writer.writeln("},")

  def get_atom_options(self, atom):
    options = atom.get("properties").get("options").get("properties")
    return list(map(lambda item: self.get_atom_option(atom, *item), options.items()))

  def get_atom_option(self, atom, name, option):
    if "$ref" in option:
      option.update(self.ruleFormat.resolve_pointer(option.get("$ref")))
    return {
      "name": name,
      "default": option.get("default", None)
    }
