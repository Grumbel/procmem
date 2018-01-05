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


import sys
import argparse
import os


def parse_args(argv):
    parser = argparse.ArgumentParser(description="A process memory inspection tool")
    parser.add_argument("PID", nargs=1, type=int)
    parser.add_argument("-a", "--address", type=str, required=True,
                        help="Address to write to")
    parser.add_argument("-b", "--bytes", type=str, required=True,
                        help="Bytes to write to")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv[1:])

    pid = args.PID[0]
    address = int(args.address)
    data = bytes.fromhex(args.bytes)

    procdir = os.path.join("/proc", str(pid))

    mem_filename = os.path.join(procdir, "mem")

    with open(mem_filename, "wb", buffering=0) as fout:
        fout.seek(address)
        fout.write(data)


def main_entrypoint():
    main(sys.argv)


# EOF #
