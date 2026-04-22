from unittest.mock import patch, MagicMock

from click.testing import CliRunner
from rich.console import Console

from chi_edge.cli import cli

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


# Test the CLI invocation, see:
# https://click.palletsprojects.com/en/stable/api/#click.testing.CliRunner


def test_os_cloud_flag():
    mock_adapter = MagicMock()
    mock_adapter.get.return_value.json.return_value = {"hardware": []}
    with (
        patch("chi_edge.cli.openstack") as mock_os,
        patch("chi_edge.cli.adapter") as mock_adapter_cls,
    ):
        mock_adapter_cls.Adapter.return_value = mock_adapter
        runner = CliRunner()
        result = runner.invoke(cli, ["--os-cloud", "edge", "device", "list"])
        assert result.exit_code == 0, result.output
        mock_os.connect.assert_called_once_with(cloud="edge")


def test_os_cloud_env_var():
    mock_adapter = MagicMock()
    mock_adapter.get.return_value.json.return_value = {"hardware": []}
    with (
        patch("chi_edge.cli.openstack") as mock_os,
        patch("chi_edge.cli.adapter") as mock_adapter_cls,
    ):
        mock_adapter_cls.Adapter.return_value = mock_adapter
        runner = CliRunner(env={"OS_CLOUD": "edge"})
        result = runner.invoke(cli, ["device", "list"])
        assert result.exit_code == 0, result.output
        mock_os.connect.assert_called_once_with(cloud="edge")


def test_device_list():
    mock_adapter = MagicMock()
    mock_adapter.get.return_value.json.return_value = {"hardware": [FAKE_DEVICE]}

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(cli, ["device", "list"])
        assert result.exit_code == 0, result.output
        assert "iot-rpi4-01" in result.output
        assert "Restricted" not in result.output
        assert "Contact" not in result.output


def test_device_list_long_shows_extra_columns():
    restricted = {
        **FAKE_DEVICE,
        "name": "iot-rpi4-restricted",
        "uuid": "11111111-1111-1111-1111-111111111111",
        "properties": {
            **FAKE_DEVICE["properties"],
            "authorized_projects": ["proj-a", "proj-b"],
            "local_egress": "allowed",
        },
    }
    public = {
        **FAKE_DEVICE,
        "name": "iot-rpi4-public",
        "uuid": "22222222-2222-2222-2222-222222222222",
        "properties": {
            k: v
            for k, v in FAKE_DEVICE["properties"].items()
            if k != "authorized_projects"
        },
    }

    mock_adapter = MagicMock()
    mock_adapter.get.return_value.json.return_value = {
        "hardware": [restricted, public],
    }

    runner = CliRunner()
    with (
        patch("chi_edge.cli.doni_client", return_value=mock_adapter),
        patch("chi_edge.cli.console", Console(width=300)),
    ):
        result = runner.invoke(cli, ["device", "list", "--long"])
        assert result.exit_code == 0, result.output
        for header in ("Type", "Restricted to", "Contact", "Local egress"):
            assert header in result.output
        assert "raspberrypi4-64" in result.output
        assert "proj-a" in result.output
        assert "proj-b" in result.output
        assert "public" in result.output
        assert "test@example.com" in result.output
        assert "allowed" in result.output


def test_device_show():
    mock_adapter = MagicMock()
    mock_adapter.get.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(cli, ["device", "show", FAKE_DEVICE["uuid"]])
        assert result.exit_code == 0, result.output
        assert "iot-rpi4-01" in result.output
        assert "raspberrypi4-64" in result.output


def test_device_set_scalar():
    mock_adapter = MagicMock()
    mock_adapter.patch.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(
            cli,
            [
                "device",
                "set",
                FAKE_DEVICE["uuid"],
                "--contact-email",
                "new@example.com",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_adapter.patch.assert_called_once_with(
            f"/v1/hardware/{FAKE_DEVICE['uuid']}/",
            json=[
                {
                    "op": "add",
                    "path": "/properties/contact_email",
                    "value": "new@example.com",
                },
            ],
        )


def test_device_set_authorized_projects_splits_on_comma():
    mock_adapter = MagicMock()
    mock_adapter.patch.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(
            cli,
            [
                "device",
                "set",
                FAKE_DEVICE["uuid"],
                "--authorized-projects",
                "proj-a,proj-b,proj-c",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_adapter.patch.assert_called_once_with(
            f"/v1/hardware/{FAKE_DEVICE['uuid']}/",
            json=[
                {
                    "op": "add",
                    "path": "/properties/authorized_projects",
                    "value": ["proj-a", "proj-b", "proj-c"],
                },
            ],
        )


def test_device_set_no_flags_sends_empty_patch():
    mock_adapter = MagicMock()
    mock_adapter.patch.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(cli, ["device", "set", FAKE_DEVICE["uuid"]])
        assert result.exit_code == 0, result.output
        mock_adapter.patch.assert_called_once_with(
            f"/v1/hardware/{FAKE_DEVICE['uuid']}/",
            json=[],
        )


def test_device_set_unset_single():
    mock_adapter = MagicMock()
    mock_adapter.patch.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(
            cli,
            [
                "device",
                "set",
                FAKE_DEVICE["uuid"],
                "--unset",
                "contact_email",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_adapter.patch.assert_called_once_with(
            f"/v1/hardware/{FAKE_DEVICE['uuid']}/",
            json=[
                {"op": "remove", "path": "/properties/contact_email"},
            ],
        )


def test_device_set_unset_multiple():
    mock_adapter = MagicMock()
    mock_adapter.patch.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(
            cli,
            [
                "device",
                "set",
                FAKE_DEVICE["uuid"],
                "--unset",
                "contact_email",
                "--unset",
                "authorized_projects",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_adapter.patch.assert_called_once_with(
            f"/v1/hardware/{FAKE_DEVICE['uuid']}/",
            json=[
                {"op": "remove", "path": "/properties/contact_email"},
                {"op": "remove", "path": "/properties/authorized_projects"},
            ],
        )


def test_device_set_with_set_and_unset_combined():
    mock_adapter = MagicMock()
    mock_adapter.patch.return_value.json.return_value = FAKE_DEVICE

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(
            cli,
            [
                "device",
                "set",
                FAKE_DEVICE["uuid"],
                "--contact-email",
                "new@example.com",
                "--unset",
                "authorized_projects",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_adapter.patch.assert_called_once_with(
            f"/v1/hardware/{FAKE_DEVICE['uuid']}/",
            json=[
                {
                    "op": "add",
                    "path": "/properties/contact_email",
                    "value": "new@example.com",
                },
                {"op": "remove", "path": "/properties/authorized_projects"},
            ],
        )


def test_device_set_rejects_set_and_unset_of_same_property():
    mock_adapter = MagicMock()

    runner = CliRunner()
    with patch("chi_edge.cli.doni_client", return_value=mock_adapter):
        result = runner.invoke(
            cli,
            [
                "device",
                "set",
                FAKE_DEVICE["uuid"],
                "--contact-email",
                "new@example.com",
                "--unset",
                "contact_email",
            ],
        )
        assert result.exit_code != 0
        assert "Cannot both set and unset --contact-email" in result.output
        mock_adapter.patch.assert_not_called()
