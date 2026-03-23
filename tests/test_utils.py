from chi_edge.utils import validate_rfc1123_name


def test_valid_names():
    assert validate_rfc1123_name("my-device-01")
    assert validate_rfc1123_name("a1")
    assert validate_rfc1123_name("device.lab.local")


def test_invalid_names():
    assert not validate_rfc1123_name("-starts-with-dash")
    assert not validate_rfc1123_name("ends-with-dash-")
    assert not validate_rfc1123_name("UPPERCASE")
    assert not validate_rfc1123_name("has spaces")


def test_single_char():
    # single char is too short for the regex (needs at least 2)
    assert not validate_rfc1123_name("a")
