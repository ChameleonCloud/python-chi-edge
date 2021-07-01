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

import logging
import pathlib
import subprocess
import sys
import tempfile

import ansible_runner
import click

from chi_edge import SUPPORTED_DEVICE_TYPES

LOG = logging.getLogger(__name__)
HERE = pathlib.Path(__file__).parent
REQUIREMENTS_FILE = pathlib.Path(HERE, "requirements.yml")
COLLECTIONS_PATH = pathlib.Path(sys.prefix, "share", "ansible", "collections")
ROLES_PATH = pathlib.Path(sys.prefix, "share", "ansible", "roles")

playbooks = [
    f.name.replace(".yml", "")
    for f in HERE.iterdir()
    if f.name.endswith(".yml") and f != REQUIREMENTS_FILE
]


def install_requirements():
    subprocess.run(
        [
            "ansible-galaxy",
            "role",
            "install",
            "--role-file",
            REQUIREMENTS_FILE.absolute(),
            "--roles-path",
            ROLES_PATH.absolute(),
        ],
        check=True,
    )
    subprocess.run(
        [
            "ansible-galaxy",
            "collection",
            "install",
            "--requirements-file",
            str(REQUIREMENTS_FILE.absolute()),
            "--collections-path",
            str(COLLECTIONS_PATH.absolute()),
        ],
        check=True,
    )


def run(playbook: "str", host: "str", group: "str" = None, host_vars: "dict" = None):
    inventory = {"all": {"children": {}}}
    inventory_host = {"hosts": {host: host_vars}}
    if group:
        inventory["all"]["children"][group] = inventory_host
    else:
        inventory["all"] = inventory_host
    with tempfile.TemporaryDirectory() as tmpdir:
        ansible_runner.run(
            private_data_dir=tmpdir,
            project_dir=str(HERE.absolute()),
            roles_path=[str(ROLES_PATH.absolute())],
            playbook=playbook,
            inventory=inventory,
        )


@click.command(
    "ansible-playbook",
    help=(
        "Execute one of the Edge SDK Ansible playbooks directly. "
        "This is intended to be a development/debug aide and should not be "
        "used as a primary workflow."
    ),
)
@click.argument("host")
@click.option(
    "--playbook", type=click.Choice(playbooks), help="Playbook to run on the host"
)
@click.option(
    "--group", type=click.Choice(SUPPORTED_DEVICE_TYPES), help="Host grouping to apply"
)
@click.option(
    "--host-vars",
    metavar="KEY=VAL",
    multiple=True,
    help=(
        "Host variables to add to the playbook run invocation, e.g., 'ansible_connection'. "
        "Should be specified as key/value pairs separated by an equal sign. Repeat "
        "to pass multiple host vars."
    ),
)
def cli(
    playbook: "str", host: "str", group: "str" = None, host_vars: "list[str]" = None
):
    host_vars_dict = dict([tuple(line.split("=")) for line in host_vars])
    return run(f"{playbook}.yml", host, group=group, host_vars=host_vars_dict)
