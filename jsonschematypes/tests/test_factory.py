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

from jsonschematypes.factory import TypeFactory
from jsonschematypes.registry import Registry
from jsonschematypes.tests.fixtures import NAME, NAME_ID, schema_for


def test_create_class():
    """
    Can create a class for a schema.
    """
    registry = Registry()
    registry.load(schema_for("data/name.json"))

    Name = registry.create_class(NAME_ID)

    name = Name(
        first="George",
        last="Washington",
    )

    assert_that(
        name,
        has_properties(
            first=equal_to("George"),
            last=equal_to("Washington"),
        )
    )
    assert_that(name.to_dict(), is_(equal_to(NAME)))
    assert_that(name, is_(equal_to(Name.from_dict(NAME))))


def test_validate_created_class():
    """
    Can validate a generated object.
    """
    registry = Registry()
    registry.load(schema_for("data/name.json"))

    Name = registry.create_class(NAME_ID)
    name = Name()

    assert_that(calling(name.validate), raises(ValidationError))

    name.first = "George"
    name.last = "Washington"

    name.validate()

    del name.first

    assert_that(calling(name.validate), raises(ValidationError))


def test_imports():
    """
    Can import a class from a registry.
    """
    registry = Registry()
    registry.load(schema_for("data/name.json"))
    registry.configure_imports()

    from generated.foo import Name

    name = Name(
        first="George",
        last="Washington",
    )
    name.validate()


def test_package_names():
    """
    Package name generation from URI works as expected.
    """
    registry = Registry()
    factory = TypeFactory(registry, basename="test")

    assert_that(
        factory.package_name_for("http://x.y.z/foo"),
        is_(equal_to("test"))
    )
    assert_that(
        factory.package_name_for("http://x.y.z/foo/bar"),
        is_(equal_to("test.foo"))
    )
    assert_that(
        factory.package_name_for("http://x.y.z/Foo/Bar/Baz"),
        is_(equal_to("test.foo.bar"))
    )
    assert_that(
        factory.package_name_for("foo"),
        is_(equal_to("test"))
    )
    assert_that(
        factory.package_name_for("foo/bar"),
        is_(equal_to("test.foo"))
    )


def test_class_names():
    """
    Class name generation from URI works as expected.
    """
    registry = Registry()
    factory = TypeFactory(registry, basename="test")

    assert_that(
        factory.class_name_for("http://x.y.z/foo"),
        is_(equal_to("Foo"))
    )
    assert_that(
        factory.class_name_for("http://x.y.z/foo/bar"),
        is_(equal_to("Bar"))
    )
    assert_that(
        factory.class_name_for("http://x.y.z/Foo/Bar/Baz"),
        is_(equal_to("Baz"))
    )
    assert_that(
        factory.class_name_for("foo"),
        is_(equal_to("Foo"))
    )
    assert_that(
        factory.class_name_for("foo/bar"),
        is_(equal_to("Bar"))
    )


def test_attribute_names():
    """
    Attribute name generation works as expected.
    """
    registry = Registry()
    factory = TypeFactory(registry, basename="test")

    assert_that(
        factory.attribute_name_for("fooBar"),
        is_(equal_to("foo_bar"))
    )
    assert_that(
        factory.attribute_name_for("FooBar"),
        is_(equal_to("foo_bar"))
    )
    assert_that(
        factory.attribute_name_for("foo_bar"),
        is_(equal_to("foo_bar"))
    )
