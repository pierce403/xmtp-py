"""Recipient resolution helpers for agents."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from xmtp import Client
from xmtp.bindings import NativeBindings
from xmtp.identifiers import Identifier, IdentifierKind
from xmtp.utils import is_hex_string


@dataclass(slots=True)
class ResolvedRecipient:
    """Resolved recipient details."""

    address: str | None
    inbox_id: str | None
    identifier: Identifier | None


def _normalize_hex(value: str) -> str:
    normalized = value[2:] if value.lower().startswith("0x") else value
    return normalized.lower()


def _normalize_address(value: str) -> str:
    if not is_hex_string(value, length=40):
        raise ValueError(f'Invalid address: "{value}"')
    normalized = value if value.lower().startswith("0x") else f"0x{value}"
    return normalized


def _is_inbox_id(value: str) -> bool:
    return is_hex_string(value, length=64)


def _address_from_inbox_state(state: object) -> str | None:
    identities = []
    recovery = getattr(state, "recovery_identity", None)
    if recovery is not None:
        identities.append(recovery)
    identities.extend(getattr(state, "account_identities", []) or [])

    for identity in identities:
        candidate = getattr(identity, "identifier", None)
        if isinstance(candidate, str) and is_hex_string(candidate, length=40):
            return _normalize_address(candidate)
    return None


async def resolve_recipient(
    client: Client,
    recipient: str | Identifier,
    *,
    name_resolver: Callable[[str], Awaitable[str | None]] | None = None,
    consent_state: NativeBindings.FfiConsentState | None = None,
) -> ResolvedRecipient:
    """Resolve an inbox ID or address for a recipient.

    Args:
        client: XMTP client to use for inbox resolution and consent.
        recipient: Inbox ID, address, ENS name, or Identifier.
        name_resolver: Optional async resolver for non-hex names (e.g. ENS).
        consent_state: Optional consent state to apply to the resolved inbox ID.
    """

    address: str | None = None
    inbox_id: str | None = None
    identifier: Identifier | None = None

    if isinstance(recipient, Identifier):
        identifier = recipient
        if identifier.kind == IdentifierKind.ETHEREUM:
            address = _normalize_address(identifier.value)
            identifier = Identifier(kind=IdentifierKind.ETHEREUM, value=address)
        inbox_id = await client.get_inbox_id_by_identifier(identifier)
        if inbox_id is None:
            raise ValueError(f'No inbox id found for identifier "{identifier.value}"')
    else:
        target = recipient.strip()
        if _is_inbox_id(target):
            inbox_id = _normalize_hex(target)
            try:
                state = await client.preferences.get_latest_inbox_state(inbox_id)
            except Exception:
                state = None
            if state is not None:
                address = _address_from_inbox_state(state)
                if address:
                    identifier = Identifier(kind=IdentifierKind.ETHEREUM, value=address)
        else:
            if is_hex_string(target, length=40):
                address = _normalize_address(target)
            else:
                if name_resolver is None:
                    raise ValueError("Name resolver required for non-hex recipient")
                resolved = await name_resolver(target)
                if resolved is None:
                    raise ValueError(f'Could not resolve address for "{target}"')
                address = _normalize_address(resolved)
            identifier = Identifier(kind=IdentifierKind.ETHEREUM, value=address)
            inbox_id = await client.get_inbox_id_by_identifier(identifier)
            if inbox_id is None:
                raise ValueError(f'No inbox id found for address "{address}"')

    if consent_state is not None:
        record = NativeBindings.FfiConsent(
            entity_type=NativeBindings.FfiConsentEntityType.INBOX_ID,
            state=consent_state,
            entity=inbox_id,
        )
        await client.preferences.set_consent_states([record])

    return ResolvedRecipient(address=address, inbox_id=inbox_id, identifier=identifier)


__all__ = ["ResolvedRecipient", "resolve_recipient"]
