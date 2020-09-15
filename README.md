This is a work in progress, please check back later!

# Akamai CLI For Jsonnet Config Management

Managing Akamai configurations as code implies dealing with a lot of JSON.

Jsonnet is a superset of JSON that provides syntax for reducing boilerplate and increasing
reusability.

This CLI provides utilities to ease the use of Jsonnet with Akamai configuration JSON.

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

