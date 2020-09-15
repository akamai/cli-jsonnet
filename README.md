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

Of course, you will also need an `.edgerc` file populated with Akamai OPEN API credentials.

## Install

```
akamai install https://github.com/ynohat/cli-jsonnet.git
```

## Managing Akamai Properties

Using this CLI, you can express your configuration using syntax that resembles the following:

```
local papi = import 'papi/SPM/v2020-03-04.libsonnet';

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

### Creating the `papi` library

In the example above, you may have noticed the following line:

```
local papi = import 'papi/SPM/v2020-03-04.libsonnet';
```

This can be easily generated using the following commands:

```bash
PRODUCT=SPM
RULE_FORMAT=v2020-03-04
mkdir -p jsonnet/lib/papi/${PRODUCT}
akamai jsonnet papi --section papi schema --productId ${PRODUCT} --ruleFormat ${RULE_FORMAT} > jsonnet/lib/papi/SPM/${RULE_FORMAT}.libsonnet
```

> SPM is the product id for Ion Premier. To see which products are available,
> this CLI provides the `akamai jsonnet papi products` command.

### Importing an existing property as jsonnet

This can very quickly be done as well:

```
PROPERTY_NAME=www.example.com
mkdir -p jsonnet/templates
cd jsonnet/templates
akamai jsonnet papi property --section papi --productId ${PRODUCT} --ruleFormat ${RULE_FORMAT} --propertyName ${PROPERTY_NAME}
cd -
```

The command will create `www.example.com.jsonnet` in the current directory, along with supporting files. The tree
might look like this:

```bash
$ tree
.
├── www.example.com
│   ├── rules
│   │   ├── Offload
│   │   │   ├── CSS_and_Javascript.jsonnet
│   │   │   ├── Static_objects.jsonnet
│   │   │   └── Uncacheable_Responses.jsonnet
│   │   ├── Offload.jsonnet
│   │   ├── Performance
│   │   │   ├── Compressible_Objects.jsonnet
│   │   │   └── JPEG_Images.jsonnet
│   │   └── Performance.jsonnet
│   ├── rules.jsonnet
│   └── variables.jsonnet
└── www.example.com.jsonnet

4 directories, 10 files
```

You can then render this as json using `jsonnet`:

```bash
jsonnet -J jsonnet/lib jsonnet/templates/www.example.com.jsonnet
```

## Troubleshooting

### PAPI

**Error: "The Race Results Hostname option in `SureRoute` must not be empty."**

When attempting to push a PAPI rule tree generated from jsonnet, you may encounter
this error (seen on ruleFormat v2020-03-04):

```json
{
  "type" : "https://problems.luna.akamaiapis.net/papi/v0/validation/option_empty",
  "errorLocation" : "#/rules/children/0/behaviors/4/options/customStatKey",
  "detail" : "The Race Results Hostname option in `SureRoute` must not be empty."
}
```

**Workaround**

When using `papi.behaviors.sureRoute`, set the `customStatKey` to `null` explicitly.
This is because the schema specifies a default value of `''` (the empty string), which
does not pass validation.

