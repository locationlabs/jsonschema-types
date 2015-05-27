"""
Factory for schema-based types.
"""
from imp import new_module
import sys

from inflection import titleize, underscore
from jsonschema.compat import urlsplit

from jsonschematypes.model import Attribute, SchemaDict


class TypeFactory(object):
    """
    Factory that knows how to make new model classes for schemas.

    `TypeFactory` also implements module loader/finder abstractions
    for fancy imports.
    """
    def __init__(self, registry, basename="generated"):
        self.registry = registry
        self.basename = basename

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
            self.package_name_for(schema_id): self.make_class(schema_id)
            for schema_id in self.registry
            if self.package_name_for(schema_id).startswith(fullname)
        }

        if not matching_classes:
            # no classes have this module as a parent
            raise ImportError(fullname)

        module = self.make_module(fullname)

        for package_name, matching_class in matching_classes.items():
            if package_name != fullname:
                # class belongs to a different module
                continue

            class_name = matching_class.__name__
            if not hasattr(module, class_name):
                setattr(module, class_name, matching_class)

        return module

    def package_name_for(self, schema_id):
        """
        Choose a package name for a given schema id.
        """
        path = urlsplit(schema_id).path
        return ".".join(
            [self.basename] +
            [underscore(part) for part in path.split("/")[:-1] if part]
        )

    def class_name_for(self, schema_id):
        """
        Choose a class name for a given schema id.
        """
        path = urlsplit(schema_id).path
        return str(titleize(path.split("/")[-1]))

    def attribute_name_for(self, property_name):
        """
        Choose an attribute name for a property name.
        """
        return str(underscore(property_name))

    def make_class(self, schema_id):
        """
        Create a Python class that maps to the given schema.
        """
        schema = self.registry[schema_id]

        class_name = self.class_name_for(schema_id)
        bases = (SchemaDict,)

        # save schema id and registry instance within the class definition
        attributes = dict(
            _ID=schema_id,
            _REGISTRY=self.registry,
        )

        # inject attributes for each property
        attributes.update({
            self.attribute_name_for(property_name): Attribute(property_name)
            for property_name in schema.get("properties", {})
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
