import json
from .edgegrid import Session
from .logging import logger
from .jsonnet.papi.libsonnet import SchemaConverter

def list_products(edgerc, section, contractId, **kwargs):
  session = Session(edgerc, section)
  response = session.get("/papi/v1/products", params={"contractId": contractId})
  products = response.json().get("products").get("items")
  print("\n".join(map(lambda p: "{productName}: {productId}".format(**p), products)))

def mklib(edgerc, section, productId, ruleFormat="latest", **kwargs):
  schema = _get_schema(edgerc, section, productId, ruleFormat)
  converter = SchemaConverter(schema)
  converter.convert()
  print(converter.writer.getvalue())

def _get_schema(edgerc, section, productId, ruleFormat="latest"):
  session = Session(edgerc, section)
  url = "/papi/v1/schemas/products/{productId}/{ruleFormat}".format(productId=productId, ruleFormat=ruleFormat)
  response = session.get(url)
  schema = response.json()
  return schema
