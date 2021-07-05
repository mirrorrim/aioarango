import pytest

from aioarango.collection import StandardCollection
from aioarango.database import StandardDatabase, TransactionDatabase
from aioarango.exceptions import (
    TransactionAbortError,
    TransactionCommitError,
    TransactionExecuteError,
    TransactionInitError,
    TransactionStatusError,
)
from aioarango.graph import Graph
from tests.helpers import extract

pytestmark = pytest.mark.asyncio


async def test_transaction_execute_raw(
    db: StandardDatabase, col: StandardCollection, docs
):
    # Test execute raw transaction
    doc = docs[0]
    key = doc["_key"]
    result = await db.execute_transaction(
        command=f"""
        function (params) {{
            var db = require('internal').db;
            db.{col.name}.save({{'_key': params.key, 'val': 1}});
            return true;
        }}
        """,
        params={"key": key},
        write=[col.name],
        read=[col.name],
        sync=False,
        timeout=1000,
        max_size=100000,
        allow_implicit=True,
        intermediate_commit_count=10,
        intermediate_commit_size=10000,
    )
    assert result is True
    assert col.has(doc, check_rev=False) and (await col.get(key))["val"] == 1

    # Test execute invalid transaction
    with pytest.raises(TransactionExecuteError) as err:
        await db.execute_transaction(command="INVALID COMMAND")
    assert err.value.error_code == 10


async def test_transaction_init(
    db: StandardDatabase, bad_db: StandardDatabase, col: StandardCollection, username
):
    txn_db = await db.begin_transaction()

    assert isinstance(txn_db, TransactionDatabase)
    assert txn_db.username == username
    assert txn_db.context == "transaction"
    assert txn_db.db_name == db.name
    assert txn_db.name == db.name
    assert txn_db.transaction_id is not None
    assert repr(txn_db) == f"<TransactionDatabase {db.name}>"

    txn_col = txn_db.collection(col.name)
    assert txn_col.username == username
    assert txn_col.context == "transaction"
    assert txn_col.db_name == db.name

    txn_aql = txn_db.aql
    assert txn_aql.username == username
    assert txn_aql.context == "transaction"
    assert txn_aql.db_name == db.name

    with pytest.raises(TransactionInitError) as err:
        await bad_db.begin_transaction()
    assert err.value.error_code in {11, 1228}


async def test_transaction_status(db: StandardDatabase, col: StandardCollection, docs):
    txn_db = await db.begin_transaction(read=col.name)
    assert await txn_db.transaction_status() == "running"

    await txn_db.commit_transaction()
    assert await txn_db.transaction_status() == "committed"

    txn_db = await db.begin_transaction(read=col.name)
    assert await txn_db.transaction_status() == "running"

    await txn_db.abort_transaction()
    assert await txn_db.transaction_status() == "aborted"

    # Test transaction_status with an illegal transaction ID
    txn_db._executor._id = "illegal"
    with pytest.raises(TransactionStatusError) as err:
        await txn_db.transaction_status()
    assert err.value.error_code in {10, 1655}


async def test_transaction_commit(db: StandardDatabase, col: StandardCollection, docs):
    txn_db = await db.begin_transaction(
        read=col.name,
        write=col.name,
        exclusive=[],
        sync=True,
        allow_implicit=False,
        lock_timeout=1000,
        max_size=10000,
    )
    txn_col = txn_db.collection(col.name)

    assert "_rev" in await txn_col.insert(docs[0])
    assert "_rev" in await txn_col.delete(docs[0])
    assert "_rev" in await txn_col.insert(docs[1])
    assert "_rev" in await txn_col.delete(docs[1])
    assert "_rev" in await txn_col.insert(docs[2])
    await txn_db.commit_transaction()

    assert extract("_key", [doc async for doc in await col.all()]) == [docs[2]["_key"]]
    assert await txn_db.transaction_status() == "committed"

    # Test commit_transaction with an illegal transaction ID
    txn_db._executor._id = "illegal"
    with pytest.raises(TransactionCommitError) as err:
        await txn_db.commit_transaction()
    assert err.value.error_code in {10, 1655}


async def test_transaction_abort(db: StandardDatabase, col: StandardCollection, docs):
    txn_db = await db.begin_transaction(write=col.name)
    txn_col = txn_db.collection(col.name)

    assert "_rev" in await txn_col.insert(docs[0])
    assert "_rev" in await txn_col.delete(docs[0])
    assert "_rev" in await txn_col.insert(docs[1])
    assert "_rev" in await txn_col.delete(docs[1])
    assert "_rev" in await txn_col.insert(docs[2])
    await txn_db.abort_transaction()

    assert extract("_key", [doc async for doc in await col.all()]) == []
    assert await txn_db.transaction_status() == "aborted"

    txn_db._executor._id = "illegal"
    with pytest.raises(TransactionAbortError) as err:
        await txn_db.abort_transaction()
    assert err.value.error_code in {10, 1655}


async def test_transaction_graph(db: StandardDatabase, graph: Graph, fvcol, fvdocs):
    col_names = [
        c["name"] for c in await db.collections() if c["name"].startswith("test")
    ]
    txn_db = await db.begin_transaction(write=col_names)
    vcol = txn_db.graph(graph.name).vertex_collection(fvcol.name)

    await vcol.insert(fvdocs[0])
    assert await vcol.count() == 1

    await vcol.delete(fvdocs[0])
    assert await vcol.count() == 0

    await txn_db.commit_transaction()
