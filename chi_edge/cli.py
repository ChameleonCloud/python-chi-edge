# Copyright 2021 University of Chicago
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import contextlib
from datetime import datetime
import json
import logging
from operator import itemgetter
import os
from uuid import UUID

import chi
import click
from keystoneauth1 import adapter
from keystoneauth1 import exceptions as ksa_exc
from rich.console import Console
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import yaml

from chi_edge import SUPPORTED_MACHINE_NAMES
from chi_edge.vendor.FATtools import cp

console = Console()


class BaseCommand(click.Command):
    """A base command class that handles global option parsing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params.append(
            click.Option(
                ("--debug/--no-debug",), default=False, help="enable debug logging"
            )
        )

    def invoke(self, ctx: "click.Context") -> "Any":
        debug = ctx.params.pop("debug")
        logging.basicConfig(level=logging.DEBUG if debug else logging.FATAL)
        return super().invoke(ctx)


@click.group()
def cli():
    """Tools for interacting with the CHI@Edge testbed.

    See the list of subcommands for futher details about device enrollment or other
    capabilities provided by the SDK.
    """
    pass


@cli.group("device", short_help="manage or register devices")
def device():
    pass


@device.command(cls=BaseCommand, short_help="register a new device")
@click.argument("device_name")
@click.option(
    "--machine-name",
    required=True,
    type=click.Choice(SUPPORTED_MACHINE_NAMES.keys()),
    help="type of device",
)
@click.option(
    "--contact-email",
    required=True,
    metavar="EMAIL",
    help="a contact email for the owner of the device",
)
@click.option(
    "--application-credential-id",
    required=True,
    metavar="ID",
    help="an ID of an application credential created for CHI@Edge",
)
@click.option(
    "--application-credential-secret",
    required=True,
    metavar="SECRET",
    help="the secret component of the application credential",
)
def register(
    device_name: "str",
    machine_name: "str" = None,
    contact_email: "str" = None,
    application_credential_id: "str" = None,
    application_credential_secret: "str" = None,
):
    """Register a device on the CHI@Edge testbed as DEVICE_NAME.

    This is the first step to enrolling an edge device into the testbed and will result
    in a configuration record for your device being added to the testbed registry. The
    testbed will generate per-device configuration as a result of this registration,
    which you can then use to "bake" a generic base OS image for your target device
    (see: bake command.)

    As a result of registration, your device will be issued a UUID, which you can use
    to interact with the testbed via other SDK methods.

    \b
    Supported devices
    -----------------

    Currently a limited number of machine names (types/classes of devices) are supported:

    \b
      raspberrypi3-64: Raspberry Pi 3 (using 64bit OS)
      raspberrypi4-64: Raspberry Pi 4 (using 64bit OS)

    \b
    Naming your device
    ------------------

    Every device registered on the testbed requires a machine-friendly name. This must
    be unique on the testbed; for help choosing a name with maximum utility, please
    refer to the enrollment documentation:
    https://chameleoncloud.gitbook.io/chi-edge/device-enrollment/edge-sdk

    """
    with doni_error_handler("failed to register device"):
        device = (
            doni_client()
            .post(
                "/v1/hardware/",
                json={
                    "name": device_name,
                    "hardware_type": "device.balena",
                    "properties": {
                        "application_credential_id": application_credential_id,
                        "application_credential_secret": application_credential_secret,
                        "contact_email": contact_email,
                        "machine_name": machine_name,
                    },
                },
            )
            .json()
        )
        print_device(device)


@device.command(cls=BaseCommand, short_help="list registered devices")
def list():
    with doni_error_handler("failed to list devices"):
        devices = doni_client().get("/v1/hardware/").json()["hardware"]
        table = make_table()
        table.add_column("Name")
        table.add_column("UUID")
        table.add_column("Registered at")
        table.add_column("Health")
        table.add_column("Last seen")
        for device in devices:
            balena_worker = None
            ok_workers, total_workers = 0, 0
            for worker in device["workers"]:
                total_workers += 1
                if worker["state"] == "STEADY":
                    ok_workers += 1
                if worker["worker_type"] == "balena":
                    balena_worker = worker
            registration_state = f"{ok_workers}/{total_workers}"
            table.add_row(
                device["name"],
                device["uuid"],
                localize(device["created_at"]),
                registration_state,
                localize(balena_worker["state_details"].get("last_seen", "--"))
                if balena_worker
                else "--",
            )
        console.print(table)


@device.command(cls=BaseCommand, short_help="show registered device details")
@click.argument("device")
def show(device: "str"):
    with doni_error_handler("failed to fetch device"):
        doni = doni_client()
        uuid = resolve_device(doni, device)
        print_device(doni.get(f"/v1/hardware/{uuid}/").json())


@device.command(cls=BaseCommand, short_help="update registered device details")
@click.argument("device")
@click.option("--contact-email")
@click.option("--application-credential-id")
@click.option("--application-credential-secret")
def set(
    device: "str",
    contact_email: "str" = None,
    application_credential_id: "str" = None,
    application_credential_secret: "str" = None,
):
    def patch_to(prop, value):
        return {"op": "replace", "path": f"/properties/{prop}", "value": value}

    with doni_error_handler("failed to fetch device"):
        doni = doni_client()
        uuid = resolve_device(doni, device)
        patch = []
        if contact_email:
            patch.append(patch_to("contact_email", contact_email))
        if application_credential_id:
            patch.append(
                patch_to("application_credential_id", application_credential_id)
            )
        if application_credential_secret:
            patch.append(
                patch_to("application_credential_secret", application_credential_secret)
            )
        print_device(doni.patch(f"/v1/hardware/{uuid}/", json=patch).json())


@device.command(cls=BaseCommand, short_help="delete registered device")
@click.argument("device")
@click.option("--yes-i-really-really-mean-it", is_flag=True)
def delete(device: "str", yes_i_really_really_mean_it: "bool" = False):
    if not yes_i_really_really_mean_it:
        raise click.ClickException(
            "Are you sure? Specify --yes-i-really-really-mean-it if so. Deleting the "
            "device will clean up all record of its registration and will impact any "
            "current users of the device on the testbed."
        )
    with doni_error_handler("failed to delete device"):
        doni = doni_client()
        uuid = resolve_device(doni, device)
        doni.delete(f"/v1/hardware/{uuid}/")
        print("Successfully deleted device")


@device.command(cls=BaseCommand, short_help="force device re-sync")
@click.argument("device")
def sync(device: "str"):
    with doni_error_handler("failed to sync device"):
        doni = doni_client()
        uuid = resolve_device(doni, device)
        doni.post(f"/v1/hardware/{uuid}/sync/")
        print("Successfully started device re-sync")


@device.command(
    cls=BaseCommand, short_help="configure an OS image for a registered device"
)
@click.argument("device_uuid")
@click.option(
    "--image",
    metavar="IMAGE",
    help=(
        "Path to the raw disk image to configure. This should be a `.img` "
        "file. If not specified, `config.json` will be created, but not "
        "copied anywhere."
    ),
)
def bake(
    device_uuid: "str",
    image: "str" = None,
):
    # Ensure we do not overwrite a `config.json` file on the user's system
    if os.path.isfile("config.json"):
        raise click.ClickException("'config.json' already exists!")

    # Check for device in doni
    doni = doni_client()
    hardware = doni.get(f"/v1/hardware/{device_uuid}/").json()
    balena_workers = [
        worker for worker in hardware["workers"] if worker["worker_type"] == "balena"
    ]
    if not balena_workers:
        raise click.ClickException(
            "Device is not enrolled with support for Balena, you may need to attempt "
            "registration again"
        )
    balena_worker = balena_workers[0]["state_details"]

    # Copy existing config file. For an unconfigured OS, it seems this
    # just contains `deviceType`
    if image:
        cp.cp([f"{image}/config.json"], "config.json")
        with open("config.json") as f:
            config = json.load(f)
    else:
        config = {}

    # Copy over needed keys to config
    config["uuid"] = device_uuid.replace("-", "").lower()
    config["apiKey"] = balena_worker["device_api_key"]
    config["applicationId"] = balena_worker["fleet_id"]
    config["appUpdatePollInterval"] = "60000"
    # This is the default Balena supervisor listen port
    config["listenPort"] = "48484"
    config["vpnPort"] = "443"
    config["apiEndpoint"] = "https://api.balena-cloud.com"
    config["vpnEndpoint"] = "vpn.balena-cloud.com"
    config["registryEndpoint"] = "registry2.balena-cloud.com"
    config["deltaEndpoint"] = "https://delta.balena-cloud.com"

    # Put config data back into image
    with open("config.json", "w") as f:
        json.dump(config, f)
    if image:
        cp.cp(["config.json"], f"{image}/config.json")
        print("Successfully patched image")
    else:
        print("Created 'config.json'")


def doni_client():
    return adapter.Adapter(chi.session(), interface="public", service_type="inventory")


def print_device(hardware):
    outer = Table(show_header=False, padding=(0, 0), pad_edge=False, show_edge=False)
    table = make_table()
    table.add_column("Property")
    table.add_column("Value")
    for prop, value in hardware["properties"].items():
        table.add_row(prop, format_value(value))
    title = Text()
    title.append(hardware["name"], style="bold green")
    title.append(" ── " + hardware["uuid"])
    outer.add_row(table)
    outer.add_row("Health details")
    workers = hardware["workers"]
    cols = [""] + [w["worker_type"] for w in workers]
    worker_table = make_table(*cols, header_style="blue")
    for key in ["state", "state_details"]:
        worker_table.add_row(*([key] + [format_value(w[key]) for w in workers]))
    outer.add_row(worker_table)
    console.print(Panel(outer, title=title, title_align="left"))


@contextlib.contextmanager
def doni_error_handler(default_message):
    try:
        yield
    except ksa_exc.AuthPluginException as auth_err:
        raise click.ClickException(f"{default_message}: {auth_err}")
    except ksa_exc.HttpError as http_err:
        try:
            message = http_err.response.json()["error"]
        except Exception:
            message = http_err.message
        raise click.ClickException(message)


def resolve_device(doni_client, device_ref: "str"):
    try:
        uuid = str(UUID(device_ref))
    except ValueError:
        uuid = None
        for d in doni_client.get(f"/v1/hardware/").json()["hardware"]:
            if d["name"] == device_ref:
                uuid = d["uuid"]
                break

    if not uuid:
        raise click.ClickException(f"Device {device_ref} not found")

    return uuid


def localize(utc_datestr):
    try:
        return (
            datetime.fromisoformat(utc_datestr.replace("Z", "+00:00"))
            .astimezone()
            .isoformat()
        )
    except ValueError as exc:
        return utc_datestr


def format_value(value):
    if isinstance(value, dict):
        return yaml.dump(value).strip()
    return value


def make_table(*headers, **kwargs):
    kwargs.setdefault("show_header", True)
    kwargs.setdefault("header_style", "bold green")
    kwargs.setdefault("box", box.MINIMAL_HEAVY_HEAD)
    return Table(*headers, **kwargs)
