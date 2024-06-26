import json
from .base import BaseConverter

class HostnamesConverter(BaseConverter):
  def __init__(self, hostnames):
    super(HostnamesConverter, self).__init__()
    self.hostnames = hostnames

  def convert(self, writer, terraform = False, edgeHostnames = {}):
    writer.writeln('[')
    for mapping in self.hostnames:
      writer.writeln('{')
      for k in ('cnameType', 'cnameFrom', 'cnameTo', 'certProvisioningType'):
        if k in mapping:
          writer.writeln('{}: {},'.format(k, json.dumps(mapping.get(k))))
      if terraform:
        cnameTo = mapping.get('cnameTo', None)
        if cnameTo in edgeHostnames:
          ip_behavior = edgeHostnames.get(mapping.get('cnameTo')).get('ipVersionBehavior')
          writer.writeln('ipBehavior: {},'.format(json.dumps(ip_behavior)))
        else:
          writer.writeln('// failed to determine ipBehavior, please fill in manually')
          writer.writeln("ipBehavior: error 'ipBehavior is required',")
        if cnameTo.endswith('edgekey.net'):
          writer.writeln("// edgekey.net Edge Hosnames require the certificate enrollment id")
          writer.writeln("// to be provided, which can be retrieved using the Akamai CPS CLI")
          writer.writeln("certificate: error 'certificate is required',")
      writer.writeln('},')
    writer.writeln(']')
