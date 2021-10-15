from .utils import pushd
import re, os.path

# def resolveIncludes(json):
#   if type(json) == dict:
#     return dict((k, resolveIncludes(v)) for k, v in json.items())
#   if type(json) == list:
#     return list(resolveIncludes(v) for v in json)
#   if type(json) == str:
#     if json.startswith("#include:"):
#       _, name = json.split(':', maxsplit=)