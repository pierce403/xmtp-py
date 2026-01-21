"""Error types for XMTP."""

from __future__ import annotations


class XmtpError(Exception):
    """Base class for XMTP errors."""


class CodecNotFoundError(XmtpError):
    """Raised when a codec is missing for a content type."""

    def __init__(self, content_type: str) -> None:
        super().__init__(f'Codec not found for "{content_type}" content type')


class MissingContentTypeError(XmtpError):
    """Raised when content type is required but missing."""

    def __init__(self) -> None:
        super().__init__("Content type is required when sending non-text content")


class SignerUnavailableError(XmtpError):
    """Raised when a signer is required but not provided."""

    def __init__(self) -> None:
        super().__init__("Signer unavailable, use Client.create with a signer")


class ClientNotInitializedError(XmtpError):
    """Raised when client is used before initialization."""

    def __init__(self) -> None:
        super().__init__("Client not initialized, use Client.create or Client.build")


class AccountAlreadyAssociatedError(XmtpError):
    """Raised when account is already associated with an inbox."""

    def __init__(self, inbox_id: str) -> None:
        super().__init__(f"Account already associated with inbox {inbox_id}")


class InboxReassignError(XmtpError):
    """Raised when inbox reassignment is disallowed."""

    def __init__(self) -> None:
        super().__init__(
            "Unable to create add account signature text, allow_inbox_reassign must be true"
        )


class StreamFailedError(XmtpError):
    """Raised when a stream fails after retries."""

    def __init__(self, retry_attempts: int) -> None:
        times = "times" if retry_attempts != 1 else "time"
        super().__init__(f"Stream failed, retried {retry_attempts} {times}")


class StreamInvalidRetryAttemptsError(XmtpError):
    """Raised when retry attempts are invalid."""

    def __init__(self) -> None:
        super().__init__("Stream retry attempts must be greater than 0")


class NotImplementedXmtpError(XmtpError):
    """Raised when a feature has not been implemented yet."""


class InvalidGroupMembershipChangeError(XmtpError):
    """Raised when group membership changes are invalid."""

    def __init__(self, message_id: str) -> None:
        super().__init__(f"Invalid group membership change for message {message_id}")


class DatabaseOpenError(XmtpError):
    """Raised when the local XMTP database cannot be opened."""

    def __init__(self, db_path: str | None, detail: str | None = None) -> None:
        message = "Failed to open the local XMTP database."
        if db_path:
            message = f'{message} Path: "{db_path}".'
        message = (
            f"{message} If this is a SQLCipher error, verify that "
            "XMTP_DB_ENCRYPTION_KEY is stable and hex-encoded. "
            "To recover from a bad key or corrupted DB, delete the .db3 file "
            "or point XMTP_DB_DIRECTORY/ClientOptions.db_path to a fresh location."
        )
        if detail:
            message = f"{message} Root error: {detail}"
        super().__init__(message)
