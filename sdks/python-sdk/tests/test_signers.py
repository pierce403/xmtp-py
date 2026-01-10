import pytest

from xmtp.identifiers import IdentifierKind
from xmtp.signers import create_signer
from xmtp.signers.eoa import EoaSigner
from xmtp.signers.scw import ScwSigner
from xmtp.signers.base import SignerType


@pytest.mark.asyncio
async def test_eoa_signer_basic() -> None:
    signer = create_signer('0x' + '1' * 64)
    assert isinstance(signer, EoaSigner)
    assert signer.type == SignerType.EOA

    address = await signer.get_address()
    assert address.startswith('0x')

    identifier = await signer.get_identifier()
    assert identifier.kind == IdentifierKind.ETHEREUM
    assert identifier.value == address

    signature = await signer.sign_message(b'test')
    assert isinstance(signature, bytes)
    assert len(signature) > 0

    with pytest.raises(ValueError, match='EOA signer does not support chain_id'):
        await signer.get_chain_id()
    assert await signer.get_block_number() is None


@pytest.mark.asyncio
async def test_scw_signer_basic() -> None:
    async def sign_message(message: bytes) -> bytes:
        return b'signature:' + message

    signer = ScwSigner('0xabc', sign_message, chain_id=1, block_number=42)
    assert signer.type == SignerType.SCW
    assert await signer.get_address() == '0xabc'
    identifier = await signer.get_identifier()
    assert identifier.value == '0xabc'
    assert await signer.sign_message(b'ping') == b'signature:ping'
    assert await signer.get_chain_id() == 1
    assert await signer.get_block_number() == 42
