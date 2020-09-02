import json
from jsonpointer import resolve_pointer
from ..writer import JsonnetWriter

class SchemaConverter:
  def __init__(self, schema):
    self.schema = schema
    self.writer = JsonnetWriter()

  def convert(self):
    self.writer.writeln("{")
    self.writer.writeln("behaviors: {")
    self.convert_behaviors()
    self.writer.writeln("},")
    self.writer.writeln("criteria: {")
    self.convert_criteria()
    self.writer.writeln("},")
    self.writer.writeln("}")

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
      """
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

    self.writer.writeln()
    for option in options:
      if "default" in option:
        # if a default value is specified in the schema, only
        # output it (commented) for reference
        self.writer.writeln("// {name}:: {default},".format(
          name=option.get("name"),
          default=json.dumps(option.get("default"))
        ))
      else:
        self.writer.writeln("{name}:: error 'required: {name}'")
    self.writer.writeln()

    self.writer.writeln("options: {")
    self.writer.write(
      """
      [name]: _[name]
      for name in {optionNames}
      if std.objectHas(_, name)
      """.format(optionNames=json.dumps(optionNames)).strip()
    )
    self.writer.writeln("}")

    self.writer.writeln("},")

  def get_atom_options(self, atom):
    options = atom.get("properties").get("options").get("properties")
    return map(lambda item: self.get_atom_option(atom, *item), options.items())

  def get_atom_option(self, atom, name, option):
    if "$ref" in option:
      option.update(self.resolve_pointer(option.get("$ref")))
    return {
      "name": name,
      "default": option.get("default", None)
    }

  def resolve_pointer(self, ptr):
    return resolve_pointer(self.schema, ptr.lstrip("#"))



