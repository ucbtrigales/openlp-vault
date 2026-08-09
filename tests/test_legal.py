import pytest

from openlp_vault.legal import PROJECT_URL, read_legal_document


def test_legal_documents_are_available():
    assert "GNU GENERAL PUBLIC LICENSE" in read_legal_document("LICENSE")
    notice = read_legal_document("NOTICE")
    assert "Copyright (C) 2026 Christian González G." in notice
    assert PROJECT_URL in notice


def test_unknown_legal_document_is_rejected():
    with pytest.raises(ValueError):
        read_legal_document("UNKNOWN")
