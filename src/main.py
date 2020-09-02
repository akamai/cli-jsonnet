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

def init_papi(parent):
  parser = parent.add_parser("papi", description="Akamai Jsonnet utilities for PAPI.")
  init_defaults(parser)
  init_edgerc(parser)
  subparsers = parser.add_subparsers(title="Commands")
  init_papi_products(subparsers)
  init_papi_mklib(subparsers)

def init_papi_products(parent):
  from .papi import list_products

  parser = parent.add_parser("products", description="list available products")
  init_defaults(parser)
  parser.add_argument("--contractId", required=True)
  parser.set_defaults(func=lambda args: list_products(**vars(args)))

def init_papi_mklib(parent):
  from .papi import mklib

  parser = parent.add_parser("mklib", description="create libsonnet file for the given product and rule format")
  init_defaults(parser)
  parser.add_argument("--productId", required=True)
  parser.add_argument("--ruleFormat", required=False, default="latest")
  parser.set_defaults(func=lambda args: mklib(**vars(args)))
