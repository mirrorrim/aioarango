import asyncio
from dataclasses import dataclass

import pytest

from aioarango import ArangoClient, formatter
from aioarango.database import Database, StandardDatabase
from aioarango.graph import Graph
from aioarango.typings import Json
from tests.executors import (
    TestAsyncApiExecutor,
    TestBatchExecutor,
    TestTransactionApiExecutor,
)
from tests.helpers import (
    empty_collection,
    generate_col_name,
    generate_db_name,
    generate_graph_name,
    generate_jwt,
    generate_string,
    generate_username,
)

pytestmark = pytest.mark.asyncio


@dataclass
class GlobalData:
    url: str = None
    username: str = None
    password: str = None
    db_name: str = None
    bad_db_name: str = None
    geo_index: Json = None
    col_name: str = None
    icol_name: str = None
    graph_name: str = None
    ecol_name: str = None
    fvcol_name: str = None
    tvcol_name: str = None
    cluster: bool = None
    complete: bool = None
    replication: bool = None
    enterprise: bool = None
    secret: str = None
    root_password: str = None


global_data = GlobalData()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_addoption(parser):
    parser.addoption("--host", action="store", default="127.0.0.1")
    parser.addoption("--port", action="store", default="8529")
    parser.addoption("--passwd", action="store", default="openSesame")
    parser.addoption("--complete", action="store_true")
    parser.addoption("--cluster", action="store_true")
    parser.addoption("--replication", action="store_true")
    parser.addoption("--enterprise", action="store_true")
    parser.addoption("--secret", action="store", default="secret")


def pytest_configure(config):
    global_data.url = f"http://{config.getoption('host')}:{config.getoption('port')}"
    global_data.username = generate_username()
    global_data.password = generate_string()
    global_data.db_name = generate_db_name()
    global_data.bad_db_name = generate_db_name()
    global_data.col_name = generate_col_name()
    global_data.icol_name = generate_col_name()
    global_data.graph_name = generate_graph_name()
    global_data.ecol_name = generate_col_name()
    global_data.fvcol_name = generate_col_name()
    global_data.tvcol_name = generate_col_name()
    global_data.cluster = config.getoption("cluster")
    global_data.complete = config.getoption("complete")
    global_data.replication = config.getoption("replication")
    global_data.enterprise = config.getoption("enterprise")
    global_data.secret = config.getoption("secret")
    global_data.root_password = config.getoption("passwd")


@pytest.fixture(autouse=True)
def mock_formatters(monkeypatch):
    def mock_verify_format(body, result):
        body.pop("error", None)
        body.pop("code", None)
        result.pop("edge", None)
        if len(body) != len(result):
            before = sorted(body, key=lambda x: x.strip("_"))
            after = sorted(result, key=lambda x: x.strip("_"))
            raise ValueError(f"\nIN: {before}\nOUT: {after}")
        return result

    monkeypatch.setattr(formatter, "verify_format", mock_verify_format)


@pytest.fixture(scope="session")
async def client():
    client = ArangoClient(hosts=[global_data.url, global_data.url, global_data.url])
    yield client
    await client.close()


@pytest.fixture(scope="session")
async def sys_db(client):
    sys_db = await client.db(
        name="_system",
        username="root",
        password=global_data.root_password,
        # superuser_token=generate_jwt(global_data.secret),
    )

    # create test database
    await sys_db.create_database(
        name=global_data.db_name,
        users=[
            {
                "active": True,
                "username": global_data.username,
                "password": global_data.password,
            }
        ]
    )

    yield sys_db

    # Remove all test async jobs.
    await sys_db.clear_async_jobs()

    # Remove all test tasks.
    for task in (await sys_db.tasks()):
        task_name = task["name"]
        if task_name.startswith("test_task"):
            await sys_db.delete_task(task_name, ignore_missing=True)

    # Remove all test users.
    for user in (await sys_db.users()):
        username = user["username"]
        if username.startswith("test_user"):
            await sys_db.delete_user(username, ignore_missing=True)

    # Remove all test databases.
    for db_name in (await sys_db.databases()):
        if db_name.startswith("test_database"):
            await sys_db.delete_database(db_name, ignore_missing=True)

    # Remove all test collections.
    for collection in (await sys_db.collections()):
        col_name = collection["name"]
        if col_name.startswith("test_collection"):
            await sys_db.delete_collection(col_name, ignore_missing=True)

    # # Remove all backups.
    if global_data.enterprise:
        for backup_id in (await sys_db.backup.get())["list"].keys():
            await sys_db.backup.delete(backup_id)


@pytest.fixture(scope="session")
async def db(sys_db, client):
    tst_db = await client.db(global_data.db_name, global_data.username, global_data.password)

    # Create a standard collection for testing.
    tst_col = await tst_db.create_collection(global_data.col_name, edge=False)
    await tst_col.add_skiplist_index(["val"])
    await tst_col.add_fulltext_index(["text"])
    geo_index = await tst_col.add_geo_index(["loc"])
    global_data.geo_index = geo_index

    # Create a legacy edge collection for testing.
    await tst_db.create_collection(global_data.icol_name, edge=True)

    # Create test vertex & edge collections and graph.
    tst_graph = await tst_db.create_graph(global_data.graph_name)
    await tst_graph.create_vertex_collection(global_data.fvcol_name)
    await tst_graph.create_vertex_collection(global_data.tvcol_name)
    await tst_graph.create_edge_definition(
        edge_collection=global_data.ecol_name,
        from_vertex_collections=[global_data.fvcol_name],
        to_vertex_collections=[global_data.tvcol_name],
    )

    return tst_db


@pytest.fixture(scope="session")
async def bad_db(client):
    return await client.db(global_data.bad_db_name, global_data.username, global_data.password)


@pytest.fixture(scope="session")
def conn(db):
    return getattr(db, "_conn")


@pytest.fixture(scope="function")
async def col(db: Database):
    collection = db.collection(global_data.col_name)
    await empty_collection(collection)
    return collection


@pytest.fixture(scope="function")
async def bad_col(bad_db: Database):
    return bad_db.collection(global_data.col_name)


@pytest.fixture(scope="function")
async def geo(db: Database):
    return global_data.geo_index


@pytest.fixture(scope="function")
async def icol(db: Database):
    collection = db.collection(global_data.icol_name)
    await empty_collection(collection)
    return collection


@pytest.fixture(scope="function")
async def graph(db: Database):
    return db.graph(global_data.graph_name)


@pytest.fixture()
async def bad_graph(bad_db: Database):
    return bad_db.graph(global_data.graph_name)


# noinspection PyShadowingNames
@pytest.fixture()
async def fvcol(graph: Graph):
    collection = graph.vertex_collection(global_data.fvcol_name)
    await empty_collection(collection)
    return collection


# noinspection PyShadowingNames
@pytest.fixture()
async def tvcol(graph: Graph):
    collection = graph.vertex_collection(global_data.tvcol_name)
    await empty_collection(collection)
    return collection


# noinspection PyShadowingNames
@pytest.fixture()
async def bad_fvcol(bad_graph: Graph):
    return bad_graph.vertex_collection(global_data.fvcol_name)


# noinspection PyShadowingNames
@pytest.fixture()
async def ecol(graph: Graph):
    collection = graph.edge_collection(global_data.ecol_name)
    await empty_collection(collection)
    return collection


# noinspection PyShadowingNames
@pytest.fixture()
async def bad_ecol(bad_graph: Graph, ):
    return bad_graph.edge_collection(global_data.ecol_name)


@pytest.fixture()
def url():
    return global_data.url


@pytest.fixture()
def username():
    return global_data.username


@pytest.fixture()
def password():
    return global_data.password


@pytest.fixture()
def cluster():
    return global_data.cluster


@pytest.fixture()
def replication():
    return global_data.replication


@pytest.fixture()
def secret():
    return global_data.secret


@pytest.fixture()
def root_password():
    return global_data.root_password


@pytest.fixture()
def enterprise():
    return global_data.enterprise


@pytest.fixture()
def db_name():
    return global_data.db_name


@pytest.fixture()
def docs():
    return [
        {"_key": "1", "val": 1, "text": "foo", "loc": [1, 1]},
        {"_key": "2", "val": 2, "text": "foo", "loc": [2, 2]},
        {"_key": "3", "val": 3, "text": "foo", "loc": [3, 3]},
        {"_key": "4", "val": 4, "text": "bar", "loc": [4, 4]},
        {"_key": "5", "val": 5, "text": "bar", "loc": [5, 5]},
        {"_key": "6", "val": 6, "text": "bar", "loc": [5, 5]},
    ]


@pytest.fixture()
def fvdocs():
    return [
        {"_key": "1", "val": 1},
        {"_key": "2", "val": 2},
        {"_key": "3", "val": 3},
    ]


@pytest.fixture()
def tvdocs():
    return [
        {"_key": "4", "val": 4},
        {"_key": "5", "val": 5},
        {"_key": "6", "val": 6},
    ]


@pytest.fixture()
def edocs():
    fv = global_data.fvcol_name
    tv = global_data.tvcol_name
    return [
        {"_key": "1", "_from": f"{fv}/1", "_to": f"{tv}/4"},
        {"_key": "2", "_from": f"{fv}/1", "_to": f"{tv}/5"},
        {"_key": "3", "_from": f"{fv}/6", "_to": f"{tv}/2"},
        {"_key": "4", "_from": f"{fv}/8", "_to": f"{tv}/7"},
    ]
