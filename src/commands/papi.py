import os, os.path
import json
from ..jsonnet.writer import JsonnetWriter
from ..utils import pushd
from ..edgegrid import Session
from ..logging import logger
from ..jsonnet.papi.ruleformat import RuleFormat
from ..jsonnet.papi.property import Property
from ..jsonnet.papi.converter import RuleTreeConverter, RuleFormatConverter, HostnamesConverter
import textwrap

def products(edgerc, section, contractId, accountkey=None, **kwargs):
  session = Session(edgerc, section, accountkey)
  response = session.get("/papi/v1/products", params={"contractId": contractId})
  products = response.json().get("products").get("items")
  print("\n".join(map(lambda p: "{productName}: {productId}".format(**p), products)))

def ruleformat(edgerc, section, productId, ruleFormat="latest", accountkey=None, **kwargs):
  ruleFormat = RuleFormat.get(edgerc, section, productId, ruleFormat, accountkey)
  writer = JsonnetWriter()
  converter = RuleFormatConverter(ruleFormat)
  converter.convert(writer)
  print(writer.getvalue())

def ruletree(edgerc, section, productId, propertyName, propertyVersion="latest", file=None, out=None, ruleFormat="latest", accountkey=None, **kwargs):
  ruleFormat = RuleFormat.get(edgerc, section, productId, ruleFormat, accountkey)
  property = None
  if file is None:
    property = Property.get(edgerc, section, propertyName, propertyVersion, ruleFormat, accountkey)
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

def hostnames(edgerc, section, propertyName, propertyVersion="latest", accountkey=None, **kwargs):
  hostnames = Property.getHostnames(edgerc, section, propertyName, propertyVersion, accountkey)
  hostnamesWriter = JsonnetWriter()
  hostnamesConverter = HostnamesConverter(hostnames)
  hostnamesConverter.convert(hostnamesWriter)
  print(hostnamesWriter.getvalue())

def bootstrap(edgerc, section, productId, propertyName, propertyVersion="latest", ruleFormat="latest", out=None, accountkey=None, bossman=False, terraform=False, **kwargs):
  out = os.path.realpath(out if not out is None else propertyName)
  with pushd(out):
    with open('.gitignore', 'w') as gitignore:
      if bossman:
        gitignore.write(textwrap.dedent(
          """
          .bossmancache
          """
        ))
      if terraform:
        from ..utils import GITIGNORE_TERRAFORM
        gitignore.write(textwrap.dedent(GITIGNORE_TERRAFORM))

    ruleFormat = RuleFormat.get(edgerc, section, productId, ruleFormat, accountkey)
    with pushd('lib/papi/{}'.format(ruleFormat.product)):
      ruleFormatWriter = JsonnetWriter()
      ruleFormatConverter = RuleFormatConverter(ruleFormat)
      ruleFormatConverter.convert(ruleFormatWriter)
      ruleFormatWriter.dump('{}.libsonnet'.format(ruleFormat.ruleFormat))

    property = Property.get(edgerc, section, propertyName, propertyVersion, ruleFormat, accountkey)
    edgeHostnames = get_edgehostnames(edgerc, section, property.contractId, property.groupId)
    with pushd('template'):
      ruleTreeWriter = JsonnetWriter()
      ruleTreeConverter = RuleTreeConverter(ruleFormat, property.ruleTree)
      ruleTreeConverter.convert(ruleTreeWriter)
      ruleTreeWriter.dump('rules.jsonnet')

      if terraform:
        terraformWriter = JsonnetWriter()
        terraformWriter.write(
          f"""
          local env = std.extVar('env');
          local rules = import './rules.jsonnet';

          {{
            terraform: {{
              required_version: '>= 1.0.0',
              required_providers: {{
                akamai: {{
                  source: 'akamai/akamai',
                  version: '1.8.0',
                }},
              }},
            }},

            provider: {{
              akamai: {{
                edgerc: '{edgerc}',
                config_section: '{section}',
              }}
            }},

            resource: {{
              akamai_edge_hostname: {{
                [hostname.resourceId]: {{
                  edge_hostname: hostname.cnameTo,
                  ip_behavior: hostname.ipBehavior,
                  product_id: rules.productId,
                  contract_id: rules.contractId,
                  group_id: rules.groupId,
                  certificate: hostname.certificate,
                }}
                for hostname in std.mapWithIndex(function (idx, hostname) hostname + {{resourceId: 'ehn_%d' % idx}}, env.hostnames)
              }},

              akamai_property: {{
                [env.name]: {{
                  name: env.name,
                  product_id: rules.productId,
                  rule_format: rules.ruleFormat,
                  contract_id: rules.contractId,
                  group_id: rules.groupId,
                  hostnames: std.map(function (hostname) {{
                      cname_from: hostname.cnameFrom,
                      cname_to: hostname.cnameTo,
                      cert_provisioning_type: 'CPS_MANAGED',
                    }}, env.hostnames),
                  rules: '${{templatefile("./rules.json", {{}})}}',
                }}
              }},

              akamai_property_activation: {{
                [env.name + '-staging']: {{
                  property_id: '${{akamai_property.%s.id}}' % env.name,
                  version: '${{akamai_property.%s.latest_version}}' % env.name,
                  network: 'STAGING',
                  contact: env.contact,
                }},

              // Uncomment the following lines to let Terraform activate also on the
              // Akamai production network.
              // The strategy here is that the production network is pinned to a specific
              // version defined in the Jsonnet environment file. This is a good strategy
              // if you have few configurations, but it does require a new commit (to bless)
              // a different version of the config.
              // With many environments, it is likely better to always activate the latest version
              // on the production network, but apply first on test envs (Essentially ignore
              // the existence of the staging network).

              //  [env.name + '-production']: {{
              //    property_id: '${{akamai_property.%s.id}}' % env.name,
              //    version: env.productionVersion,
              //    network: 'PRODUCTION',
              //    contact: env.contact,
              //  }},
              }},
            }}
          }}
          """
        )
        terraformWriter.dump('terraform.tf.jsonnet')

    with pushd('envs'):
      envWriter = JsonnetWriter()
      envWriter.writeln('{')
      envWriter.writeln('name: {},'.format(json.dumps(property.name)))
      if terraform:
        envWriter.writeln('// The terraform template will reference these variables')
        envWriter.writeln('// - to determine which version should be active in production.')
        envWriter.writeln('productionVersion: error "productionVersion should be an integer",')

        envWriter.writeln('// - to determine the email addresses to send notifications to.')
        envWriter.writeln('contact: error "contact should be an array of email addresses",')

      envWriter.write('hostnames: ')
      hostnamesConverter = HostnamesConverter(property.hostnames)
      hostnamesConverter.convert(envWriter, terraform, edgeHostnames)
      envWriter.writeln(',')
      envWriter.writeln('}')
      envWriter.dump('{}.jsonnet'.format(property.name))

    templateWriter = JsonnetWriter()
    templateWriter.writeln('local env = std.extVar("env");')
    templateWriter.writeln('')
    templateWriter.writeln('{')
    templateWriter.writeln('["%s/rules.json" % env.name]: import "template/rules.jsonnet",')
    if not terraform:
      # if we're generating for terraform, the hostnames are embedded in the terraform config file
      templateWriter.writeln('["%s/hostnames.json" % env.name]: env.hostnames,')
    if terraform:
      templateWriter.writeln('["%s/terraform.tf.json" % env.name]: import "template/terraform.tf.jsonnet",')
    templateWriter.writeln('}')
    templateWriter.dump('template.jsonnet')

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
            '#     switch_key: {accountkey}\n'
          ).format(
            edgerc=edgerc if edgerc else "~/.edgerc",
            section=section if section else "papi",
            accountkey=accountkey if accountkey else "xyz"
          ),
          file=bossmanRcFd
        )
        os.chmod(bossmanRcFd.name, mode=0o640)

    with open('./render.sh', 'w') as renderFd:
      print(
        '#!/bin/sh\n'
        '\n'
        'echo ">" cd $(dirname $0)\n'
        'cd $(dirname $0)\n'
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

      if terraform:
        print(f'### Some required parameters must be set in {out}/envs/{property.name}.jsonnet')
      print('### You may now render your template using:')
      print('    {out}/render.sh'.format(out=out))
      if terraform:
        print('### You will then be able to run terraform from the dist dir')
        print(f'    cd {out}/dist/{property.name}')
        print(f'    terraform init')
        print(f'    terraform import akamai_property.{property.name} {property.id}')
        for idx, hostname in enumerate(property.hostnames):
          if hostname.get('cnameTo') in edgeHostnames:
            ehnId = edgeHostnames.get(hostname.get('cnameTo')).get('edgeHostnameId')
            print(f'    terraform import akamai_edge_hostname.ehn_{idx} {ehnId},{property.contractId},{property.groupId}')
        print(f'    terraform apply')
      if bossman:
        print('### Then run the following commands to get started with Bossman'.format(out=out))
        print('    cd {out}'.format(out=out))
        print('    $EDITOR .bossman # Check that contents are correct'.format(out=out))
        print('    git init && git add . && git commit -m "init"')
        print('    bossman init')
        print('    bossman status')

def get_edgehostnames(edgerc, section, contractId, groupId, accountkey=None, **kwargs):
  session = Session(edgerc, section, accountkey)
  response = session.get("/papi/v1/edgehostnames", params={
    "contractId": contractId,
    "groupId": groupId,
  })
  edgeHostnames = response.json().get("edgeHostnames").get("items")
  return dict((ehn.get('edgeHostnameDomain'), ehn) for ehn in edgeHostnames)
