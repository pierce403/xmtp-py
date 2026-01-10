Migration Guide (xmtp-js -> xmtp-py)
===================================

This SDK mirrors the xmtp-js APIs with Python-idiomatic conventions.

Key differences
---------------

- JavaScript ``camelCase`` becomes Python ``snake_case``.
- Async APIs use ``async``/``await`` and ``pytest-asyncio`` for tests.
- Options are passed as ``ClientOptions`` rather than plain objects.

Common mappings
---------------

+-----------------------------+----------------------------------+
| xmtp-js                     | xmtp-py                          |
+=============================+==================================+
| ``Client.create(...)``      | ``await Client.create(...)``     |
+-----------------------------+----------------------------------+
| ``newDm()``                 | ``await new_dm()``               |
+-----------------------------+----------------------------------+
| ``streamAllMessages()``     | ``stream_all_messages()``        |
+-----------------------------+----------------------------------+
| ``inboxId``                 | ``inbox_id``                     |
+-----------------------------+----------------------------------+
| ``ContentTypeId``           | ``ContentTypeId``                |
+-----------------------------+----------------------------------+
