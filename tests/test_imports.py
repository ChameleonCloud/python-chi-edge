def test_package_imports():
    from chi_edge import SUPPORTED_MACHINE_NAMES, LOCAL_EGRESS

    assert "raspberrypi4-64" in SUPPORTED_MACHINE_NAMES
    assert "allow" in LOCAL_EGRESS


def test_utils_import():
    from chi_edge.utils import validate_rfc1123_name

    assert callable(validate_rfc1123_name)
