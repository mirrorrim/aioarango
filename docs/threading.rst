Multithreading
--------------

There are a few things you should consider before using aioarango in a
multithreaded (or multiprocess) architecture.

Stateful Objects
================

Instances of the following classes are considered *stateful*, and should not be
accessed across multiple threads without locks in place:

* :ref:`BatchDatabase` (see :doc:`batch`)
* :ref:`BatchJob` (see :doc:`batch`)
* :ref:`Cursor` (see :doc:`cursor`)


HTTP Sessions
=============

When :ref:`ArangoClient` is initialized, a `httpx.AsyncClient`_ instance is
created per ArangoDB host connected. HTTP requests to a host are sent using
only its corresponding session. For more information on how to override this
behaviour, see :doc:`http`.

Note that a `httpx.AsyncClient`_ object may not always be thread-safe. Always
research your use case!

.. _httpx.AsyncClient: https://www.python-httpx.org/advanced/#client-instances
