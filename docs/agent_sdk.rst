Agent SDK
=========

Key management tips
-------------------

- ``create_user()`` generates a new in-memory key; persist it if you want a stable inbox.
- ``XMTP_WALLET_KEY`` should be provided via env vars or a secrets manager.
- Preserve the database directory to avoid extra installations.
- ``XMTP_DB_ENCRYPTION_KEY`` is optional; set it only when using an encrypted
  local database, and keep it stable once set.

Local database workflow
-----------------------

Use a stable ``XMTP_DB_DIRECTORY`` or ``ClientOptions.db_path`` for agents that
must keep the same installation. To wipe a disposable dev agent, stop it and
delete the matching ``.db3``, ``.db3-wal``, and ``.db3-shm`` files. For
production, back up the wallet key, database files, and optional encryption key
together.

Configuration & troubleshooting
-------------------------------

- Override endpoints with ``XMTP_API_URL``, ``XMTP_HISTORY_SYNC_URL``, or ``XMTP_GATEWAY_HOST``.
- History sync is disabled by default. Set ``disable_history_sync=False`` (and optionally
  ``history_sync_url``) to enable it.
- Set ``XMTP_DISABLE_HISTORY_SYNC=1`` if the history sync endpoint returns gRPC errors.
- Set ``XMTP_RUST_LOG=error`` (or pass ``rust_log="error"``) to reduce Rust logs.

.. automodule:: xmtp_agent.agent
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.context
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.filters
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.middleware
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.command_router
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.user
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.name_resolver
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.attachments
   :members:
   :undoc-members:

.. automodule:: xmtp_agent.debug
   :members:
   :undoc-members:
