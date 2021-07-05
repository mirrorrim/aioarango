Schema Validation
-----------------

ArangoDB supports document validation using JSON schemas. You can use this
feature by providing a schema during collection creation using the ``schema``
parameter.

**Example:**

.. testcode::

    from aioarango import ArangoClient

    # Initialize the ArangoDB client.
    client = ArangoClient()

    # Connect to "test" database as root user.
    db = await client.db('test', username='root', password='passwd')

    if await db.has_collection('employees'):
        await db.delete_collection('employees')

    # Create a new collection named "employees" with custom schema.
    my_schema = {
        'rule': {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'email': {'type': 'string'}
            },
            'required': ['name', 'email']
        },
        'level': 'moderate',
        'message': 'Schema Validation Failed.'
    }
    await employees = db.create_collection(name='employees', schema=my_schema)

    # Modify the schema.
    await employees.configure(schema=my_schema)

    # Remove the schema.
    await employees.configure(schema={})
