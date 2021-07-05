Backups
-------

Backups are near consistent snapshots of an entire ArangoDB service including
databases, collections, indexes, views and users. For more information, refer
to `ArangoDB manual`_.

.. _ArangoDB manual: https://docs.arangodb.com

**Example:**

.. code-block:: python

    from aioarango import ArangoClient

    # Initialize the ArangoDB client.
    client = ArangoClient()

    # Connect to "_system" database as root user.
    sys_db = await client.db(
        '_system',
        username='root',
        password='passwd',
        auth_method='jwt'
    )

    # Get the backup API wrapper.
    backup = sys_db.backup

    # Create a backup.
    result = await backup.create(
        label='foo',
        allow_inconsistent=True,
        force=False,
        timeout=1000
    )
    backup_id = result['backup_id']

    # Retrieve details on all backups
    await backup.get()

    # Retrieve details on a specific backup.
    await backup.get(backup_id=backup_id)

    # Upload a backup to a remote repository.
    result = await backup.upload(
        backup_id=backup_id,
        repository='local://tmp/backups',
        config={'local': {'type': 'local'}}
    )
    upload_id = result['upload_id']

    # Get status of an upload.
    await backup.upload(upload_id=upload_id)

    # Abort an upload.
    await backup.upload(upload_id=upload_id, abort=True)

    # Download a backup from a remote repository.
    result = await backup.download(
        backup_id=backup_id,
        repository='local://tmp/backups',
        config={'local': {'type': 'local'}}
    )
    download_id = result['download_id']

    # Get status of an download.
    await backup.download(download_id=download_id)

    # Abort an download.
    await backup.download(download_id=download_id, abort=True)

    # Restore from a backup.
    await backup.restore(backup_id)

    # Delete a backup.
    await backup.delete(backup_id)

See :ref:`Backup` for API specification.
