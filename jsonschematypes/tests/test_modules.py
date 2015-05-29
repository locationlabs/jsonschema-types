"""
Code generation and import tests.
"""
from hamcrest import (
    assert_that,
    calling,
    equal_to,
    is_,
    raises,
)
from jsonschematypes.modules import ModuleLoader
from jsonschematypes.registry import Registry
from jsonschematypes.tests.fixtures import schema_for


def test_package_names():
    """
    Package name generation from URI works as expected.
    """
    registry = Registry()
    loader = ModuleLoader(registry.factory, basename="test")

    assert_that(
        loader.package_name_for("http://x.y.z/foo"),
        is_(equal_to("test"))
    )
    assert_that(
        loader.package_name_for("http://x.y.z/foo/bar"),
        is_(equal_to("test.foo"))
    )
    assert_that(
        loader.package_name_for("http://x.y.z/Foo/Bar/Baz"),
        is_(equal_to("test.foo.bar"))
    )
    assert_that(
        loader.package_name_for("foo"),
        is_(equal_to("test"))
    )
    assert_that(
        loader.package_name_for("foo/bar"),
        is_(equal_to("test.foo"))
    )


def test_illegal_package_name():
    """
    Illegal package names are detected.
    """
    registry = Registry()
    loader = ModuleLoader(registry.factory, basename="test")

    assert_that(
        calling(loader.package_name_for).with_args("foo/1.0/bar"),
        raises(ValueError),
    )
    assert_that(
        calling(loader.package_name_for).with_args("_foo/bar"),
        raises(ValueError),
    )


def test_keep_part_of_package_name():
    """
    URI withs otherwise illegal package names can be truncated to form legal ones
    by keeping only part of the URI.
    """
    registry = Registry()
    loader = ModuleLoader(registry.factory, basename="test", keep_uri_parts=2)

    assert_that(
        loader.package_name_for("foo/bar"),
        is_(equal_to("test.foo"))
    )
    assert_that(
        loader.package_name_for("foo/bar/baz"),
        is_(equal_to("test.bar"))
    )
    assert_that(
        loader.package_name_for("foo/1.0/bar/baz"),
        is_(equal_to("test.bar"))
    )


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
