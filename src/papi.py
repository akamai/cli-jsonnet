import json
from .edgegrid import Session
from .logging import logger
from .jsonnet.papi.schema import Schema, SchemaConverter
from .jsonnet.papi.property import Property, PropertyConverter

def products(edgerc, section, contractId, **kwargs):
  session = Session(edgerc, section)
  response = session.get("/papi/v1/products", params={"contractId": contractId})
  products = response.json().get("products").get("items")
  print("\n".join(map(lambda p: "{productName}: {productId}".format(**p), products)))

def schema(edgerc, section, productId, ruleFormat="latest", **kwargs):
  schema = Schema.get(edgerc, section, productId, ruleFormat)
  converter = SchemaConverter(schema)
  converter.convert()
  print(converter.writer.getvalue())

def property(edgerc, section, productId, propertyName, propertyVersion="latest", file=None, ruleFormat="latest", **kwargs):
  schema = Schema.get(edgerc, section, productId, ruleFormat)

  property = None
  if file is None:
    property = Property.get(edgerc, section, propertyName, propertyVersion)
  else:
    with open(file, "r") as fd:
      data = json.loads(fd.read())
      property = Property(propertyName, data)

  converter = PropertyConverter(schema, property)
  converter.convert()
