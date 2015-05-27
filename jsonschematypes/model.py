"""
Model generation based on JSON schema definitions.
"""


class Attribute(object):
    """
    Descriptor for attribute references into a dictionary.
    """
    def __init__(self, key):
        self.key = key

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


class SchemaDict(dict):
    """
    Schema and registry-aware dictionary.
    """
    def validate(self, skip_http=True):
        """
        Validate that this instance matches its schema.

        See `Registry.validate()`.
        """
        self.__class__._REGISTRY.validate(
            self.to_dict(),
            self.__class__._ID,
            skip_http=skip_http,
        )

    def to_dict(self):
        """
        Convert to a dictionary.
        """
        return self

    @classmethod
    def from_dict(cls, dct):
        """
        Construct instance from a dictionary.
        """
        return cls(dct)
