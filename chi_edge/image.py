"""Utilities for reading and writing to disk image."""
import json
from pathlib import Path

from chi_edge.vendor.FATtools import Volume
from chi_edge.vendor.FATtools.partutils import partition


def find_boot_partition_id(image: str):

    # max of 128 gpt partitions possible
    for partid in range(0, 128):
        try:
            part = Volume.vopen(
                image,
                mode="r+b",
                what=f"partition{partid}",
            )
            partfs = Volume.openvolume(part)
        except ZeroDivisionError:
            pass
        except FileNotFoundError:
            raise
        else:
            try:
                part_label = partfs.label()
            except AttributeError:
                pass
            else:
                if part_label == "resin-bo.ot":
                    Volume.vclose(part)
                    return partid
            Volume.vclose(part)
    else:
        raise Exception("Cannot find boot partition")


def read_config_json(image, partition_id, filename):
    o = Volume.vopen(image, mode="r+b", what=f"partition{partition_id}")
    fs = Volume.openvolume(o)
    f = fs.open(filename)
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        raise
    finally:
        f.close()
        fs.close()
        o.close()

    return data


def write_config_json(image, partition_id, filename, configdata):
    o = Volume.vopen(image, mode="r+b", what=f"partition{partition_id}")
    fs = Volume.openvolume(o)
    try:
        # we need to write bytes, use fattools write method
        json_str = json.dumps(
            obj=configdata,
            indent=2,
        )
        f = fs.create(filename)
        f.write(json_str.encode("utf-8"))
        fs.flush()
    except json.JSONDecodeError:
        raise
    finally:
        f.close()
        fs.close()
        o.close()
