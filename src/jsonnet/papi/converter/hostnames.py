import json
from .base import BaseConverter

class HostnamesConverter(BaseConverter):
  def __init__(self, hostnames):
    super(HostnamesConverter, self).__init__()
    self.hostnames = hostnames

  def convert(self, writer):
    writer.writeln('[')
    for mapping in self.hostnames:
      writer.writeln('{')
      for k in ('cnameType', 'cnameFrom', 'cnameTo'):
        if k in mapping:
          writer.writeln('{}: {},'.format(k, json.dumps(mapping.get(k))))
      writer.writeln('},')
    writer.writeln(']')
