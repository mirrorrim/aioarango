from abc import ABC, abstractmethod
from typing import MutableMapping, Optional, Tuple

import httpx

from aioarango.response import Response
from aioarango.typings import Headers


class HTTPClient(ABC):  # pragma: no cover
    """Abstract base class for HTTP clients."""

    @abstractmethod
    def create_session(self, host: str) -> httpx.AsyncClient:
        """Return a new requests session given the host URL.

        This method must be overridden by the user.

        :param host: ArangoDB host URL.
        :type host: str
        :returns: httpx client object.
        :rtype: httpx.AsyncClient
        """
        raise NotImplementedError

    @abstractmethod
    async def send_request(
        self,
        session: httpx.AsyncClient,
        method: str,
        url: str,
        headers: Optional[Headers] = None,
        params: Optional[MutableMapping[str, str]] = None,
        data: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
    ) -> Response:
        """Send an HTTP request.

        This method must be overridden by the user.

        :param session: httpx session object.
        :type session: httpx.AsyncClient
        :param method: HTTP method in lowercase (e.g. "post").
        :type method: str
        :param url: Request URL.
        :type url: str
        :param headers: Request headers.
        :type headers: dict
        :param params: URL (query) parameters.
        :type params: dict
        :param data: Request payload.
        :type data: str | None
        :param auth: Username and password.
        :type auth: tuple
        :returns: HTTP response.
        :rtype: aioarango.response.Response
        """
        raise NotImplementedError


class DefaultHTTPClient(HTTPClient):
    """Default HTTP client implementation."""

    REQUEST_TIMEOUT = 60
    RETRY_ATTEMPTS = 3

    def create_session(self, host: str, verify: bool = True) -> httpx.AsyncClient:
        """Create and return a new session/connection.

        :param host: ArangoDB host URL.
        :type host: str | unicode
        :returns: httpx client object
        :rtype: httpx.AsyncClient
        """
        transport = httpx.AsyncHTTPTransport(retries=self.RETRY_ATTEMPTS, verify=verify)
        return httpx.AsyncClient(transport=transport)

    async def send_request(
        self,
        session: httpx.AsyncClient,
        method: str,
        url: str,
        headers: Optional[Headers] = None,
        params: Optional[MutableMapping[str, str]] = None,
        data: Optional[str] = None,
        auth: Optional[Tuple[str, str]] = None,
    ) -> Response:
        """Send an HTTP request.

        :param session: httpx client object.
        :type session: httpx.AsyncClient
        :param method: HTTP method in lowercase (e.g. "post").
        :type method: str
        :param url: Request URL.
        :type url: str
        :param headers: Request headers.
        :type headers: dict
        :param params: URL (query) parameters.
        :type params: dict
        :param data: Request payload.
        :type data: str | None
        :param auth: Username and password.
        :type auth: tuple
        :returns: HTTP response.
        :rtype: aioarango.response.Response
        """
        response = await session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            auth=auth,
            timeout=self.REQUEST_TIMEOUT,
        )
        return Response(
            method=method,
            url=str(response.url),
            headers=response.headers,
            status_code=response.status_code,
            status_text=response.reason_phrase,
            raw_body=response.text,
        )
