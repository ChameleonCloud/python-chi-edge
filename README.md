# python-chi-edge

[![Python application](https://github.com/ChameleonCloud/python-chi-edge/actions/workflows/python-app.yml/badge.svg)](https://github.com/ChameleonCloud/python-chi-edge/actions/workflows/python-app.yml)
[![PyPI](https://img.shields.io/pypi/v/python-chi-edge)](https://pypi.org/project/python-chi-edge/)

CLI for enrolling and managing your own edge devices in the [Chameleon](https://chameleoncloud.org) testbed.

## What this is for

You have a single-board computer (Like a Raspberry Pi 4/5, Nvidia Jetson, ...) and you want to add it to [CHI@Edge](https://chameleoncloud.gitbook.io/chi-edge) so that it can be used for Computer Science related Research and Education, by yourself, classmates or coworkers, or the larger Chameleon user community. This tool handles device registration, OS image configuration, and ongoing device management.

**You do NOT need this tool to use devices that are already enrolled.** If you just want to reserve and run containers on existing CHI@Edge hardware, use the [web dashboard](https://chi.edge.chameleoncloud.org/) or the [python-chi SDK](https://python-chi.readthedocs.io/).

## Prerequisites

- A [Chameleon account](https://www.chameleoncloud.org) with an active allocation
- A clouds.yaml or openrc file from the [CHI@Edge dashboard](https://chi.edge.chameleoncloud.org/identity/application_credentials/)
- Python 3.9+
- Physical access to the device you're enrolling

## Install

```
pip install python-chi-edge
```

## Enrollment workflow

### 1. Register your device

```
chi-edge device register \
  --contact-email you@example.com \
  --machine-name raspberrypi5 \
  my-device
```

After this stage, the device will appear with  (`2/4` checks) passing.

### 2. Bake the OS image

Download the appropriate [balenaOS image](https://chameleoncloud.gitbook.io/chi-edge/edge-sdk#download-balena-os-image) for your device, then configure it for the testbed:

```
chi-edge device bake --image balena.img <device-uuid>
```

### 3. Flash and boot

Write the baked image to your device's storage (microSD or eMMC) using [balenaEtcher](https://etcher.balena.io/) or `dd`, then power on. The device should appear healthy (`4/4` checks) within a few minutes.

## Device management

| Command | Description |
|---------|-------------|
| `chi-edge device list` | List your registered devices |
| `chi-edge device show <name>` | Show device details and health |
| `chi-edge device set` | Update device configuration |
| `chi-edge device delete <name>` | Remove a device |
| `chi-edge device sync <name>` | Force device re-sync |

## Configuration

Uses OpenStack [clouds.yaml](https://docs.openstack.org/python-openstackclient/latest/configuration/index.html) or environment variables for authentication. Specify the cloud with `--os-cloud` or set `OS_CLOUD`.

## Documentation

- [CHI@Edge enrollment guide](https://chameleoncloud.gitbook.io/chi-edge/edge-sdk) — full walkthrough with screenshots
- [CHI@Edge user docs](https://chameleoncloud.gitbook.io/chi-edge) — reservations, containers, peripherals
- [Chameleon docs](https://chameleoncloud.readthedocs.io/en/latest/) — broader platform documentation

## License

Apache 2.0
