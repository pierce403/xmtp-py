Python SDK
==========

Key management tips
-------------------

- Store private keys outside source control (env vars or a secrets manager).
- Keep ``XMTP_DB_ENCRYPTION_KEY`` and your database path stable between runs.
- Use a custom signer implementation for hardware wallets or KMS.

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
