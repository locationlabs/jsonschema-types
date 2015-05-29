"""
Factory for schema-based types.
"""
import sys

from inflection import camelize, underscore
from jsonschema.compat import urlsplit

from jsonschematypes.model import (
    Attribute,
    SchemaAwareDict,
    SchemaAwareList,
    SchemaAwareString,
    DEFAULT,
    DESCRIPTION,
    PROPERTIES,
    REQUIRED,
    TYPE,
)


if sys.version > '3':
    long = int


class TypeFactory(object):
    """
    Factory that knows how to make new model classes for schemas.

    `TypeFactory` also implements module loader/finder abstractions
    for fancy imports.
    """
    PRIMITIVE_BASES = {
        # There's hopefully no good reason to define a custom boolean type
        # (e.g. with enumerated values) because the only legal values are
        # True and False *AND* Python doesn't let you extend boolean.
        #
        # See: https://mail.python.org/pipermail/python-dev/2002-March/020822.html
        "boolean": bool,
        # There are arguments for custom long and float types, but YAGNI.
        "integer": long,
        "number": float,
    }
    SCHEMA_AWARE_BASES = {
        "array": SchemaAwareList,
        "object": SchemaAwareDict,
        "string": SchemaAwareString,
    }

    def __init__(self, registry):
        self.registry = registry
        self.classes = {}

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

    def make_class(self, schema_id, extra_bases=()):
        """
        Create a Python class that maps to the given schema.

        :param extra_bases: extra bases to add to generated types
        """
        if schema_id in self.classes:
            return self.classes[schema_id]

        schema = self.registry[schema_id]

        schema_type = schema.get(TYPE, "object")

        # skip type generation for primitives
        if schema_type in TypeFactory.PRIMITIVE_BASES:
            return TypeFactory.PRIMITIVE_BASES.get(schema_type)

        base = TypeFactory.SCHEMA_AWARE_BASES[schema_type]
        bases = (base, ) + extra_bases

        class_name = self.class_name_for(schema_id)

        # save backref and metadata within the class definition
        attributes = dict(
            _ID=schema_id,
            _REGISTRY=self.registry,
            _SCHEMA=schema,
        )

        # include class level doc string if available
        if DESCRIPTION in schema:
            attributes["__doc__"] = schema[DESCRIPTION]

        # inject attributes for each property
        if schema_type == "object":
            attributes.update({
                self.attribute_name_for(property_name): Attribute(
                    registry=self.registry,
                    key=property_name,
                    description=property_.get(DESCRIPTION),
                    required=property_name in schema.get(REQUIRED, []),
                    default=property_.get(DEFAULT),
                )
                for property_name, property_ in schema.get(PROPERTIES, {}).items()
            })

        # create the class
        cls = type(class_name, bases, attributes)
        self.classes[schema_id] = cls
        return cls
