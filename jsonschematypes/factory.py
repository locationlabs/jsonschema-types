"""
Factory for schema-based types.
"""
import sys

from inflection import camelize, underscore
from jsonschema.compat import urlsplit

from jsonschematypes.model import Attribute, SchemaAware


if sys.version > '3':
    long = int

BASES = {
    "array": list,
    "boolean": bool,
    "integer": long,
    "number": float,
    "object": dict,
    "string": str,
}


class TypeFactory(object):
    """
    Factory that knows how to make new model classes for schemas.

    `TypeFactory` also implements module loader/finder abstractions
    for fancy imports.

    """
    def __init__(self, registry):
        self.registry = registry

    def class_name_for(self, schema_id):
        """
        Choose a class name for a given schema id.
        """
        path = urlsplit(schema_id).path
        last = path.split("/")[-1].split(".", 1)[0]
        return str(camelize(last))

    def attribute_name_for(self, property_name):
        """
        Choose an attribute name for a property name.
        """
        return str(underscore(property_name))

    def make_class(self, schema_id, bases=()):
        """
        Create a Python class that maps to the given schema.

        :param bases: a tuple of bases; should be compatible with `SchemaDict`
        """
        DEFAULT = u"default"
        DESCRIPTION = u"description"
        PROPERTIES = u"properties"
        REQUIRED = u"required"
        TYPE = u"type"

        schema = self.registry[schema_id]

        base = BASES.get(schema.get(TYPE), dict)
        bases = (SchemaAware, base) + bases

        class_name = self.class_name_for(schema_id)

        # save schema id and registry instance within the class definition
        attributes = dict(
            _ID=schema_id,
            _REGISTRY=self.registry,
        )

        if DESCRIPTION in schema:
            attributes["__doc__"] = schema[DESCRIPTION]

        # inject attributes for each property
        attributes.update({
            self.attribute_name_for(property_name): Attribute(
                property_name,
                description=property_.get(DESCRIPTION),
                required=property_name in schema.get(REQUIRED, []),
                default=property_.get(DEFAULT),
            )
            for property_name, property_ in schema.get(PROPERTIES, {}).items()
        })

        return type(class_name, bases, attributes)
