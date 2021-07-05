import pytest

from aioarango.database import StandardDatabase
from aioarango.errno import DATABASE_NOT_FOUND, FORBIDDEN
from aioarango.exceptions import (
    ClusterEndpointsError,
    ClusterHealthError,
    ClusterMaintenanceModeError,
    ClusterServerCountError,
    ClusterServerEngineError,
    ClusterServerIDError,
    ClusterServerRoleError,
    ClusterServerStatisticsError,
    ClusterServerVersionError,
)
from tests.helpers import assert_raises

pytestmark = pytest.mark.asyncio


async def test_cluster_server_id(sys_db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    result = await sys_db.cluster.server_id()
    assert isinstance(result, str)

    with assert_raises(ClusterServerIDError) as err:
        await bad_db.cluster.server_id()
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_server_role(sys_db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    result = await sys_db.cluster.server_role()
    assert isinstance(result, str)

    with assert_raises(ClusterServerRoleError) as err:
        await bad_db.cluster.server_role()
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_health(sys_db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    result = await sys_db.cluster.health()
    assert "Health" in result
    assert "ClusterId" in result

    with assert_raises(ClusterHealthError) as err:
        await bad_db.cluster.health()
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_server_version(sys_db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    server_id = await sys_db.cluster.server_id()
    result = await sys_db.cluster.server_version(server_id)
    assert "server" in result
    assert "version" in result

    with assert_raises(ClusterServerVersionError) as err:
        await bad_db.cluster.server_version(server_id)
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_server_engine(sys_db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    server_id = await sys_db.cluster.server_id()
    result = await sys_db.cluster.server_engine(server_id)
    assert "name" in result
    assert "supports" in result

    with assert_raises(ClusterServerEngineError) as err:
        await bad_db.cluster.server_engine(server_id)
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_server_statistics(sys_db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    server_id = await sys_db.cluster.server_id()
    result = await sys_db.cluster.server_statistics(server_id)
    assert "time" in result
    assert "system" in result
    assert "enabled" in result

    with assert_raises(ClusterServerStatisticsError) as err:
        await bad_db.cluster.server_statistics(server_id)
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_toggle_maintenance_mode(sys_db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    result = await sys_db.cluster.toggle_maintenance_mode("on")
    assert "error" in result or "warning" in result

    result = await sys_db.cluster.toggle_maintenance_mode("off")
    assert "error" in result or "warning" in result

    with assert_raises(ClusterMaintenanceModeError) as err:
        await bad_db.cluster.toggle_maintenance_mode("on")
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_endpoints(db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    # Test get server endpoints
    assert len(await db.cluster.endpoints()) > 0

    # Test get server endpoints with bad database
    with assert_raises(ClusterEndpointsError) as err:
        await bad_db.cluster.endpoints()
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}


async def test_cluster_server_count(db: StandardDatabase, bad_db: StandardDatabase, cluster):
    if not cluster:
        pytest.skip("Only tested in a cluster setup")

    # Test get server count
    await db.cluster.server_count()

    # Test get server endpoints with bad database
    with assert_raises(ClusterServerCountError) as err:
        await bad_db.cluster.server_count()
    assert err.value.error_code in {FORBIDDEN, DATABASE_NOT_FOUND}
