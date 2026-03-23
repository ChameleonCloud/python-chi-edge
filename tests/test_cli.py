from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from chi_edge.cli import cli, doni_client

FAKE_DEVICE = {
    "created_at": "2022-03-01T00:34:16+00:00",
    "hardware_type": "device.balena",
    "name": "iot-rpi4-01",
    "project_id": "a5f0758da4a5404bbfcef0a64206614c",
    "properties": {
        "machine_name": "raspberrypi4-64",
        "contact_email": "test@example.com",
    },
    "updated_at": "2025-09-30T21:56:48+00:00",
    "uuid": "b3437b33-048d-4809-ad7e-7b8d186195a4",
    "workers": [
        {
            "worker_type": "balena",
            "state": "STEADY",
            "state_details": {
                "device_api_key": "fake",
                "device_id": 6217514,
                "fleet_id": 1918419,
                "last_seen": "2025-11-07T17:29:43+00:00",
            },
        },
        {
            "worker_type": "blazar.device",
            "state": "STEADY",
            "state_details": {
                "blazar_resource_id": "b0e2988c-4d81-4433-a583-8ffbefd14742",
            },
        },
        {
            "worker_type": "tunelo",
            "state": "STEADY",
            "state_details": {
                "channels": {
                    "user": {
                        "endpoint": None,
                        "ip": "10.0.3.200",
                        "uuid": "c94581ff-223a-4ee7-963d-2e4d68c02d5e",
                    }
                }
            },
        },
        {
            "worker_type": "k8s",
            "state": "STEADY",
            "state_details": {
                "created_token_secrets": 0,
                "num_labels": 2,
            },
        },
    ],
}


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
    with patch("chi_edge.cli.openstack") as mock_os:
        mock_os.connect.return_value = MagicMock()
        client = doni_client()
        assert client.service_type == "inventory"
        assert client.interface == "public"


def test_device_list():
    mock_adapter = MagicMock()
    mock_adapter.get.return_value.json.return_value = {
        "hardware": [FAKE_DEVICE]
    }

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(cli, ["device", "list"])
        assert result.exit_code == 0, result.output
        assert "iot-rpi4-01" in result.output


def test_device_show():
    mock_adapter = MagicMock()
    mock_adapter.get.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(cli, ["device", "show", FAKE_DEVICE["uuid"]])
        assert result.exit_code == 0, result.output
        assert "iot-rpi4-01" in result.output
        assert "raspberrypi4-64" in result.output
