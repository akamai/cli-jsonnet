import argparse
import os

def main():
  parser = argparse.ArgumentParser(prog="akamai-jsonnet", description="Akamai Jsonnet utilities.")
  init_defaults(parser)
  init_edgerc(parser)
  subparsers = parser.add_subparsers(title="Commands")
  init_papi(subparsers)
  args = parser.parse_args()
  args.func(args)

def init_defaults(parser):
  parser.set_defaults(func=lambda args: parser.print_help())

def init_edgerc(parser):
  env_edgerc = os.getenv("AKAMAI_EDGERC")
  default_edgerc = env_edgerc if env_edgerc else os.path.join(os.path.expanduser("~"), ".edgerc")
  parser.add_argument("--edgerc", help="Path to the edgerc file", default=default_edgerc)

  env_edgerc_section = os.getenv("AKAMAI_EDGERC_SECTION")
  default_edgerc_section = env_edgerc_section if env_edgerc_section else "default"
  parser.add_argument("--section", help="Edgerc section", default=default_edgerc_section)
  parser.add_argument("--accountSwitchKey", default=None, required=False, help="[Akamai Internal] account switch key")

def init_papi(parent):
  parser = parent.add_parser("papi", description="Akamai Jsonnet utilities for PAPI.")
  init_defaults(parser)
  subparsers = parser.add_subparsers(title="Commands")
  init_papi_products(subparsers)
  init_papi_schema(subparsers)
  init_papi_property(subparsers)

def init_papi_products(parent):
  from .papi import products

  parser = parent.add_parser("products", help="list available products")
  init_defaults(parser)
  parser.add_argument("--contractId", required=True)
  parser.set_defaults(func=lambda args: products(**vars(args)))

def init_papi_schema(parent):
  from .papi import schema

  parser = parent.add_parser("schema", help="create libsonnet file for the given product and rule format")
  init_defaults(parser)
  parser.add_argument("--productId", required=True)
  parser.add_argument("--ruleFormat", required=False, default="latest")
  parser.set_defaults(func=lambda args: schema(**vars(args)))

def init_papi_property(parent):
  from .papi import property

  parser = parent.add_parser("property", help="create jsonnet template from an existing PAPI property")
  init_defaults(parser)
  parser.add_argument("--productId", required=True)
  parser.add_argument("--ruleFormat", required=False, default="latest")
  parser.add_argument("--propertyName", required=True)
  parser.add_argument("--propertyVersion", required=False, default="latest")
  parser.add_argument("--file", required=False, help="file containing a json rule tree")
  parser.set_defaults(func=lambda args: property(**vars(args)))
