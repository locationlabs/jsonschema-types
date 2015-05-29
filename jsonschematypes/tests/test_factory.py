"""
Code generation and import tests.
"""
from hamcrest import (
    assert_that,
    calling,
    equal_to,
    has_properties,
    is_,
    raises,
)
from jsonschema import ValidationError

from jsonschematypes.registry import Registry
from jsonschematypes.tests.fixtures import NAME, NAME_ID, schema_for


def test_class_names():
    """
    Class name generation from URI works as expected.
    """
    registry = Registry()

    assert_that(
        registry.factory.class_name_for("http://x.y.z/foo"),
        is_(equal_to("Foo"))
    )
    assert_that(
        registry.factory.class_name_for("http://x.y.z/foo/bar"),
        is_(equal_to("Bar"))
    )
    assert_that(
        registry.factory.class_name_for("http://x.y.z/Foo/Bar/Baz"),
        is_(equal_to("Baz"))
    )
    assert_that(
        registry.factory.class_name_for("foo"),
        is_(equal_to("Foo"))
    )
    assert_that(
        registry.factory.class_name_for("foo.json"),
        is_(equal_to("Foo"))
    )
    assert_that(
        registry.factory.class_name_for("foo/bar"),
        is_(equal_to("Bar"))
    )
    assert_that(
        registry.factory.class_name_for("foo/bar.schema"),
        is_(equal_to("Bar"))
    )
    assert_that(
        registry.factory.class_name_for("FooBar"),
        is_(equal_to("FooBar"))
    )


def test_attribute_names():
    """
    Attribute name generation works as expected.
    """
    registry = Registry()

    assert_that(
        registry.factory.attribute_name_for("fooBar"),
        is_(equal_to("foo_bar"))
    )
    assert_that(
        registry.factory.attribute_name_for("FooBar"),
        is_(equal_to("foo_bar"))
    )
    assert_that(
        registry.factory.attribute_name_for("foo_bar"),
        is_(equal_to("foo_bar"))
    )


def test_create_object():
    """
    Can create a class for an object schema.
    """
    registry = Registry()
    registry.load(schema_for("data/name.json"))

    Name = registry.create_class(NAME_ID)

    name = Name(
        first="George",
    )

    assert_that(calling(name.validate), raises(ValidationError))

    name.last = "Washington"

    name.validate()

    assert_that(
        name,
        has_properties(
            first=equal_to("George"),
            last=equal_to("Washington"),
        )
    )
    assert_that(name, is_(equal_to(NAME)))
    assert_that(name, is_(equal_to(Name(**NAME))))
    assert_that(Name.loads(name.dumps()), is_(equal_to(name)))

    del name.first

    assert_that(calling(name.validate), raises(ValidationError))


def test_create_enum():
    """
    Can create a class for an enum schema
    """
    registry = Registry()
    registry["id"] = {
        "type": "string",
        "enum": ["Foo", "Bar"],
    }

    Enum = registry.create_class("id")

    enum = Enum("Foo")
    enum.validate()

    assert_that(calling(Enum("").validate), raises(ValidationError))

    assert_that(Enum.loads(enum.dumps()), is_(equal_to(enum)))
    assert_that(enum.dumps(), is_(equal_to(('"Foo"'))))


def test_create_array():
    """
    Can create a class for an array schema
    """
    registry = Registry()
    registry["id"] = {
        "type": "array",
        "items": {"type": "integer"}
    }

    Array = registry.create_class("id")

    array = Array([1, 2])
    array.validate()

    assert_that(calling(Array("foo").validate), raises(ValidationError))
    assert_that(calling(Array([1.0, 2.0]).validate), raises(ValidationError))

    assert_that(Array.loads(array.dumps()), is_(equal_to(array)))
    assert_that(array.dumps(), is_(equal_to(('[1, 2]'))))
