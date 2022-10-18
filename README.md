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

> The [`go-jsonnet`](https://github.com/google/go-jsonnet) flavour of jsonnet is strongly recommended.

You will also need Akamai OPEN API credentials, please refer to the [Getting Started with APIs](https://developer.akamai.com/api/getting-started).

### Render jsonnet to json

The `papi bootstrap` command generates a `render.sh` script which requires a Unix-like shell and a
PowerShell script `render.ps1`. You may use one or the other depending on your environment.

You can also do without the render script, it should be fairly trivial and is only provided
for convenience.

## Install

```
akamai install jsonnet
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

## Subcommands

* [PAPI (Property Manager API)](./docs/papi.md)
