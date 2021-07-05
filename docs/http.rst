HTTP Clients
------------

aioarango lets you define your own HTTP client for sending requests to
ArangoDB server. The default implementation uses the httpx_ library.

Your HTTP client must inherit :class:`aioarango.http.HTTPClient` and implement the
following abstract methods:

* :func:`aioarango.http.HTTPClient.create_session`
* :func:`aioarango.http.HTTPClient.send_request`

The **create_session** method must return a `httpx.AsyncClient`_ instance per
connected host (coordinator). The session objects are stored in the client.

The **send_request** method must use the session to send an HTTP request, and
return a fully populated instance of :class:`aioarango.response.Response`.

For example, let's say your HTTP client needs:

* Automatic retries
* Additional HTTP header called ``x-my-header``
* SSL certificate verification disabled
* Custom logging

Your ``CustomHTTPClient`` class might look something like this:

.. testcode::

    import logging

    from requests.adapters import HTTPAdapter
    from requests import Session
    from requests.packages.urllib3.util.retry import Retry

    from aioarango.response import Response
    from aioarango.http import HTTPClient


    class CustomHTTPClient(HTTPClient):
        """My custom HTTP client with cool features."""

        def __init__(self):
            # Initialize your logger.
            self._logger = logging.getLogger('my_logger')

        def create_session(self, host: str) -> httpx.AsyncClient:
            transport = httpx.AsyncHTTPTransport(retries=3)
            return httpx.AsyncClient(transport=transport)

        async def send_request(
            self,
            session: httpx.AsyncClient,
            method: str,
            url: str,
            headers: Optional[Headers] = None,
            params: Optional[MutableMapping[str, str]] = None,
            data: Union[str, MultipartEncoder, None] = None,
            auth: Optional[Tuple[str, str]] = None,
        ) -> Response:
            # Add your own debug statement.
            self._logger.debug(f'Sending request to {url}')

            # Send a request.
            response = await session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                auth=auth,
                timeout=5, # Use timeout of 5 seconds
            )
            self._logger.debug(f'Got {response.status_code}')

            # Return an instance of aioarango.response.Response.
            return Response(
                method=method,
                url=str(response.url),
                headers=response.headers,
                status_code=response.status_code,
                status_text=response.reason_phrase,
                raw_body=response.text,
            )

Then you would inject your client as follows:

.. code-block:: python

    from aioarango import ArangoClient

    from my_module import CustomHTTPClient

    client = ArangoClient(
        hosts='http://localhost:8529',
        http_client=CustomHTTPClient()
    )

See `httpx.AsyncClient`_ for more details on how to create and manage sessions.

.. _httpx: https://github.com/encode/httpx
.. _httpx.AsyncClient: https://www.python-httpx.org/advanced/#client-instances
