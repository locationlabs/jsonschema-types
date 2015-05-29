"""
Interpose JSON schema loading through a registry of known schemas.
"""
import sys

from jsonschema import RefResolver, RefResolutionError, validate

from jsonschematypes.factory import TypeFactory
from jsonschematypes.files import iter_gzip, iter_tar, iter_schemas
from jsonschematypes.model import DEFINITIONS, ID, REF
from jsonschematypes.modules import ModuleFinder


def iter_schema_refs(schema):
    """
    Iterate through all refs in a schema.
    """
    if REF in schema:
        yield schema[REF]
    for property_ in schema.get("properties", {}).values():
        if REF in property_:
            yield property_[REF]


def do_not_resolve(uri):
    raise RefResolutionError(uri)


class Registry(dict):
    """
    A registry of loaded JSON schemas, mapped by id.

    JSON Schema ids are both unique names and URIs. Keeping a registry of
    known schemas avoids URI loading at runtime.
    """
    def __init__(self, mime_types=None):
        """
        :param mime_types: a mapping of mime types to schema loading functions.
        """
        super(Registry, self).__init__()
        self.mime_types = {
            "application/x-gzip": iter_gzip,
            "application/x-tar": iter_tar,
        }
        if mime_types:
            self.mime_types.update(mime_types)
        self.factory = TypeFactory(self)

    def load(self, *filenames):
        """
        Load one or more schemas from file.

        Files are evaluated according to their mime types, which allows
        archives (e.g. tars) to be loaded.
        """
        return [
            self.register(schema)
            for filename in filenames
            for schema in iter_schemas(filename, self.mime_types)
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
        return self.factory.make_class(schema_id)

    def create_class_for(self, schema, ref):
        if ref is None:
            return None

        try:
            return self.create_class(self.expand_ref(schema, ref))
        except KeyError:
            # unable to resolve ref; fall through
            return None

    def configure_imports(self, basename="generated", keep_uri_parts=None):
        """
        Register an import handler that automatically creates classes.
        """
        sys.meta_path.append(ModuleFinder(
            factory=self.factory,
            basename=basename,
            keep_uri_parts=keep_uri_parts,
        ))

    def find_unresolved(self):
        """
        Return all unresolved schema references.
        """
        return {
            ref
            for schema in self.values()
            for ref in iter_schema_refs(schema)
            if self.expand_ref(schema, ref) not in self
        }

    def register(self, schema):
        """
        Register a schema.

        Schemas must define an `id` attribute.
        """
        schema_id = schema[ID]
        self[schema_id] = schema
        for definition in schema.get(DEFINITIONS, {}).values():
            self.register(definition)
        return schema_id

    def expand_ref(self, schema, ref):
        """
        Expand refs to internal definitions.
        """
        if ref is None:
            return ref

        if ref.startswith("#/definitions/"):
            definition = ref.split("#/definitions/", 1)[1]
            return schema.get(DEFINITIONS, {}).get(definition, {}).get(ID, ref)

        return ref
