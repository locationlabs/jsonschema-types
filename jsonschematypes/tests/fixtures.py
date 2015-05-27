"""
Common test fixtures.
"""
from os.path import dirname, join


ADDRESS = dict(
    street="1600 Pennsylvania Ave",
    city="Washington",
    state="DC",
)

NAME = dict(
    first="George",
    last="Washington",
)

RECORD = dict(
    name=NAME,
    address=ADDRESS,
)


ADDRESS_ID = "http://x.y.z/bar/address"
NAME_ID = "http://x.y.z/foo/name"
RECORD_ID = "http://x.y.z/record"


def schema_for(name):
    return join(dirname(__file__), name)
