from typing import TypeVar, Union

from aioarango.job import AsyncJob, BatchJob

T = TypeVar("T")

Result = Union[T, AsyncJob[T], BatchJob[T], None]
