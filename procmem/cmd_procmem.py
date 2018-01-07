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
    read_p.add_argument("-o", "--outfile", metavar="FILE", type=str, required=True,
                        help="Save memory to FILE")
    read_p.add_argument("-s", "--split", action='store_true', default=False,
                        help="Write each memory segment to it's own file")
    read_p.add_argument("-H", "--human-readable", action='store_true', default=False,
                        help="Print memory in human readable hex format")
    read_p.add_argument("-r", "--range", type=AddressRangeOpt, default=None,
                        help="Limit output to range")
    read_p.add_argument("-R", "--relative-range", type=AddressRangeOpt, default=None,
                        help="Limit output to range, address relative to the start of the segment")

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
    maps_path = os.path.join("/proc/", str(pid), "maps")
    with open(maps_path, 'r') as fin:
        for line in fin:
            infos.append(MemoryRegion.from_string(line))
    return infos


def main_info(pid, args):
    if args.raw:
        filename = os.path.join("/proc", str(pid), "maps")
        with open(filename, "r") as fin:
            sys.stdout.write(fin.read())
    else:
        infos = read_memory_maps(pid)
        infos = filter_memory_maps(args, infos)
        total = 0
        for info in infos:
            total += info.length()
            print("{:012x}-{:012x}  {:>10}  {}  {}".format(info.addr_beg, info.addr_end,
                                                         bytes2human_binary(info.length()),
                                                         info.perms(),
                                                         info.pathname))
        print("-" * 72)
        print("Total: {} - {} bytes".format(bytes2human_binary(total), total))


def chunk_iter(lst, size):
    return (lst[p:p + size] for p in range(0, len(lst), size))


printable_set = set([ord(c) for c in string.digits + string.ascii_letters + string.punctuation])


def write_hex(fp, buf, offset):
    skiped_zeroes = 0
    for i, chunk in enumerate(chunk_iter(buf, 16)):
        if chunk == (b"\x00" * 16):
            skiped_zeroes += 1
            continue

        if skiped_zeroes != 0:
            fp.write("  -- skipped nulls: {}\n".format(skiped_zeroes).encode())
            skiped_zeroes = 0

        fp.write("{:016x}  ".format(i * 16 + offset).encode())

        fp.write(" ".join(["{:02x}".format(c) for c in chunk[0:8]]).encode())
        fp.write(b"  ")
        fp.write(" ".join(["{:02x}".format(c) for c in chunk[8:16]]).encode())

        fp.write(b"  |")
        for c in chunk:
            if c in printable_set:
                fp.write(bytes([c]))
            else:
                fp.write(b".")
        fp.write(b"|")

        fp.write(b"\n")


def filter_memory_maps(args, infos):
    if args.writable:
        infos = [info for info in infos if info.writable]

    if args.pathname is not None:
        infos = [info for info in infos if info.pathname == args.pathname]

    return infos


def main_read(pid, args):
    procdir = os.path.join("/proc", str(pid))

    infos = read_memory_maps(pid)
    infos = filter_memory_maps(args, infos)

    def write_func_default(fp, buf, offset):
        fp.write(buf)

    if args.human_readable:
        write_func = write_hex
    else:
        write_func = write_func_default

    total_length = 0
    with open(os.path.join(procdir, "mem"), 'rb', buffering=0) as fin:
        if args.split:
            shutil.copyfile(os.path.join(procdir, "maps"),
                            args.outfile + ".maps")

            for info in infos:
                print(info)
                try:
                    fin.seek(info.addr_beg)
                    chunk = fin.read(info.length())
                    total_length = len(chunk)
                    with open(make_outfile(args.outfile, info.addr_beg), 'wb') as fout:
                        write_func(fout, chunk, info.addr_beg)
                except OverflowError:
                    print("overflow error")
                except OSError:
                    print("OS error")
        else:
            with open(args.outfile, 'wb') as fout:
                if args.range is not None:
                    fin.seek(args.range.start)
                    chunk = fin.read(len(args.range))
                    write_func(fout, chunk, args.range.start)
                else:
                    for info in infos:
                        print(info)
                        try:
                            fin.seek(info.addr_beg)
                            chunk = fin.read(info.length())
                            total_length = len(chunk)
                            write_func(fout, chunk, info.addr_beg)
                        except OverflowError:
                            print("overflow error")
                        except OSError:
                            print("OS error")

    print("dumped {} bytes".format(total_length))


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

def pid_by_name(name):
    results = [p for p in psutil.process_iter() if p.name() == name]
    if results == []:
        raise Exception("Couldn't find process with name={}".format(name))
    elif len(results) != 1:
        print(results)
        raise Exception("process is not unique: name={}".format(name))
    else:
        return results[0].pid


def pid_from_args(args):
    if args.pid is not None:
        if args.pid == "self":
            return os.getpid()
        else:
            return int(args.pid)
    elif args.process is not None:
        return pid_by_name(args.process)
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
