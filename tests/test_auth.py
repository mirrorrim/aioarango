import pytest

from aioarango import ArangoClient
from aioarango.connection import BasicConnection, JwtConnection, JwtSuperuserConnection
from aioarango.errno import FORBIDDEN, HTTP_UNAUTHORIZED
from aioarango.exceptions import (
    JWTAuthError,
    JWTSecretListError,
    JWTSecretReloadError,
    ServerEncryptionError,
    ServerTLSError,
    ServerTLSReloadError,
    ServerVersionError,
)
from tests.helpers import assert_raises, generate_jwt, generate_string

pytestmark = pytest.mark.asyncio


async def test_auth_invalid_method(client: ArangoClient, db_name, username, password):
    with assert_raises(ValueError) as err:
        await client.db(
            name=db_name,
            username=username,
            password=password,
            verify=True,
            auth_method="bad_method",
        )
    assert "invalid auth_method" in str(err.value)


async def test_auth_basic(client: ArangoClient, db, db_name, username, password):
    db = await client.db(
        name=db_name,
        username=username,
        password=password,
        verify=True,
        auth_method="basic",
    )
    assert isinstance(db.conn, BasicConnection)
    assert isinstance(await db.version(), str)
    assert isinstance(await db.properties(), dict)


async def test_auth_jwt(client: ArangoClient, db, db_name, username, password):
    db = await client.db(
        name=db_name,
        username=username,
        password=password,
        verify=True,
        auth_method="jwt",
    )
    assert isinstance(db.conn, JwtConnection)
    assert isinstance(await db.version(), str)
    assert isinstance(await db.properties(), dict)

    bad_password = generate_string()
    with assert_raises(JWTAuthError) as err:
        await client.db(db_name, username, bad_password, auth_method="jwt")
    assert err.value.error_code == HTTP_UNAUTHORIZED


# TODO re-examine commented out code
@pytest.mark.skip(reason="ArangoDB is not configured to use JWT auth.")
async def test_auth_superuser_token(client, db_name, root_password, secret):
    token = generate_jwt(secret)
    db = await client.db("_system", superuser_token=token)
    bad_db = await client.db("_system", superuser_token="bad_token")

    assert isinstance(db.conn, JwtSuperuserConnection)
    assert isinstance(await db.version(), str)
    assert isinstance(await db.properties(), dict)

    # # Test get JWT secrets
    # secrets = db.jwt_secrets()
    # assert 'active' in secrets
    # assert 'passive' in secrets

    # Test get JWT secrets with bad database
    with assert_raises(JWTSecretListError) as err:
        await bad_db.jwt_secrets()
    assert err.value.error_code == FORBIDDEN

    # # Test reload JWT secrets
    # secrets = db.reload_jwt_secrets()
    # assert 'active' in secrets
    # assert 'passive' in secrets

    # Test reload JWT secrets with bad database
    with assert_raises(JWTSecretReloadError) as err:
        await bad_db.reload_jwt_secrets()
    assert err.value.error_code == FORBIDDEN

    # Test get TLS data
    result = await db.tls()
    assert isinstance(result, dict)

    # Test get TLS data with bad database
    with assert_raises(ServerTLSError) as err:
        await bad_db.tls()
    assert err.value.error_code == FORBIDDEN

    # Test reload TLS
    result = await db.reload_tls()
    assert isinstance(result, dict)

    # Test reload TLS with bad database
    with assert_raises(ServerTLSReloadError) as err:
        await bad_db.reload_tls()
    assert err.value.error_code == FORBIDDEN

    # # Test get encryption
    # result = db.encryption()
    # assert isinstance(result, dict)

    # Test reload user-defined encryption keys.
    with assert_raises(ServerEncryptionError) as err:
        await bad_db.encryption()
    assert err.value.error_code == FORBIDDEN


async def test_auth_jwt_expiry(client, db_name, root_password, secret):
    # Test automatic token refresh on expired token.
    db = await client.db("_system", "root", root_password, auth_method="jwt")
    expired_token = generate_jwt(secret, exp=-1000)
    db.conn._token = expired_token
    db.conn._auth_header = f"bearer {expired_token}"
    assert isinstance(await db.version(), str)

    # Test correct error on token expiry.
    db = await client.db("_system", superuser_token=expired_token)
    with assert_raises(ServerVersionError) as err:
        await db.version()
    assert err.value.error_code == FORBIDDEN
