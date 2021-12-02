# PAPI (Property Manager API)

This section discusses the use of the `akamai jsonnet papi` subcommand, which is dedicated to
managing Akamai CDN configurations (caching and routing) as Jsonnet.

## Commands

### akamai jsonnet papi bootstrap

> Use case: quickly create a multi-environment template from an existing configuration

Assuming an Ion configuration called `example_prod_pm` exists in the Akamai portal, the
following command will convert it to Jsonnet in a folder (`example_jsonnet`) ready to be checked into
version control.

```bash
akamai jsonnet papi bootstrap \
    --propertyName example_prod_pm \
    --propertyVersion latest \
    --productId SPM \
    --ruleFormat latest \
    --out example_jsonnet
```

> A reference of common `productId` values is available on the [PAPI Documentation](https://developer.akamai.com/api/core_features/property_manager/v1.html#productids).

The CLI creates a simple `render.sh` script that turns the Jsonnet back into valid PAPI JSON.

```bash
cd example_jsonnet
./render.sh
```

Creating more environments is as easy as creating new environment files e.g. `env/xyz.jsonnet` files and adjusting the values within
to specialise the output of the template.

The JSON generated by this process is meant to be compatible with the API. This means that you can 

#### Bootstrap for specific deployment tools

The `bootstrap` commands accepts two extra mutually exclusive flags to help get started with deploying configurations
using Terraform or Bossman.

##### `--terraform`

If provided, the CLI will create a terraform configuration template. Just like the rules template,
it will render to the output directory which will effectively become a terraform configuration directory.

After running `render.sh` you should end up with:

```
.
├── dist
│   └── example.com
│       ├── hostnames.json
│       ├── rules.json
│       ├── terraform.tf.json
│       ├── terraform.tfstate
│       └── terraform.tfstate.backup
├── envs
│   └── example.com.jsonnet
├── render.sh
├── template
│   ├── pmvariables.jsonnet
(...)
```

To run terraform at this point, you'll need to execute the commands output by the CLI, essentially:

```
cd dist/example.com
terraform init
terraform import akamai_property.example.com prp_XYZ # the property ID is output by the bootstrap command
terraform plan
```

Note that the CLI makes two assumptions that may or may not work for you:

* Jsonnet generates the Terraform configuration, as opposed to Terraform calling Jsonnet

This is the approach chosen here because Jsonnet is better suited for structuring very large or very complex
Akamai property configurations. Using Terraform simply as a deployment tool makes a lot of sense in that regard.

It is entirely possible to instead author the Terraform configuration in HCL and use a Jsonnet provider
(such as [alxrem/jsonnet](https://registry.terraform.io/providers/alxrem/jsonnet/latest/docs)) to stitch the
property template together from Terraform.

* Each Akamai property configuration gets its own Terraform configuration and state 

If you wish to activate environments separately (promotional deployment), this is a sensible approach. CI can easily run
`terraform` from the appropriate folders as dictated by your workflow, and it avoids the use of
[Terraform Workspaces](https://www.terraform.io/docs/language/state/workspaces.html) which are not supported by all
terraform storage backends.

If your use case is to manage all configurations at the same time, the template can be easily adjusted.

##### `--bossman`

If provided, the CLI will create a simple [Bossman](https://github.com/ynohat/bossman) configuration.

##### CP Codes (and other property dependencies)

Creating new configurations often entails creating new CP Codes as well. With Terraform the usual approach is
to do something like this:

```
resource "akamai_cp_code" "default" {
  ...
}

resource "akamai_property" "default" {
  ...
  rules = templatefile("./rules.json", {
    cpcode = parseint(replace(akamai_cp_code.default.id, "cpc_", ""), 10)
  })
}
```

The CLI currently doesn't detect the presence of all the CP Codes to extract them into the configuration and reinject them
back, but it is possible to do so quite easily:

* In the property template, define the CP Code ID like so:

```
      papi.behaviors.cpCode {
        value: {
          id: '${default_cpcode}',
        },
      },
```

* In the Terraform config template, provision an `akamai_cp_code` and inject its id into the ruletree:

```
  resource: {
    akamai_cp_code: {
      default: {
        contract_id: env.contractId,
        group_id: env.groupId,
        product_id: env.productId,
        name: env.name,
      }
    },
    akamai_property: {
      default: {
        ...
        rules: '${templatefile("./rules.json", {default_cpcode = parseint(replace(akamai_cp_code.default.id, "cpc_", ""), 10)})}'
      }
    }
  }
```

### akamai jsonnet papi ruleformat

> Use case: download a new version of the libsonnet when upgrading rule formats

In the example above, you may have noticed the following line:

```
local papi = import 'papi/SPM/v2021-07-30.libsonnet';
```

This command will generate the contents of that file to its standard output:

```bash
akamai jsonnet papi ruleformat \
  --productId SPM \
  --ruleFormat v2021-07-30
```

### akamai jsonnet papi ruletree

> Use case: download a rule tree as jsonnet, without the ruleformat or hostnames

```
akamai jsonnet papi ruletree \ 
    --propertyName example_prod_pm \
    --propertyVersion latest \
    --productId SPM \
    --ruleFormat v2021-07-30 \
    --out example_jsonnet_ruletree
```

The command will create `example_prod_pm/` in the current directory, containing the rule tree:

```bash
$ tree
.
└── example_prod_pm
  ├── rules
  │   ├── Offload
  │   │   ├── CSS_and_Javascript.jsonnet
  │   │   ├── Static_objects.jsonnet
  │   │   └── Uncacheable_Responses.jsonnet
  │   ├── Offload.jsonnet
  │   ├── Performance
  │   │   ├── Compressible_Objects.jsonnet
  │   │   └── JPEG_Images.jsonnet
  │   └── Performance.jsonnet
  ├── rules.jsonnet
  └── variables.jsonnet
```

### akamai jsonnet papi hostnames

> Use case: download a property's hostname mapping as jsonnet, without the ruleformat or ruletree

```bash
akamai jsonnet papi hostnames --propertyName example_prod_pm --propertyVersion 2
```

Output:

```
[
  {
    cnameType: 'EDGE_HOSTNAME',
    cnameFrom: 'www.example.com',
    cnameTo: 'www.example.com.edgesuite.net',
  },
]
```

Note: only the `cnameType`, `cnameFrom` and `cnameTo` fields are output by the command. The
API outputs more fields, but it is not clear that they are required and have caused problems.