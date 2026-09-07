"""예외 계층·비민감 메시지 (P5, NFR-4)."""

from __future__ import annotations

from aegis.contracts.errors import (
    ContractError,
    EvidenceRejectedError,
    InvalidEnumError,
    SchemaVersionError,
    UnknownFieldError,
)


def test_all_derive_from_contract_error() -> None:
    for cls in (
        SchemaVersionError,
        UnknownFieldError,
        InvalidEnumError,
        EvidenceRejectedError,
    ):
        assert issubclass(cls, ContractError)


def test_contract_error_is_exception() -> None:
    assert issubclass(ContractError, Exception)
