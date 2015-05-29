"""
Module finder and loader implementations.

Supports auto-generation of classes on import.
"""
from imp import new_module
import re
import sys

from inflection import underscore
from jsonschema.compat import urlsplit


class ModuleFinder(object):
    """
    A module "finder" that matches a configured basename.
    """
    def __init__(self, factory, basename, keep_uri_parts=None):
        """
        :param factory: the class generation factory
        :param basename: package name prefix for module auto-loading
        :param keep_uri_parts: number of URI parts to keep when computing package names
        """
        self.factory = factory
        self.basename = basename
        self.keep_uri_parts = keep_uri_parts

    def find_module(self, fullname, path=None):
        """
        Return a valid module loader for paths matching basename.
        """
        if fullname.split(".")[0] == self.basename:
            # only handle basename
            return ModuleLoader(
                factory=self.factory,
                basename=self.basename,
                keep_uri_parts=self.keep_uri_parts,
            )
        return None


class ModuleLoader(object):
    """
    A module "loader" that auto-generates classes.
    """
    def __init__(self, factory, basename, keep_uri_parts=None):
        """
        :param factory: the class generation factory
        :param basename: package name prefix for module auto-loading
        :param keep_uri_parts: number of URI parts to keep when computing package names
        """
        self.factory = factory
        self.basename = basename
        self.keep_uri_parts = keep_uri_parts

    def load_module(self, fullname):
        """
        Load module matching full name.
        """
        matching_classes = {
            schema_id: self.factory.make_class(schema_id)
            for schema_id in self.factory.registry
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
