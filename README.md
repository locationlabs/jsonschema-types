# jsonschema-types

[JSON Schema](http://json-schema.org/) type generator.

[![Build Status](https://travis-ci.org/locationlabs/jsonschema-types.png)](https://travis-ci.org/locationlabs/jsonschema-types)

## Why?

JSON Schema is a powerful tool for data validation, but is not a perfect fit
for generating language-specific bindings (e.g. classes) for the types represented
by its schemas.

`jsonschema-types` solves several problems that emerge from generating types from
schemas:

 1. Schemas use URIs to reference other schemas and commonly resolve these URIs
    *at runtime* over HTTP(S). In many production scenarios, it is preferable to
    resolve all schema references *in advance* and enforce that schemas correspond
    to a known version.

    `jsonschema-types` provides a `Registry` to store known schemas and ensures that
    schema URI resolution occurs locally. The `Registry` also supports bulk-loading
    of mulitple schemas (e.g. from a tar file).

 2. Schemas need to be translated into appropritate language bindings.

    `jsonschema-types` generates Python classes for schemas and, optionally, integrates
    with Python's import system for ease-of-use.


## How?

 1. Define your schema(s) in file(s) (or tar files):

        $ cat jsonschematypes/tests/data/address.json
        {
            "id": "http://x.y.z/bar/address",
            "properties": {
                "street": {
                    "type": "string"
                },
                "city": {
                    "type": "string"
                },
                "state": {
                    "type": "string"
                },
                "zip": {
                    "type": "string"
                },
                "country": {
                    "type": "string"
                }
            },
            "required": ["street", "city", "state"]
        }

 2. Load your schema(s) into a `Registry`:

        from jsonschematypes.registry import Registry

        registry = Registry()
        registry.load("jsonschematypes/tests/data/address.json")

 3. Generate types explicitly or via imports:

        if explicit:
            Address = registry.create_class("http://x.y.z/bar/address")
        else:
            registry.configure_imports(basename="generated")
            
            from generated.bar import Address

 4. Use the generated types to validate data and generate JSON:
 
        address = Address(
            street="1600 Pennsylvania Ave",
            city="Washington",
            state="DC",
        )
        address.validate()
        
        print address.dumps()


## Caveats

 -  Schemas **MUST** define an `id` and **SHOULD** define `properties` and `type`
 -  Support for `anyOf`, `oneOf`, and `allOf` is accidental at best.

## Related Work

The [Warlock](https://github.com/bcwaldon/warlock) and
[python-jsonschema-objects](https://github.com/cwacek/python-jsonschema-objects) also provide
type generation for JSON Schema. `jsonschema-types` makes a few decisions differently:

 -  Generated types do not validate themselves automatically; the `validate()` method must
    be called explicitly. There are many testing scenarios where it useful to be able to
    generate invalid data.

 -  Similar to `Warlock`, generated types are backed by a Python dictionary. Unlike `Warlock`,
    generated types use the [descriptor]( https://docs.python.org/2/howto/descriptor.html)
    protocol to map between attributes and dictionary keys and maps other naming conventions
    (e.g. "fooBar") to more Pythonic ones (e.g. "foo_bar").

    `jsonschema-types` also does not track changes to underlying objects (to generate
    patches), though this is an intriguing feature.

 -  `python-jsonschema-objects` also provides a mechanism for bypassing runtime URI resolution
    over HTTP(S), using a custom "memory" URI schema. `jsonschema-types` instead preserves HTTP
    URIs, but ensures that HTTP(S) results are cached in advance.
