"""
Interpose JSON schema loading through a registry of known schemas.
"""
from contextlib import closing
from gzip import GzipFile
from json import load, loads
from tarfile import TarFile
from tempfile import NamedTemporaryFile
import sys

from jsonschema import RefResolver, RefResolutionError, validate
import magic

from jsonschematypes.factory import TypeFactory


def iter_file(registry, filename):
    with closing(open(filename)) as fileobj:
        yield load(fileobj)


def iter_gzip(registry, filename):
    with GzipFile(filename, "r") as gzipfileobj:
        with NamedTemporaryFile() as fileobj:
            fileobj.write(gzipfileobj.read())
            fileobj.flush()
            for schema in registry.iter_schemas(fileobj.name):
                yield schema


def iter_tarfile(registry, filename, mode="r"):
    with closing(TarFile.open(filename)) as tarfile:
        for tarinfo in tarfile:
            if tarinfo.isreg():
                fileobj = tarfile.extractfile(tarinfo)
                data = fileobj.read()
                yield loads(data.decode())


def do_not_resolve(uri):
    raise RefResolutionError(uri)


class Registry(dict):
    """
    A registry of loaded JSON schemas, mapped by id.

    JSON Schema ids are both unique names and URIs. Keeping a registry of
    known schemas avoids URI loading at runtime.
    """
    def __init__(self, mime_types=None):
        super(Registry, self).__init__()
        self._mime_types = {
            "application/x-gzip": iter_gzip,
            "application/x-tar": iter_tarfile,
        }
        if mime_types:
            self._mime_types.update(mime_types)

    def load(self, *filenames):
        """
        Load one or more schemas from file.

        Files are evaluated according to their mime types, which allows
        archives (e.g. tars) to be loaded.
        """
        return [
            self.register(schema)
            for filename in filenames
            for schema in self.iter_schemas(filename)
        ]

    def validate(self, instance, schema_id, skip_http=True):
        """
        Validate an instance against a registered schema.
        """
        schema = self[schema_id]
        handlers = {}
        if skip_http:
            handlers.update(
                http=do_not_resolve,
                https=do_not_resolve,
            )
        resolver = RefResolver.from_schema(
            schema,
            store=self,
            handlers=handlers,
        )
        return validate(instance, schema, resolver=resolver)

    def create_class(self, schema_id):
        """
        Create a Python class that maps to the given schema.
        """
        return TypeFactory(self).make_class(schema_id)

    def configure_imports(self, basename="generated"):
        """
        Register an import handler that automatically creates classes.
        """
        sys.meta_path.append(TypeFactory(self, basename=basename))

    def find_unresolved(self):
        """
        Return all unresolved schema references.
        """
        return {
            ref
            for schema in self.values()
            for ref in self.iter_refs(schema)
            if ref not in self
        }

    def register(self, schema):
        """
        Register a schema.

        Schemas must define an `id` attribute.
        """
        schema_id = schema["id"]
        self[schema_id] = schema
        return schema_id

    def iter_schemas(self, filename):
        """
        Iterate through all schemas in a file.
        """
        mime_type = magic.from_file(filename, mime=type)
        iter_func = self._mime_types.get(mime_type.decode(), iter_file)
        for schema in iter_func(self, filename):
            yield schema

    def iter_refs(self, schema):
        """
        Iterate through all refs in a schema.
        """
        REF = "$ref"
        if REF in schema:
            yield schema[REF]
        for property_ in schema.get("properties", {}).values():
            if REF in property_:
                yield property_[REF]
