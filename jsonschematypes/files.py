"""
Schema loading functions from various kinds of files.

The `Registry` loads schemas based on file paths. To support
various kinds of files (especially tar+gz), it delegates to
different schmea loading functions based on the file mime type.
"""
from contextlib import closing
from gzip import GzipFile
from json import load, loads
from tarfile import TarFile
from tempfile import NamedTemporaryFile

import magic


def iter_file(filename, mime_types):
    """
    Iterate through (the single) schema in a JSON file.
    """
    with closing(open(filename)) as fileobj:
        yield load(fileobj)


def iter_gzip(filename, mime_types):
    """
    Iterate through all schemas in a gzip file.
    """
    with GzipFile(filename, "r") as gzipfileobj:
        with NamedTemporaryFile() as fileobj:
            fileobj.write(gzipfileobj.read())
            fileobj.flush()
            for schema in iter_schemas(fileobj.name, mime_types):
                yield schema


def iter_tar(filename, mime_types):
    """
    Iterate through all schemas in a tar file.
    """
    with closing(TarFile.open(filename)) as tarfile:
        for tarinfo in tarfile:
            if tarinfo.isreg():
                fileobj = tarfile.extractfile(tarinfo)
                data = fileobj.read()
                yield loads(data.decode())


def iter_schemas(filename, mime_types):
    """
    Iterate through all schemas in a file.
    """
    mime_type = magic.from_file(filename, mime=type)
    iter_func = mime_types.get(mime_type.decode(), iter_file)
    for schema in iter_func(filename, mime_types):
        yield schema
