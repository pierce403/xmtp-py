Python SDK
==========

Key management tips
-------------------

- Store private keys outside source control (env vars or a secrets manager).
- Keep ``XMTP_DB_ENCRYPTION_KEY`` and your database path stable between runs.
- Use a custom signer implementation for hardware wallets or KMS.

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
