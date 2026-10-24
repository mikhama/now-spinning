"""Shared NFC exceptions; re-exported by lib.nfc for public compatibility."""


class NfcError(Exception):
    """Raised on NFC transport, protocol, read/write, or RF lifecycle failure."""


class NfcNoCard(NfcError):
    """Raised when valid detection replies found no card within the timeout."""
