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
import json
import os

import chi
import click
import yaml
from keystoneauth1 import adapter

from chi_edge import SUPPORTED_MACHINE_NAMES
from chi_edge.vendor.FATtools import cp


@click.group()
def cli():
    pass


@cli.command(short_help="register a new device")
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
def register(
    device_name: "str",
    machine_name: "str" = None,
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
    pass


@cli.command(short_help="configure an OS image for a registered device")
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
