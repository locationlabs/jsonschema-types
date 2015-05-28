"""
Model generation based on JSON schema definitions.
"""
import json


class Attribute(object):
    """
    Descriptor for attribute references into a dictionary.
    """
    def __init__(self, key, description=None, required=False):
        self.key = key
        self.description = description
        self.required = required

        if description:
            self.__doc__ = "{} ({})".format(
                description,
                "required" if required else "optional",
            )

    def __get__(self, instance, owner):
        if instance is None:
            return self
        try:
            return instance[self.key]
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
