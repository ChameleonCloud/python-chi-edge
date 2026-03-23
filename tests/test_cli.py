from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from chi_edge.cli import cli, doni_client


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "CHI@Edge" in result.output


def test_device_group_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["device", "--help"])
    assert result.exit_code == 0
    assert "register" in result.output


def test_doni_client_returns_adapter():
    with patch("chi_edge.cli.chi") as mock_chi:
        mock_chi.session.return_value = MagicMock()
        client = doni_client()
        assert client.service_type == "inventory"
        assert client.interface == "public"
        mock_chi.session.assert_called_once()
