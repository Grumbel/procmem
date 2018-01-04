#!/usr/bin/env python3

# procmem - A process memory inspection tool
# Copyright (C) 2018 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import re
import os
import sys
import argparse
from collections import namedtuple


# address, perms, offset, dev, inode, pathname
maps_re = re.compile(
    r'([0-9a-f]+)-([0-9a-f]+) ([r-])([w-])([x-])([ps]) ([0-9a-f]+) (\d+:\d+) (\d+) *(.*)\n',
    re.ASCII)

PagesInfo = namedtuple('PagesInfo', ['addr_range', 'perms', 'offset', 'dev', 'inode', 'pathname'])


def unpack_maps_re(m):
    addr_beg, addr_end, r, w, x, p, offset, dev, inode, pathname = m.groups()
    return PagesInfo(addr_range=range(int(addr_beg, 16), int(addr_end, 16)),
              perms=(r, w, x, p),
              offset=int(offset, 16),
              dev=dev,
              inode=int(inode),
              pathname=pathname)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="A process memory inspection tool")
    parser.add_argument("PID", nargs=1)
    parser.add_argument("-o", "--outfile", metavar="FILE", type=str, required=True,
                        help="Save memory to FILE")
    parser.add_argument("-w", "--writable", action='store_true', default=False,
                        help="Only dump writable pages")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv[1:])
    pid = args.PID[0]
    procdir = os.path.join("/proc", pid)

    infos = []
    with open(os.path.join(procdir, "maps"), 'r') as fin:
        for line in fin:
            m = maps_re.match(line)
            if not m:
                print("unknown line format:")
                print(line)
            else:
                info = unpack_maps_re(m)
                infos.append(info)

    if args.writable:
        infos = [info for info in infos if info.perms[1] == 'w']

    # infos = [info for info in infos if info.pathname == '']

    total_length = 0
    with open(args.outfile, 'wb') as fout:
        with open(os.path.join(procdir, "mem"), 'rb', buffering=0) as fin:
            for info in infos:
                print(info)
                try:
                    fin.seek(info.addr_range.start)
                    chunk = fin.read(len(info.addr_range))
                    total_length = len(chunk)
                    fout.write(chunk)
                except OverflowError as err:
                    print("overflow error")
                except OSError as err:
                    print("OS error")

    print("dumped {} bytes".format(total_length))


def main_entrypoint():
    main(sys.argv)


# EOF #
