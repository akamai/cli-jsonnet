import os, os.path
import json
from .jsonnet.writer import JsonnetWriter
from .utils import pushd
from .edgegrid import Session
from .logging import logger
from .jsonnet.papi.ruleformat import RuleFormat
from .jsonnet.papi.property import Property
from .jsonnet.papi.converter import RuleTreeConverter, RuleFormatConverter, HostnamesConverter

def products(edgerc, section, contractId, accountSwitchKey=None, **kwargs):
  session = Session(edgerc, section, accountSwitchKey)
  response = session.get("/papi/v1/products", params={"contractId": contractId})
  products = response.json().get("products").get("items")
  print("\n".join(map(lambda p: "{productName}: {productId}".format(**p), products)))

def ruleformat(edgerc, section, productId, ruleFormat="latest", accountSwitchKey=None, **kwargs):
  ruleFormat = RuleFormat.get(edgerc, section, productId, ruleFormat, accountSwitchKey)
  writer = JsonnetWriter()
  converter = RuleFormatConverter(ruleFormat)
  converter.convert(writer)
  print(writer.getvalue())

def ruletree(edgerc, section, productId, propertyName, propertyVersion="latest", file=None, out=None, ruleFormat="latest", accountSwitchKey=None, **kwargs):
  ruleFormat = RuleFormat.get(edgerc, section, productId, ruleFormat, accountSwitchKey)
  property = None
  if file is None:
    property = Property.get(edgerc, section, propertyName, propertyVersion, ruleFormat, accountSwitchKey)
  else:
    with open(file, "r") as fd:
      data = json.loads(fd.read())
      property = Property(propertyName, data)

  out = '%s/rules.jsonnet' % (propertyName if out is None else out)
  with pushd(os.path.dirname(os.path.realpath(out))):
    ruleTreeWriter = JsonnetWriter()
    ruleTreeConverter = RuleTreeConverter(ruleFormat, property.ruleTree)
    ruleTreeConverter.convert(ruleTreeWriter)
    ruleTreeWriter.dump(os.path.basename(out))

def hostnames(edgerc, section, propertyName, propertyVersion="latest", accountSwitchKey=None, **kwargs):
  hostnames = Property.getHostnames(edgerc, section, propertyName, propertyVersion, accountSwitchKey)
  hostnamesWriter = JsonnetWriter()
  hostnamesConverter = HostnamesConverter(hostnames)
  hostnamesConverter.convert(hostnamesWriter)
  print(hostnamesWriter.getvalue())

def bootstrap(edgerc, section, productId, propertyName, propertyVersion="latest", ruleFormat="latest", out=None, accountSwitchKey=None, bossman=False, **kwargs):
  out = os.path.realpath(out if not out is None else propertyName)
  with pushd(out):
    ruleFormat = RuleFormat.get(edgerc, section, productId, ruleFormat, accountSwitchKey)
    with pushd('lib/papi/{}'.format(ruleFormat.product)):
      ruleFormatWriter = JsonnetWriter()
      ruleFormatConverter = RuleFormatConverter(ruleFormat)
      ruleFormatConverter.convert(ruleFormatWriter)
      ruleFormatWriter.dump('{}.libsonnet'.format(ruleFormat.ruleFormat))

    property = Property.get(edgerc, section, propertyName, propertyVersion, ruleFormat, accountSwitchKey)
    with pushd('template'):
      ruleTreeWriter = JsonnetWriter()
      ruleTreeConverter = RuleTreeConverter(ruleFormat, property.ruleTree)
      ruleTreeConverter.convert(ruleTreeWriter)
      ruleTreeWriter.dump('rules.jsonnet')

    with pushd('envs'):
      envWriter = JsonnetWriter()
      envWriter.writeln('{')
      envWriter.write('name: {},'.format(json.dumps(propertyName)))
      envWriter.write('hostnames: ')
      hostnamesConverter = HostnamesConverter(property.hostnames)
      hostnamesConverter.convert(envWriter)
      envWriter.writeln(',')
      envWriter.writeln('}')
      envWriter.dump('{}.jsonnet'.format(propertyName))

    templateWriter = JsonnetWriter()
    templateWriter.writeln('local env = std.extVar("env");')
    templateWriter.writeln('')
    templateWriter.writeln('{')
    templateWriter.writeln('["%s/rules.json" % env.name]: import "template/rules.jsonnet",')
    templateWriter.writeln('["%s/hostnames.json" % env.name]: env.hostnames,')
    templateWriter.writeln('}')
    templateWriter.dump('template.jsonnet')

    with open('./render.sh', 'w') as renderFd:
      print(
        '#!/bin/sh\n'
        '\n'
        'echo ">" cd $(dirname $(realpath $0))\n'
        'cd $(dirname $(realpath $0))\n'
        'ls envs/*.jsonnet |\n'
        '  while IFS=/ read _ envFile; do\n'
        '    envName=$(basename $envFile .jsonnet)\n'
        '    echo "> Rendering $envName..."\n'
        '    jsonnet -cm ./dist -J ./lib \\\n'
        '      --ext-code-file env=./envs/${envFile} \\\n'
        '      ./template.jsonnet\n'
        '    echo\n'
        '  done\n',
        file=renderFd
      )
      os.chmod(renderFd.name, mode=0o750)
      print('*** You may now render your template using:')
      print('    {out}/render.sh'.format(out=out))

    if bossman:
      with open('./.bossman', 'w') as bossmanRcFd:
        print(
          (
            'resources:\n'
            '#   https://bossman.readthedocs.io/en/latest/plugins/akamai/property.html#resource-configuration\n'
            '  - module: bossman.plugins.akamai.property\n'
            '    pattern: dist/{{name}}\n'
            '#   options:\n'
            '#     edgerc: {edgerc}\n'
            '#     section: {section}\n'
            '#     env_prefix: ""\n'
            '#     switch_key: {accountSwitchKey}\n'
          ).format(
            edgerc=edgerc if edgerc else "~/.edgerc",
            section=section if section else "papi",
            accountSwitchKey=accountSwitchKey if accountSwitchKey else "xyz"
          ),
          file=bossmanRcFd
        )
        os.chmod(bossmanRcFd.name, mode=0o640)
      print('*** Check that {out}/.bossman contents are correct'.format(out=out))
