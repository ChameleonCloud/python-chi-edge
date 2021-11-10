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
import os

import click
import yaml

from chi_edge import SUPPORTED_DEVICE_TYPES, VIRTUAL_SITE_INTERNAL_ADDRESS, ansible


@click.group("edge")
def cli():
    pass


@cli.command(help="Bootstrap an edge device for enrollment into CHI@Edge")
@click.argument("host")
@click.option(
    "--device-type",
    required=True,
    type=click.Choice(SUPPORTED_DEVICE_TYPES),
    help=(
        "Type of device to bootstrap. Device needs are very specific; only "
        "the device types listed are supported."
    ),
)
@click.option(
    "--enrollment-type",
    type=click.Choice(["legacy-openstack"]),
    default="legacy-openstack",
    help=(
        "Type of enrollment to perform. This will affect how your device is integrated "
        "with the edge testbed, and what interfaces and capabilities are provided to "
        "end users."
    ),
)
@click.option(
    "--enrollment-conf",
    type=click.File(),
    help=(
        "An optional YAML enrollment configuration file. This should be in your "
        "posession for certain types of enrollment."
    ),
)
@click.option(
    "--network-interface",
    metavar="DEVICE",
    default="eth0",
    help=(
        "The name of the interface on the device that has connectivity. If "
        "there are multiple such interfaces, pick one to consider as the primary."
    ),
)
@click.option(
    "--mgmt-channel-address",
    metavar="IPV4",
    help=(
        "The address assigned to the device on the management channel. If "
        "you do not know what this is, ask the edge site operators."
    ),
)
@click.option(
    "--user-channel-address",
    metavar="IPV4",
    help=(
        "The address assigned to the device on the user channel. If "
        "you do not know what this is, ask the edge site operators."
    ),
)
@click.option(
    "--sudo-password",
    metavar="PASSWORD",
    help=("The sudo password, if required"),
)
@click.option(
    "--sudo/--no-sudo",
    default=True,
    help=(
        "If an unprivileged user is currently set up on the device and will "
        "be used for bootstrapping (recommended), use sudo for escalation."
    ),
)
@click.option(
    "--extra-vars",
    metavar="KEY=VAL",
    multiple=True,
    help=(
        "Extra variables to add to the Ansible invocation(s), e.g., 'ansible_connection'. "
        "Should be specified as key/value pairs separated by an equal sign. Repeat "
        "to pass multiple host vars."
    ),
)
def bootstrap(
    host: "str" = None,
    device_type: "str" = None,
    enrollment_type: "str" = None,
    enrollment_conf=None,
    network_interface: "str" = None,
    mgmt_channel_address: "str" = None,
    user_channel_address: "str" = None,
    sudo_password: "str" = None,
    sudo: "bool" = None,
    extra_vars: "dict" = None,
):
    if extra_vars:
        extra_vars_dict = dict([tuple(line.split("=") for line in extra_vars)])
    else:
        extra_vars_dict = {}

    host_vars = {
        "site_internal_vip": VIRTUAL_SITE_INTERNAL_ADDRESS,
        "enrollment_type": enrollment_type,
        **extra_vars_dict,
    }

    # Prefer to use enrollment config file to set most additional vars
    if enrollment_conf:
        for key, value in yaml.safe_load(enrollment_conf).items():
            host_vars.setdefault(key, value)

    # Some special (legacy) vars are set via CLI if provided
    cli_vars = {
        "iface": network_interface,
        "mgmt_ipv4": mgmt_channel_address,
        "user_ipv4": user_channel_address,
    }
    for key, value in cli_vars.items():
        if value is not None:
            host_vars[key] = value

    if sudo:
        host_vars.setdefault("ansible_become", True)
        if sudo_password:
            host_vars.setdefault("ansible_sudo_pass", sudo_password)

    if device_type == "nano":
        # Jetson Nanos use L4T distribution based on Ubuntu 18.04, which
        # doesn't have docker-ce built for stable.
        host_vars.setdefault("docker_package", "docker")

    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, "ansible/defaults.yml")
    with open(filename, "r") as f:
        defaults = yaml.safe_load(f)
        for key, value in defaults.items():
            host_vars.setdefault(key, value)

    return ansible.run(
        "setup_edge_dev.yml", host, group=device_type, host_vars=host_vars
    )
