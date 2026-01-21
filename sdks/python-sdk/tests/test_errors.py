from xmtp.errors import (
    AccountAlreadyAssociatedError,
    ClientNotInitializedError,
    CodecNotFoundError,
    DatabaseOpenError,
    InboxReassignError,
    InvalidGroupMembershipChangeError,
    MissingContentTypeError,
    NotImplementedXmtpError,
    SignerUnavailableError,
    StreamFailedError,
    StreamInvalidRetryAttemptsError,
)


def test_error_messages() -> None:
    assert 'Codec not found' in str(CodecNotFoundError('text'))
    assert 'Content type is required' in str(MissingContentTypeError())
    assert 'Signer unavailable' in str(SignerUnavailableError())
    assert 'Client not initialized' in str(ClientNotInitializedError())
    assert 'Account already associated' in str(AccountAlreadyAssociatedError('inbox'))
    assert 'allow_inbox_reassign' in str(InboxReassignError())
    assert 'Stream failed' in str(StreamFailedError(2))
    assert '1 time' in str(StreamFailedError(1))
    assert 'Stream retry attempts' in str(StreamInvalidRetryAttemptsError())
    assert isinstance(NotImplementedXmtpError(), Exception)
    assert 'Invalid group membership change' in str(InvalidGroupMembershipChangeError('msg'))


def test_database_open_error_without_optional_details() -> None:
    error = DatabaseOpenError(None)
    message = str(error)

    assert 'Failed to open the local XMTP database.' in message
    assert 'Path:' not in message
    assert 'Root error:' not in message
