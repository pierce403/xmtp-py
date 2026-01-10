from xmtp.errors import (
    AccountAlreadyAssociatedError,
    ClientNotInitializedError,
    CodecNotFoundError,
    InvalidGroupMembershipChangeError,
    InboxReassignError,
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
