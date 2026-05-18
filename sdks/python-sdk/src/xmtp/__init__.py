"""XMTP Python SDK (unofficial)."""

from xmtp.client import Client
from xmtp.conversation import Conversation, Dm, Group
from xmtp.conversations import Conversations
from xmtp.env import load_client_options_from_env, load_signer_from_env
from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.messages import DecodedMessage
from xmtp.preferences import Preferences
from xmtp.types import ClientOptions, LogLevel, XmtpEnv
from xmtp.version import __version__

try:
    from xmtp.bindings import get_bindings_version
except ImportError:  # pragma: no cover - import guard
    __bindings_version__ = None
else:
    __bindings_version__ = get_bindings_version()

__all__ = [
    "__bindings_version__",
    "__version__",
    "Client",
    "ClientOptions",
    "Conversation",
    "Conversations",
    "DecodedMessage",
    "Dm",
    "Group",
    "Identifier",
    "IdentifierKind",
    "LogLevel",
    "load_client_options_from_env",
    "load_signer_from_env",
    "Preferences",
    "XmtpEnv",
]
