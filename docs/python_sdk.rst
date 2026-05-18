Python SDK
==========

Key management tips
-------------------

- Store private keys outside source control (env vars or a secrets manager).
- Keep your database path stable between runs.
- ``XMTP_DB_ENCRYPTION_KEY`` is optional; set it only for encrypted local databases,
  and keep it stable once set.
- Use a custom signer implementation for hardware wallets or KMS.

Local database workflow
-----------------------

``db_path="auto"`` stores ``xmtp-<env>-<inbox_id>.db3`` in the current working
directory. SQLite can also create ``.db3-wal`` and ``.db3-shm`` sidecars; keep
or delete those files together.

For development, use a dev-only ``XMTP_DB_DIRECTORY`` or ``ClientOptions.db_path``.
To wipe a dev installation, stop the client and delete the matching database and
sidecar files. For production, preserve the wallet key, database files, and
optional encryption key together so the same XMTP installation is reused.

Configuration & troubleshooting
-------------------------------

- Override endpoints with ``XMTP_API_URL``, ``XMTP_HISTORY_SYNC_URL``, or ``XMTP_GATEWAY_HOST``.
- History sync is disabled by default. Set ``disable_history_sync=False`` (and optionally
  ``history_sync_url``) to enable it.
- Set ``XMTP_DISABLE_HISTORY_SYNC=1`` if the history sync endpoint returns gRPC errors.
- Set ``XMTP_RUST_LOG=error`` (or pass ``rust_log="error"``) to reduce Rust logs.

.. automodule:: xmtp.client
   :members:
   :undoc-members:

.. automodule:: xmtp.conversations
   :members:
   :undoc-members:

.. automodule:: xmtp.conversation
   :members:
   :undoc-members:

.. automodule:: xmtp.messages
   :members:
   :undoc-members:

.. automodule:: xmtp.preferences
   :members:
   :undoc-members:

.. automodule:: xmtp.types
   :members:
   :undoc-members:

.. automodule:: xmtp.signers
   :members:
   :undoc-members:

.. automodule:: xmtp.env
   :members:
   :undoc-members:
