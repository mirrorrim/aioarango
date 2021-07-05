import json

import pytest
from pkg_resources import get_distribution

from aioarango.client import ArangoClient
from aioarango.database import StandardDatabase
from aioarango.exceptions import ServerConnectionError
from aioarango.http import DefaultHTTPClient
from aioarango.resolver import (
    RandomHostResolver,
    RoundRobinHostResolver,
    SingleHostResolver,
)
from tests.helpers import generate_db_name, generate_string, generate_username

pytestmark = pytest.mark.asyncio


@pytest.mark.skip(reason="Package is not installed")
async def test_client_attributes():
    http_client = DefaultHTTPClient()

    client = ArangoClient(hosts="http://127.0.0.1:8529", http_client=http_client)
    assert client.version == get_distribution("aioarango").version
    assert client.hosts == ["http://127.0.0.1:8529"]

    assert repr(client) == "<ArangoClient http://127.0.0.1:8529>"
    assert isinstance(client._host_resolver, SingleHostResolver)

    client_repr = "<ArangoClient http://127.0.0.1:8529,http://localhost:8529>"
    client_hosts = ["http://127.0.0.1:8529", "http://localhost:8529"]

    client = ArangoClient(
        hosts="http://127.0.0.1:8529,http://localhost" ":8529",
        http_client=http_client,
        serializer=json.dumps,
        deserializer=json.loads,
    )
    assert client.version == get_distribution("aioarango").version
    assert client.hosts == client_hosts
    assert repr(client) == client_repr
    assert isinstance(client._host_resolver, RoundRobinHostResolver)

    client = ArangoClient(
        hosts=client_hosts,
        host_resolver="random",
        http_client=http_client,
        serializer=json.dumps,
        deserializer=json.loads,
    )
    assert client.version == get_distribution("aioarango").version
    assert client.hosts == client_hosts
    assert repr(client) == client_repr
    assert isinstance(client._host_resolver, RandomHostResolver)


async def test_client_good_connection(db: StandardDatabase, username, password):
    client = ArangoClient(hosts="http://127.0.0.1:8529")

    # Test connection with verify flag on and off
    for verify in (True, False):
        db = await client.db(db.name, username, password, verify=verify)
        assert isinstance(db, StandardDatabase)
        assert db.name == db.name
        assert db.username == username
        assert db.context == "default"


async def test_client_bad_connection(db: StandardDatabase, username, password, cluster):
    client = ArangoClient(hosts="http://127.0.0.1:8529")

    bad_db_name = generate_db_name()
    bad_username = generate_username()
    bad_password = generate_string()

    if not cluster:
        # Test connection with bad username password
        with pytest.raises(ServerConnectionError):
            await client.db(db.name, bad_username, bad_password, verify=True)

    # Test connection with missing database
    with pytest.raises(ServerConnectionError):
        await client.db(bad_db_name, bad_username, bad_password, verify=True)

    # Test connection with invalid host URL
    client = ArangoClient(hosts="http://127.0.0.1:8500")
    with pytest.raises(ServerConnectionError) as err:
        await client.db(db.name, username, password, verify=True)
    assert "bad connection" in str(err.value)


async def test_client_custom_http_client(db: StandardDatabase, username, password):

    # Define custom HTTP client which increments the counter on any API call.
    class MyHTTPClient(DefaultHTTPClient):
        def __init__(self) -> None:
            super().__init__()
            self.counter = 0

        async def send_request(
            self, session, method, url, headers=None, params=None, data=None, auth=None
        ):
            self.counter += 1
            return await super().send_request(
                session, method, url, headers, params, data, auth
            )

    http_client = MyHTTPClient()
    client = ArangoClient(hosts="http://127.0.0.1:8529", http_client=http_client)
    # Set verify to True to send a test API call on initialization.
    await client.db(db.name, username, password, verify=True)
    assert http_client.counter == 1
