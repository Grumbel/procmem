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
    subparsers = parser.add_subparsers()

    pid_p = parser.add_mutually_exclusive_group(required=True)
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
    read_p.add_argument("-w", "--writable", action='store_true', default=False,
                        help="Only dump writable pages")
    read_p.add_argument("-s", "--split", action='store_true', default=False,
                        help="Write each memory segment to it's own file")
    read_p.add_argument("-S", "--suspend", action='store_true', default=False,
                        help="Suspend the given process while dumping memory")
    read_p.add_argument("-P", "--pathname", type=str, default=None,
                        help="Limit output to segments matching pathname")

    info_p = subparsers.add_parser("info", help="Print information")
    info_p.set_defaults(command=main_info)
    info_p.add_argument("-v", "--verbose", action='store_true', default=False,
                        help="Include additional information")

    write_p = subparsers.add_parser("write", help="Write to memory")
    write_p.set_defaults(command=main_write)
    write_p.add_argument("-a", "--address", type=str, required=True,
                         help="Address to write to")
    write_p.add_argument("-b", "--bytes", metavar="BYTES", type=str,
                         help="Bytes to write to the given address")
    write_p.add_argument("-s", "--string", metavar="STRING", type=str,
                         help="String to write to the given address")
    write_p.add_argument("-S", "--string0", metavar="STRING", type=str,
                         help="Write a \0 terminated string to the given address")

    search_p = subparsers.add_parser("search", help="Search through memory")
    search_p.set_defaults(command=main_search)

    args = parser.parse_args(argv)
    print(args)
    return args


def make_outfile(template, addr):
    return "{}-{:016x}".format(template, addr)


def main_info(pid, args):
    pass



    if pid == "self":
        pid = os.getpid()
    else:
        pid = int(pid)

    if args.suspend:
        os.kill(pid, signal.SIGSTOP)

def main_read(pid, args):
    procdir = os.path.join("/proc", str(pid))

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

    if args.pathname is not None:
        infos = [info for info in infos if info.pathname == args.pathname]

    total_length = 0
    with open(os.path.join(procdir, "mem"), 'rb', buffering=0) as fin:
        if args.split:
            shutil.copyfile(os.path.join(procdir, "maps"),
                            args.outfile + ".maps")

            for info in infos:
                print(info)
                try:
                    fin.seek(info.addr_range.start)
                    chunk = fin.read(len(info.addr_range))
                    total_length = len(chunk)
                    with open(make_outfile(args.outfile, info.addr_range.start), 'wb') as fout:
                        fout.write(chunk)
                except OverflowError as err:
                    print("overflow error")
                except OSError as err:
                    print("OS error")
        else:
            with open(args.outfile, 'wb') as fout:
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

    if args.suspend:
        os.kill(pid, signal.SIGCONT)

    print("dumped {} bytes".format(total_length))


def main_write(pid, args):
    address = int(args.address)

    if args.bytes is not None:
        data = bytes.fromhex(args.bytes)
    elif args.string is not None:
        data = args.string.encode("UTF-8")
    elif args.string0 is not None:
        data = args.string0.encode("UTF-8") + b"\0"
    else:
        raise Exception("--bytes or --string")

    procdir = os.path.join("/proc", str(pid))

    mem_filename = os.path.join(procdir, "mem")

    with open(mem_filename, "wb", buffering=0) as fout:
        fout.seek(address)
        fout.write(data)


def main_search(pid, args):
    pass


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
    else:
        return pid_by_name(args.process)


def main(argv):
    args = parse_args(argv[1:])
    pid = pid_from_args(args)



def main_entrypoint():
    main(sys.argv)


# EOF #
