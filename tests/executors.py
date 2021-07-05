import asyncio

from aioarango.executor import AsyncApiExecutor, BatchApiExecutor, TransactionApiExecutor
from aioarango.job import BatchJob


class TestAsyncApiExecutor(AsyncApiExecutor):
    def __init__(self, connection) -> None:
        super().__init__(connection=connection, return_result=True)

    async def execute(self, request, response_handler):
        job = await AsyncApiExecutor.execute(self, request, response_handler)
        while await job.status() != "done":
            await asyncio.sleep(0.01)
        return await job.result()


class TestBatchExecutor(BatchApiExecutor):
    def __init__(self, connection) -> None:
        super().__init__(connection=connection, return_result=True)

    async def execute(self, request, response_handler):
        self._committed = False
        self._queue.clear()

        job = BatchJob(response_handler)
        self._queue[job.id] = (request, job)
        await self.commit()
        return await job.result()


class TestTransactionApiExecutor(TransactionApiExecutor):

    # noinspection PyMissingConstructor
    def __init__(self, connection) -> None:
        self._conn = connection

    async def execute(self, request, response_handler):
        if request.read is request.write is request.exclusive is None:
            resp = await self._conn.send_request(request)
            return response_handler(resp)

        await self.begin(
            sync=True,
            allow_implicit=False,
            lock_timeout=0,
            read=request.read,
            write=request.write,
            exclusive=request.exclusive,
        )
        result = super().execute(request, response_handler)
        await self.commit()
        return result
