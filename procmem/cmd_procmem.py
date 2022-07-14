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
import signal
import psutil
import logging

from procmem.main_info import main_info
from procmem.main_list import main_list
from procmem.main_read import main_read
from procmem.main_replace import main_replace
from procmem.main_search import main_search
from procmem.main_statm import main_statm
from procmem.main_watch import main_watch
from procmem.main_write import main_write


def AddressRangeOpt(text: str) -> range:
    g = re.match(r"^([0-9a-fA-F]+)$", text)
    if g is not None:
        s = int(g.group(1), 16)
        return range(s, s + 1)

    g = re.match(r"^([0-9a-fA-F]+):([-+]?[0-9a-fA-F]*)$", text)
    if g is None:
        raise Exception("range argument wrong")
    else:
        lhs_value = int(g.group(1), 16)
        rhs = g.group(2)

        if rhs[0] == "+":
            rhs_value = lhs_value + int(rhs)
        elif rhs[0] == "-":
            rhs_value = lhs_value + int(rhs)
            lhs_value, rhs_value = rhs_value, lhs_value
        else:
            rhs_value = int(rhs, 16)

        return range(lhs_value, rhs_value)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A process memory inspection tool")
    subparsers = parser.add_subparsers()

    parser.set_defaults(command=None)

    pid_p = parser.add_mutually_exclusive_group(required=False)
    pid_p.add_argument("-p", "--pid", metavar="PID", type=str,
                       help="The id of the process to read or write to")
    pid_p.add_argument("-P", "--process", metavar="NAME", type=str,
                       help="The name of the process to read or write to")

    parser.add_argument("-S", "--suspend", action='store_true', default=False,
                        help="Suspend the given process while interacting with the memory")

    read_p = subparsers.add_parser("read", help="Read memory")
    read_p.set_defaults(command=main_read)
    read_p.add_argument("-o", "--outfile", metavar="FILE", type=str, default=None,
                        help="Save memory to FILE")
    read_p.add_argument("--png", metavar="FILE", type=str, default=None,
                        help="Save memory into a PNG file")
    read_p.add_argument("-S", "--sparse", action='store_true', default=False,
                        help="Write a sparse output file")
    read_p.add_argument("-s", "--split", action='store_true', default=False,
                        help="Write each memory segment to it's own file")
    read_p.add_argument("-H", "--human-readable", action='store_true', default=False,
                        help="Print memory in human readable hex format")
    read_p.add_argument("-r", "--range", type=AddressRangeOpt, default=None,
                        help="Limit output to range")
    read_p.add_argument("-W", "--width", metavar="NUM", type=int, default=16,
                        help="Write NUM bytes per row")

    write_p = subparsers.add_parser("write",
                                    description="Write the given memory sequency to the given address.",
                                    help="Write to memory")
    write_p.set_defaults(command=main_write)
    write_p.add_argument("-a", "--address", type=str, required=True,
                         help="Address to write to")
    write_p.add_argument("DATA", help="DATA to write at the given address")

    list_p = subparsers.add_parser("list", help="List processes")
    list_p.set_defaults(command=main_list)

    info_p = subparsers.add_parser("info", help="Print information")
    info_p.set_defaults(command=main_info)
    info_p.add_argument("-v", "--verbose", action='store_true', default=False,
                        help="Include additional information")
    info_p.add_argument("-R", "--raw", action='store_true', default=False,
                        help="Print raw information from /proc/$PID/maps")

    search_p = subparsers.add_parser("search",
                                     description="Search for the given memory sequence",
                                     help="Search through memory")
    search_p.set_defaults(command=main_search)
    search_p.add_argument("-c", "--context", metavar="BYTES", type=int, default=16,
                          help="Display context around the located address")
    search_p.add_argument("-B", "--before-context", metavar="BYTES", type=int, default=None,
                          help="Display context before the located address")
    search_p.add_argument("-A", "--after-context", metavar="BYTES", type=int, default=None,
                          help="Display context after the located address")
    search_p.add_argument("-W", "--width", metavar="NUM", type=int, default=16,
                          help="Write NUM bytes per row")
    search_p.add_argument("NEEDLE", help="Search for NEEDLE")

    statm_p = subparsers.add_parser("statm", help="Memory usage information")
    statm_p.set_defaults(command=main_statm)

    replace_p = subparsers.add_parser("replace", help="Search and replace a section of memory")
    replace_p.set_defaults(command=main_replace)
    replace_p.add_argument("NEEDLE", help="Search for NEEDLE")
    replace_p.add_argument("DATA", help="Replace NEEDLE with DATA")

    watch_p = subparsers.add_parser("watch", help="Watch memory region")
    watch_p.set_defaults(command=main_watch)
    watch_p.add_argument("-r", "--range", type=AddressRangeOpt, default=None,
                         help="Watch the given range for changes")

    # MemoryRegion filter
    for p in [read_p, info_p, search_p, replace_p]:
        g = p.add_argument_group("Memory Region Filter")
        g.add_argument("-P", "--pathname", type=str, default=None,
                       help="Limit output to segments matching pathname")
        g.add_argument("-w", "--writable", action='store_true', default=False,
                       help="Only dump writable pages")
        g.add_argument("--size", metavar="SIZE", type=int, default=None,
                       help="Only show areas larger than SIZE")
        g.add_argument("--no-default-filter", action='store_true', default=False,
                       help="Do not filter [vvar] and [vsyscall] regions")

    for p in [write_p, search_p, replace_p]:
        p.add_argument("-t", "--type", metavar="TYPE", type=str, default="string",
                       help="Specify the type of the data (int8, int16, float, double, ...)")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    return args


def pid_by_name(name: str) -> list[int]:
    return [p.pid for p in psutil.process_iter() if p.name() == name]


def pid_from_args(args: argparse.Namespace) -> int:
    if args.pid is not None:
        if args.pid == "self":
            return os.getpid()
        else:
            return int(args.pid)
    elif args.process is not None:
        pids = pid_by_name(args.process)
        if len(pids) == 0:
            raise Exception("Couldn't find process with name={}".format(args.process))
        elif len(pids) == 1:
            return pids[0]
        else:
            raise Exception("process is not unique: name={}".format(args.process))
    else:
        return os.getpid()


def main(argv: list[str]) -> None:
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args(argv[1:])
    pid = pid_from_args(args)

    if args.suspend:
        os.kill(pid, signal.SIGSTOP)
        try:
            args.command(pid, args)
        finally:
            os.kill(pid, signal.SIGCONT)
    else:
        args.command(pid, args)


def main_entrypoint() -> None:
    main(sys.argv)


# EOF #
