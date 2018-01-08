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
import shutil
import signal
import string
import psutil
import time
from contextlib import ExitStack

from procmem.units import bytes2human_binary
from procmem.memory_region import MemoryRegion


def AddressRangeOpt(text):
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


def parse_args(argv):
    parser = argparse.ArgumentParser(description="A process memory inspection tool")
    subparsers = parser.add_subparsers()

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
    read_p.add_argument("-S", "--sparse", action='store_true', default=False,
                        help="Write a sparse output file")
    read_p.add_argument("-s", "--split", action='store_true', default=False,
                        help="Write each memory segment to it's own file")
    read_p.add_argument("-H", "--human-readable", action='store_true', default=False,
                        help="Print memory in human readable hex format")
    read_p.add_argument("-r", "--range", type=AddressRangeOpt, default=None,
                        help="Limit output to range")

    write_p = subparsers.add_parser("write", help="Write to memory")
    write_p.set_defaults(command=main_write)
    write_p.add_argument("-a", "--address", type=str, required=True,
                         help="Address to write to")
    data_g = write_p.add_mutually_exclusive_group(required=True)
    data_g.add_argument("-b", "--bytes", metavar="BYTES", type=str,
                        help="Bytes to write to the given address")
    data_g.add_argument("-s", "--string", metavar="STRING", type=str,
                        help="String to write to the given address")
    data_g.add_argument("-S", "--string0", metavar="STRING", type=str,
                        help="Write a \0 terminated string to the given address")

    list_p = subparsers.add_parser("list", help="List processes")
    list_p.set_defaults(command=main_list)

    info_p = subparsers.add_parser("info", help="Print information")
    info_p.set_defaults(command=main_info)
    info_p.add_argument("-v", "--verbose", action='store_true', default=False,
                        help="Include additional information")
    info_p.add_argument("-R", "--raw", action='store_true', default=False,
                        help="Print raw information from /proc/$PID/maps")

    search_p = subparsers.add_parser("search", help="Search through memory")
    search_p.set_defaults(command=main_search)

    statm_p = subparsers.add_parser("statm", help="Memory usage information")
    statm_p.set_defaults(command=main_statm)

    watch_p = subparsers.add_parser("watch", help="Watch memory region")
    watch_p.set_defaults(command=main_watch)
    watch_p.add_argument("-r", "--range", type=AddressRangeOpt, default=None,
                         help="Watch the given range for changes")

    # MemoryRegion filter
    for p in [read_p, info_p]:
        g = p.add_argument_group("Memory Region Filter")
        g.add_argument("-P", "--pathname", type=str, default=None,
                       help="Limit output to segments matching pathname")
        g.add_argument("-w", "--writable", action='store_true', default=False,
                       help="Only dump writable pages")

    return parser.parse_args(argv)


def make_outfile(template, addr):
    return "{}-{:016x}".format(template, addr)


def read_memory_maps(pid):
    infos = []
    maps_path = os.path.join("/proc/", str(pid), "smaps")
    with open(maps_path, 'r') as fin:
        while True:
            info = MemoryRegion.from_smaps_io(fin)
            if info is not None:
                infos.append(info)
            else:
                break

    return infos


def main_info(pid, args):
    if args.raw:
        filename = os.path.join("/proc", str(pid), "smaps")
        with open(filename, "r") as fin:
            sys.stdout.write(fin.read())
    else:
        infos = read_memory_maps(pid)
        infos = filter_memory_maps(args, infos)
        total = 0
        for info in infos:
            total += info.length()
            print(info)
        print("-" * 72)
        print("Total: {} - {} bytes".format(bytes2human_binary(total), total))


def chunk_iter(lst, size):
    return (lst[p:p + size] for p in range(0, len(lst), size))


printable_set = set([ord(c) for c in string.digits + string.ascii_letters + string.punctuation])


def write_hex(fout, buf, offset, width=16):
    """Write the content of 'buf' out in a hexdump style

    Args:
        fout: file object to write to
        buf: the buffer to be pretty printed
        offset: the starting offset of the buffer
        width: how many bytes should be displayed per row
    """

    skipped_zeroes = 0
    for i, chunk in enumerate(chunk_iter(buf, width)):
        # zero skipping
        if chunk == (b"\x00" * 16):
            skipped_zeroes += 1
            continue
        elif skipped_zeroes != 0:
            fout.write("  -- skipped zeroes: {}\n".format(skipped_zeroes).encode())
            skipped_zeroes = 0

        # starting address of the current line
        fout.write("{:016x}  ".format(i * 16 + offset).encode())

        fout.write(
            "  ".join([" ".join(["{:02x}".format(c) for c in subchunk])
                       for subchunk in chunk_iter(chunk, 8)]).encode())

        fout.write(b"  |")
        for c in chunk:
            if c in printable_set:
                fout.write(bytes([c]))
            else:
                fout.write(b".")
        fout.write(b"|")

        fout.write(b"\n")


def filter_memory_maps(args, infos):
    if args.writable:
        infos = [info for info in infos if info.writable]

    if args.pathname is not None:
        infos = [info for info in infos if info.pathname == args.pathname]

    return infos


def main_read(pid, args):
    procdir = os.path.join("/proc", str(pid))

    total_length = 0

    mem_file = os.path.join(procdir, "mem")
    if args.range is not None:
        with open(mem_file, 'rb', buffering=0) as fin, \
             open(args.outfile, 'wb') as fout:
            try:
                fin.seek(args.range.start)
                chunk = fin.read(len(args.range))
                total_length += len(chunk)
                fout.write(chunk)
            except OverflowError:
                print("overflow error", file=sys.stderr)
            except OSError:
                print("OS error", file=sys.stderr)
    else:
        infos = read_memory_maps(pid)
        infos = filter_memory_maps(args, infos)

        fout = None
        with ExitStack() as stack:
            with open(mem_file, 'rb', buffering=0) as fin:
                for info in infos:
                    if args.outfile is None:
                        fout = None
                    elif args.split:
                        filename = make_outfile(args.outfile, info.addr_beg)
                        print("writing to {}".format(filename))
                        fout = stack.enter_context(
                            open(filename, "wb"))
                    else:
                        if fout is None:
                            print("writing to {}".format(args.outfile))
                            fout = stack.enter_context(
                                open(args.outfile, "wb"))

                    if fout is None:
                        print(info)

                    try:
                        fin.seek(info.addr_beg)
                        chunk = fin.read(info.length())
                        total_length += len(chunk)
                        if fout is not None:
                            if args.sparse:
                                fout.seek(info.addr_beg)
                            fout.write(chunk)
                        else:
                            write_hex(sys.stdout, chunk, info.addr_beg)
                    except OverflowError as err:
                        print("overflow error", err)
                    except OSError as err:
                        print("OS error", err)

    print("dumped {}".format(bytes2human_binary(total_length)))


def main_write(pid, args):
    address = int(args.address, 16)

    if args.bytes is not None:
        data = bytes.fromhex(args.bytes)
    elif args.string is not None:
        data = args.string.encode("UTF-8")
    elif args.string0 is not None:
        data = args.string0.encode("UTF-8") + b"\0"

    procdir = os.path.join("/proc", str(pid))

    mem_filename = os.path.join(procdir, "mem")

    with open(mem_filename, "wb", buffering=0) as fout:
        fout.seek(address)
        fout.write(data)


def main_list(pid, args):
    for p in psutil.process_iter():
        print("{:5d}  {}".format(p.pid, p.name()))


def main_search(pid, args):
    pass


def main_watch(pid, args):
    beg = args.range.start
    end = args.range.stop

    filename = os.path.join("/proc", str(pid), "mem")

    print("watching", filename)
    with open(filename, "rb", buffering=0) as fin:
        oldstate = None
        while True:
            fin.seek(beg)
            newstate = fin.read(end - beg)
            if oldstate != newstate:
                print("^-- change detected --")
                write_hex(sys.stdout.buffer, newstate, beg)
                sys.stdout.buffer.flush()
                oldstate = newstate
            time.sleep(0.1)


def main_statm(pid, args):
    filename = os.path.join("/proc", str(pid), "statm")
    with open(filename, "r") as fin:
        content = fin.read()
    size, resident, shared, text, lib, data, dt = [int(x) for x in content.split()]
    page_size = 4096
    print(("{:>10}  total program size\n"
           "{:>10}  resident set size\n"
           "{:>10}  shared size\n"
           "{:>10}  text\n"
           # "{:>10}  lib (unused,always 0)\n"
           "{:>10}  data + stack"
           # "{:>10}  dirty pages (unused, always 0)"
           "")
          .format(*[bytes2human_binary(x * page_size)
                    for x in [size, resident, shared, text, data]]))


def pid_by_name(name):
    return [p.pid for p in psutil.process_iter() if p.name() == name]


def pid_from_args(args):
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


def main(argv):
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


def main_entrypoint():
    main(sys.argv)


# EOF #
