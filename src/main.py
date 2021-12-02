import argparse
import os, sys, textwrap

def main():
  parser = argparse.ArgumentParser(prog="akamai-jsonnet", description="Akamai Jsonnet utilities.")
  init_defaults(parser)
  init_edgerc(parser)
  subparsers = parser.add_subparsers(title="Commands")
  init_papi(subparsers)
  args = parser.parse_args()

  args.func(args)
  # try:
  #   args.func(args)
  # except Exception as e:
  #   print(textwrap.indent("Error: " + str(e), prefix='!!! '), file=sys.stderr)
  #   sys.exit(1)

def init_defaults(parser):
  parser.set_defaults(func=lambda args: parser.print_help())

def init_edgerc(parser):
  env_edgerc = os.getenv("AKAMAI_EDGERC")
  default_edgerc = env_edgerc if env_edgerc else os.path.join(os.path.expanduser("~"), ".edgerc")
  parser.add_argument("--edgerc", help="Path to the edgerc file", default=default_edgerc)

  env_edgerc_section = os.getenv("AKAMAI_EDGERC_SECTION")
  default_edgerc_section = env_edgerc_section if env_edgerc_section else "default"
  parser.add_argument("--section", help="Edgerc section", default=default_edgerc_section)
  parser.add_argument("--accountkey", default=None, required=False, help="[Akamai Internal] account switch key")

def init_papi(parent):
  parser = parent.add_parser("papi", description="Akamai Jsonnet utilities for PAPI.")
  init_defaults(parser)
  subparsers = parser.add_subparsers(title="Commands")
  init_papi_products(subparsers)
  init_papi_bootstrap(subparsers)
  init_papi_ruleformat(subparsers)
  init_papi_ruletree(subparsers)
  init_papi_hostnames(subparsers)

def init_papi_products(parent):
  from .commands.papi import products

  parser = parent.add_parser("products", help="list available products")
  init_defaults(parser)
  parser.add_argument("--contractId", required=True)
  parser.set_defaults(func=lambda args: products(**vars(args)))

def init_papi_ruleformat(parent):
  from .commands.papi import ruleformat

  parser = parent.add_parser("ruleformat", help="create libsonnet file for the given product and rule format")
  init_defaults(parser)
  parser.add_argument("--productId", required=True)
  parser.add_argument("--ruleFormat", required=False, default="latest")
  parser.set_defaults(func=lambda args: ruleformat(**vars(args)))

def init_papi_ruletree(parent):
  from .commands.papi import ruletree

  parser = parent.add_parser("ruletree", help="create jsonnet template from an existing PAPI rule tree")
  init_defaults(parser)
  parser.add_argument("--productId", required=True)
  parser.add_argument("--ruleFormat", required=False, default="latest")
  parser.add_argument("--propertyName", required=True)
  parser.add_argument("--propertyVersion", required=False, default="latest")
  parser.add_argument("--file", required=False, help="file containing a json rule tree")
  parser.add_argument("--out", required=False, help="output directory for the template entrypoint; default to {propertyName}")
  parser.set_defaults(func=lambda args: ruletree(**vars(args)))

def init_papi_hostnames(parent):
  from .commands.papi import hostnames

  parser = parent.add_parser("hostnames", help="create jsonnet template from an existing PAPI hostnames mapping")
  init_defaults(parser)
  parser.add_argument("--propertyName", required=True)
  parser.add_argument("--propertyVersion", required=False, default="latest")
  parser.set_defaults(func=lambda args: hostnames(**vars(args)))

def init_papi_bootstrap(parent):
  from .commands.papi import bootstrap

  parser = parent.add_parser("bootstrap", help="bootstrap a property as a template in a multi-env setup")
  init_defaults(parser)
  parser.add_argument("--productId", required=True)
  parser.add_argument("--ruleFormat", required=False, default="latest")
  parser.add_argument("--propertyName", required=True)
  parser.add_argument("--propertyVersion", required=False, default="latest")
  parser.add_argument("--out", required=False, help="output directory for the template entrypoint; default to {propertyName}")
  parser.add_argument("--bossman", required=False, action='store_true', default=False, help="create .bossman configuration?")
  parser.set_defaults(func=lambda args: bootstrap(**vars(args)))
