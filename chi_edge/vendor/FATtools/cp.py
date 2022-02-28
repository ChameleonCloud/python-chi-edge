# -*- coding: utf-8 -*-

import sys, os, argparse, logging
from chi_edge.vendor.FATtools import Volume
from chi_edge.vendor.FATtools.FAT import Handle
from chi_edge.vendor.FATtools.utils import is_vdisk

DEBUG = 0
from chi_edge.vendor.FATtools.debug import log

#~ logging.basicConfig(level=logging.DEBUG, filename='cp.log', filemode='w')



def cp(srcs_list, dest):
    "Copies items from srcs_list to a target directory (real or inside an image). Supports copy and rename of a single source file, too."
    if is_vdisk(dest):
        dst_image = is_vdisk(dest)
        sub_path = dest[len(dst_image):]
        if DEBUG: log("cp: target is virtual disk '%s', path '%s'", dst_image, sub_path)
        dest = Volume.vopen(dst_image, 'r+b')
        if sub_path:
            if os.path.isdir(sub_path[1:]) or len(srcs_list) > 1 or sub_path[-1] in ('\\','/'):
                if sub_path[-1] in ('\\','/'):
                    sub_path = sub_path[:-1]
                dest = dest.mkdir(sub_path[1:])
            else:
                dest = dest.create(sub_path[1:]) # creates the single target file
        #~ print(srcs_list, sub_path, dest, printn, 2)
        Volume.copy_in(srcs_list, dest, printn, 2)
    else:
        if DEBUG: log("cp: target is real filesystem")
        if not os.path.isdir(dest):
            # Assumes copy-with-rename for a single source item
            if len(srcs_list) > 1:
                if DEBUG: log("cp: target does not exist!")
                raise FileNotFoundError('cp: fatal, target directory "%s" does not exist!'%dest)
        for it in srcs_list:
            src_image = is_vdisk(it)
            sub_path = it[len(src_image)+1:]
            if DEBUG: log("cp: source is virtual disk '%s', path '%s'", src_image, sub_path)
            src = Volume.vopen(src_image, 'rb')
            Volume.copy_out(src, [sub_path], dest, printn, 2)

def printn(s): print(s)



if __name__ == '__main__':
    help_s = """
    cp.py <file1 or dir1> [file2 or dir2...] <destination>
    """
    par = argparse.ArgumentParser(usage=help_s,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="Copies items between real and virtual volumes. Wildcards accepted.\nCopy between virtual disk images is not supported yet.",
    epilog="Examples:\ncp.py File1.txt File2.txt Dir1 image.vhd\ncp.py File*.txt Dir? image.vhd/Subdir\ncp.py image.vhd\\*.py image.vhd/Subdir1 C:\\MyDir\ncp.py image.vhdx/Readme.txt Leggimi.txt")
    par.add_argument('items', nargs='*')
    args = par.parse_args()

    if len(args.items) < 2:
        print("copy error: you must specify at least one source and the destination!")
        par.print_help()
        sys.exit(1)

    dest = args.items.pop()
    cp(args.items, dest)
