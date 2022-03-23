"""Utilities for reading and writing to disk image."""
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


def read_config_file(image, partition_id, src_file, dest_file):

    part_ref = Volume.vopen(image, mode="r+b", what=f"partition{partition_id}")
    fs_ref = Volume.openvolume(part_ref)

    Volume.copy_out(
        base=fs_ref,
        src_list=[src_file],
        dest=dest_file,
    )

    Volume.vclose(part_ref)


def write_config_file(image, partition_id, src_file, dest_file):

    part_ref = Volume.vopen(image, mode="r+b", what=f"partition{partition_id}")
    fs_ref = Volume.openvolume(part_ref)
    dest_ref = fs_ref.open(dest_file)

    Volume.copy_in(
        [src_file],
        dest=dest_ref,
    )
    fs_ref.flush()
    fs_ref.fat.stream.close()

    Volume.vclose(part_ref)
