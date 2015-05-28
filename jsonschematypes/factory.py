"""
Factory for schema-based types.
"""
from imp import new_module
import re
import sys

from inflection import camelize, underscore
from jsonschema.compat import urlsplit

from jsonschematypes.model import Attribute, SchemaDict


class TypeFactory(object):
    """
    Factory that knows how to make new model classes for schemas.

    `TypeFactory` also implements module loader/finder abstractions
    for fancy imports.

    :param basename: package name prefix for module auto-loading
    :param keep_uri_parts: number of URI parts to keep when computing package names
    """
    def __init__(self, registry, basename="generated", keep_uri_parts=None):
        self.registry = registry
        self.basename = basename
        self.keep_uri_parts = keep_uri_parts

    def find_module(self, fullname, path=None):
        """
        Return a valid module loader for paths matching basename.
        """
        if fullname.split(".")[0] == self.basename:
            # only handle basename
            return self
        return None

    def load_module(self, fullname):
        """
        Load module matching full name.
        """
        matching_classes = {
            schema_id: self.make_class(schema_id)
            for schema_id in self.registry
            if self.package_name_for(schema_id).startswith(fullname)
        }
        if not matching_classes:
            # no classes have this module as a parent
            raise ImportError(fullname)

        module = self.make_module(fullname)

        for schema_id, matching_class in matching_classes.items():
            if self.package_name_for(schema_id) != fullname:
                # class belongs to a different module
                continue

            class_name = matching_class.__name__

            if not hasattr(module, class_name):
                setattr(module, class_name, matching_class)

        return module

    def is_legal_package_name(self, name):
        """
        Is name a legal Python package name?

        PEP8 says that "Python packages should also have short, all-lowercase names,
        although the use of underscores is discouraged."
        """
        return re.match(r"[a-z][a-z_]*", name)

    def package_name_for(self, schema_id):
        """
        Choose a package name for a given schema id.
        """
        path = urlsplit(schema_id).path
        uri_parts = path.split("/")
        if self.keep_uri_parts:
            uri_parts = uri_parts[-self.keep_uri_parts:]
        parts = [underscore(part) for part in uri_parts[:-1] if part]

        if not all(self.is_legal_package_name(part) for part in parts):
            raise ValueError("Unable to construct legal package name from: {}".format(path))

        return ".".join([self.basename] + parts)

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

    def make_class(self, schema_id, bases=(SchemaDict,)):
        """
        Create a Python class that maps to the given schema.

        :param bases: a tuple of bases; should be compatible with `SchemaDict`
        """
        DESCRIPTION = u"description"
        PROPERTIES = u"properties"
        REQUIRED = u"required"

        schema = self.registry[schema_id]

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
                required=property_name in schema.get(REQUIRED, [])
            )
            for property_name, property_ in schema.get(PROPERTIES, {}).items()
        })

        return type(class_name, bases, attributes)

    def make_module(self, fullname):
        """
        Create a new module.
        """
        if fullname in sys.modules:
            return sys.modules[fullname]

        module = new_module(fullname)
        module.__file__ = "<jsonschematypes>"
        module.__loader__ = self
        module.__package__ = fullname
        module.__path__ = []
        sys.modules[fullname] = module
        return module
