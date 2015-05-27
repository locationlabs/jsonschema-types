"""
Test registry loading and validation.
"""
from gzip import GzipFile
from tarfile import TarFile
from tempfile import NamedTemporaryFile

from hamcrest import (
    assert_that,
    calling,
    equal_to,
    has_item,
    has_key,
    has_length,
    is_,
    raises,
)
from jsonschema import RefResolutionError, ValidationError

from jsonschematypes.registry import Registry
from jsonschematypes.tests.fixtures import (
    ADDRESS_ID,
    NAME_ID,
    RECORD,
    RECORD_ID,
    schema_for,
)


def build_tar(fileobj, mode="w"):
    tarfile = TarFile(mode=mode, fileobj=fileobj)
    tarfile.add(schema_for("data/address.json"))
    tarfile.add(schema_for("data/name.json"))
    tarfile.add(schema_for("data/record.json"))


def test_load_single_file():
    """
    Registry can load a single file.
    """
    registry = Registry()

    schema_ids = registry.load(schema_for("data/name.json"))

    assert_that(schema_ids, has_length(1))
    assert_that(schema_ids, has_item(NAME_ID))

    assert_that(registry, has_length(1))
    assert_that(registry, has_key(NAME_ID))


def test_load_multiple_files():
    """
    Registry can load multiple files.
    """
    registry = Registry()

    schema_ids = registry.load(
        schema_for("data/address.json"),
        schema_for("data/name.json"),
    )
    assert_that(schema_ids, has_length(2))
    assert_that(schema_ids, has_item(ADDRESS_ID))
    assert_that(schema_ids, has_item(NAME_ID))

    assert_that(registry, has_length(2))
    assert_that(registry, has_key(ADDRESS_ID))
    assert_that(registry, has_key(NAME_ID))


def test_load_tarfile():
    """
    Registry can load a tar file.
    """
    registry = Registry()

    with NamedTemporaryFile() as fileobj:
        build_tar(fileobj)
        fileobj.flush()

        schema_ids = registry.load(fileobj.name)
        assert_that(schema_ids, has_length(3))
        assert_that(schema_ids, has_item(ADDRESS_ID))
        assert_that(schema_ids, has_item(NAME_ID))
        assert_that(schema_ids, has_item(RECORD_ID))

        assert_that(registry, has_length(3))
        assert_that(registry, has_key(ADDRESS_ID))
        assert_that(registry, has_key(NAME_ID))
        assert_that(registry, has_key(RECORD_ID))


def test_load_compressed_tarfile():
    """
    Registry can load a compressed tar file.
    """
    registry = Registry()

    with NamedTemporaryFile() as fileobj:
        with GzipFile(fileobj.name, "w") as gzfileobj:
            build_tar(gzfileobj)
        fileobj.flush()

        schema_ids = registry.load(fileobj.name)
        assert_that(schema_ids, has_length(3))
        assert_that(schema_ids, has_item(ADDRESS_ID))
        assert_that(schema_ids, has_item(NAME_ID))
        assert_that(schema_ids, has_item(RECORD_ID))

        assert_that(registry, has_length(3))
        assert_that(registry, has_key(ADDRESS_ID))
        assert_that(registry, has_key(NAME_ID))
        assert_that(registry, has_key(RECORD_ID))


def test_validate():
    """
    Registry can validate using stored schemas.
    """
    registry = Registry()

    registry.load(
        schema_for("data/address.json"),
        schema_for("data/name.json"),
        schema_for("data/record.json"),
    )

    assert_that(
        calling(registry.validate).with_args({}, RECORD_ID),
        raises(ValidationError),
    )

    registry.validate(RECORD, RECORD_ID)


def test_validate_does_not_resolve_reference():
    """
    Registry suppresses HTTP URI resolution by default.
    """
    registry = Registry()

    registry.load(
        schema_for("data/record.json"),
    )

    assert_that(
        calling(registry.validate).with_args(RECORD, RECORD_ID),
        raises(RefResolutionError),
    )


def test_find_unresolved():
    """
    Registry can find unresolved refs.
    """
    registry = Registry()

    registry.load(schema_for("data/record.json"))

    assert_that(
        registry.find_unresolved(),
        is_(equal_to({ADDRESS_ID, NAME_ID}))
    )
