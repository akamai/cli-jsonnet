# Akamai CLI For Jsonnet Config Management

Managing Akamai configurations as code implies dealing with a lot of JSON.

Jsonnet is a superset of JSON that provides syntax for reducing boilerplate and increasing
modularity.

This CLI provides utilities to ease the use of Jsonnet with Akamai configuration JSON.

## Prerequisites

You will need Python 3.

The CLI will format the jsonnet it generates if you have the `jsonnetfmt` executable on your
PATH.

To render configurations using the output of this CLI, you will of course need `jsonnet`.

Lastly, you will also need an `.edgerc` file populated with Akamai OPEN API credentials.

## Install

```
akamai install akamai-contrib/cli-jsonnet.git
```

## Overview

Using this CLI, you can express your configuration using syntax that resembles the following:

```
local papi = import 'papi/SPM/v2021-07-30.libsonnet';

papi.rule {
  name: 'Offload',
  comments: |||
    Controls caching, which offloads traffic away from the origin. Most objects
    types are not cached. However, the child rules override this behavior for
    certain subsets of requests.
  |||,
  behaviors: [
    papi.behaviors.caching { behavior: 'NO_STORE' },
    papi.behaviors.cacheError { ttl: '10s' },
    papi.behaviors.downstreamCache,
    papi.behaviors.tieredDistribution,
  ],
  children: [
    import 'Offload/CSS_and_Javascript.jsonnet',
    import 'Offload/Static_objects.jsonnet',
    import 'Offload/Uncacheable_Responses.jsonnet',
  ],
}
```

## Commands

### akamai jsonnet papi bootstrap

> Use case: quickly setup an existing configuration as a multi-environment template

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

The CLI creates a simple `render.sh` script that turns the Jsonnet back into valid PAPI JSON.

```bash
cd example_jsonnet
./render.sh
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