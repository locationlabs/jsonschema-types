"""
Model generation based on JSON schema definitions.
"""
import json


ID = u"id"
DEFAULT = u"default"
DEFINITIONS = u"definitions"
DESCRIPTION = u"description"
ITEMS = u"items"
PROPERTIES = u"properties"
REF = u"$ref"
REQUIRED = u"required"
TYPE = u"type"


class Attribute(object):
    """
    Descriptor for attribute references into a dictionary.
    """
    def __init__(self, registry, key, description=None, required=False, default=None):
        self.registry = registry
        self.key = key
        self.description = description
        self.required = required
        self.default = default

        if description:
            self.__doc__ = "{} ({})".format(
                description,
                "required" if required else "optional",
            )

    def __get__(self, instance, owner):
        """
        Attribute-based access to underlying JSON data.

        Converts between Pythonic types and naming conventions and underlying raw data.
        """
        if instance is None:
            return self
        try:
            value = instance[self.key]

            if isinstance(value, SchemaAware):
                return value

            ref = instance._SCHEMA.get(PROPERTIES, {}).get(self.key, {}).get(REF)
            ref_class = instance._REGISTRY.create_class_for(instance._SCHEMA, ref)
            return ref_class(value) if ref_class else value
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                instance.__class__.__name__,
                self.key,
            ))

    def __set__(self, instance, value):
        instance[self.key] = value

    def __delete__(self, instance):
        try:
            del instance[self.key]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format(
                instance.__class__.__name__,
                self.key,
            ))


class SchemaAware(object):
    """
    Schema and registry-aware mixin.

    Generated classes mix-in SchemaAware with the Python representations of
    JSON primitives (e.g. dict, list, float) so that existing JSON libraries
    "just work".
    """
    def validate(self, skip_http=True):
        """
        Validate that this instance matches its schema.

        See `Registry.validate()`.
        """
        self.__class__._REGISTRY.validate(
            self,
            self.__class__._ID,
            skip_http=skip_http,
        )

    def dump(self, fileobj):
        return json.dump(self, fileobj)

    def dumps(self):
        return json.dumps(self)

    @classmethod
    def loads(cls, data):
        return cls(json.loads(data))

    @classmethod
    def load(cls, fileobj):
        return cls(json.load(fileobj))


class SchemaAwareDict(dict, SchemaAware):
    """
    Schema aware dictionary type.

    Sets defaults based on attributes.
    """
    def __init__(self, *args, **kwargs):
        """
        Insert defaults into dictionary.
        """
        super(SchemaAwareDict, self).__init__(*args, **kwargs)
        for key, value in vars(self.__class__).items():
            if isinstance(value, Attribute):
                if value.default is not None and not hasattr(self, key):
                    setattr(self, key, value.default)


class SchemaAwareList(list, SchemaAware):
    """
    Schema aware list type.
    """
    def __getitem__(self, index):
        """
        Override item access to convert types.
        """
        value = super(SchemaAwareList, self).__getitem__(index)

        if isinstance(value, SchemaAware):
            return value

        ref = self._SCHEMA.get(ITEMS, {}).get(REF)
        ref_class = self._REGISTRY.create_class_for(self._SCHEMA, ref)
        return ref_class(value) if ref_class else value


class SchemaAwareString(str, SchemaAware):
    """
    Schema aware string type.

    Especially useful for enumeration validation.
    """
    pass
