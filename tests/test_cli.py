from unittest import mock

from click.testing import CliRunner

from chi_edge import cli


@mock.patch.object(cli, "doni_client")
@mock.patch.object(cli, "print_device")
def test_register_device(
    mocked_doni_client: mock.MagicMock,
    mocked_print_device: mock.MagicMock,
):
    runner = CliRunner()

    register_args = [
        "a-test-device-name",
        "--machine-name",
        "raspberrypi5",
        "--contact-email",
        "fake@email.local",
        "--application-credential-id",
        "fake-app-cred-id",
        "--application-credential-secret",
        "fake-app-cred-secret",
    ]

    result = runner.invoke(cli.register, register_args)
    assert result.exit_code == 0
    mocked_doni_client.assert_called_once()
