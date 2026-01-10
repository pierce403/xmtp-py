Test parity map
===============

This document maps xmtp-js test suites to their Python equivalents. Where
features are not yet implemented in Python or require networked integration,
we note the gap explicitly.

Content types
-------------

- ``content-type-primitives/src/index.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py``
- ``content-type-text/src/Text.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py``
- ``content-type-markdown/src/Markdown.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py``
- ``content-type-reaction/src/Reaction.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (unit coverage)
- ``content-type-read-receipt/src/ReadReceipt.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (unit coverage)
- ``content-type-reply/src/Reply.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (unit coverage)
- ``content-type-remote-attachment/src/Attachment.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (unit coverage)
- ``content-type-remote-attachment/src/RemoteAttachment.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (metadata encode/decode)
- ``content-type-group-updated/src/GroupUpdated.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (decode only; encode unavailable)
- ``content-type-transaction-reference/src/TransactionReference.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (unit coverage)
- ``content-type-wallet-send-calls/src/WalletSendCalls.test.ts`` -> ``sdks/python-sdk/tests/test_content_types.py`` (unit coverage)

Notes:

- Remote attachment encryption/load helpers are not implemented in Python yet
  (no bindings support). Tests cover metadata encode/decode and https validation.
- GroupUpdated encode is not available in bindings; decode path is tested.

Node SDK
--------

- ``AsyncStream.test.ts`` -> ``sdks/python-sdk/tests/test_async_stream.py``
- ``Client.test.ts`` -> ``sdks/python-sdk/tests/test_client.py`` (unit wrapper coverage)
- ``Conversation.test.ts`` -> ``sdks/python-sdk/tests/test_conversation.py``
- ``Conversations.test.ts`` -> ``sdks/python-sdk/tests/test_conversations.py``
- ``Preferences.test.ts`` -> ``sdks/python-sdk/tests/test_preferences.py``
- ``DebugInformation.test.ts`` -> not applicable (no Python debug info helpers)
- ``validation.test.ts`` -> ``sdks/python-sdk/tests/test_utils.py``
- ``inboxId.test.ts`` -> ``sdks/python-sdk/tests/test_client.py`` (inbox ID generation in init)

Agent SDK
---------

- ``core/Agent.test.ts`` -> ``sdks/agent-sdk/tests/test_agent.py``
- ``core/MessageContext.test.ts`` -> ``sdks/agent-sdk/tests/test_context.py``
- ``core/filter.test.ts`` -> ``sdks/agent-sdk/tests/test_filters.py``
- ``middleware/CommandRouter.test.ts`` -> ``sdks/agent-sdk/tests/test_command_router.py``
- ``util/AttachmentUtil.test.ts`` -> ``sdks/agent-sdk/tests/test_attachments.py`` (download + digest)
- ``user/NameResolver.test.ts`` -> ``sdks/agent-sdk/tests/test_name_resolver.py``

Integration parity
------------------

The JavaScript test suite includes integration tests that exercise live XMTP
services. Python equivalents live in ``sdks/python-sdk/tests/test_integration.py``
(and should be expanded as integration coverage grows). Set
``XMTP_INTEGRATION_TESTS=1`` to run them.
