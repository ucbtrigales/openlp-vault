import openlp_vault


def test_package_importable():
    assert hasattr(openlp_vault, "__version__")
