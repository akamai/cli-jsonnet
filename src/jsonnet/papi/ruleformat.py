from jsonpointer import resolve_pointer
from ...edgegrid import Session

class RuleFormatError(RuntimeError):
  pass

class RuleFormat:
  @staticmethod
  def get(edgerc, section, product, ruleFormat="latest", accountSwitchKey=None):
    session = Session(edgerc, section, accountSwitchKey)
    url = "/papi/v1/schemas/products/{product}/{ruleFormat}".format(
      product=product,
      ruleFormat=ruleFormat
    )
    response = session.get(url)
    schema = response.json()
    return RuleFormat(schema, product, ruleFormat)

  def __init__(self, schema, product, ruleFormat):
    self.schema = schema
    self.product = product
    self.ruleFormat = ruleFormat

  def resolve_pointer(self, ptr):
    return resolve_pointer(self.schema, ptr.lstrip("#"))

  def get_defaults(self, atom):
    if atom.get("type", None) != "object":
      raise RuleFormatError("expecting object schema")
    defaults = {}
    for (name, prop) in atom.get("properties", {}).items():
      if "$ref" in prop:
        prop = self.resolve_pointer(prop.get("$ref"))
      defaults[name] = prop.get("default", None)
    return defaults
