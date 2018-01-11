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


import os
import sys
import logging
from contextlib import ExitStack

import PIL
import bytefmt

from procmem.memory_region import MemoryRegion, filter_memory_maps
from procmem.hexdump import write_hex


def make_outfile(template, addr):
    return "{}-{:016x}".format(template, addr)


def main_read(pid, args):
    procdir = os.path.join("/proc", str(pid))

    total_length = 0

    mem_file = os.path.join(procdir, "mem")
    if args.range is not None:
        with open(mem_file, 'rb', buffering=0) as fin:
            try:
                fin.seek(args.range.start)
                chunk = fin.read(len(args.range))

                if args.outfile is not None:
                    with open(args.outfile, 'wb') as fout:
                        total_length += len(chunk)
                        fout.write(chunk)
                else:
                    write_hex(sys.stdout, chunk, args.range.start, args.width)
            except OverflowError:
                logging.exception("overflow error")
            except OSError:
                logging.exception("OS error")
    else:
        infos = MemoryRegion.regions_from_pid(pid)
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
                    except OverflowError:
                        logging.exception("overflow error: %s", info)
                    except OSError:
                        logging.exception("OS error: %s", info)

                    total_length += len(chunk)
                    if fout is not None:
                        if args.sparse:
                            fout.seek(info.addr_beg)
                        fout.write(chunk)

                    if fout is None and args.png is None:
                        write_hex(sys.stdout, chunk, info.addr_beg, args.width)

                    if args.png is not None:
                        png_outfile = make_outfile(args.png, info.addr_beg) + ".png"
                        png_height = (len(chunk) + 1024) // 1024
                        padding = (1024 - len(chunk) % 1024) * b"\00"
                        img = PIL.Image.frombytes(mode="L", size=(1024, png_height), data=chunk + padding)
                        logging.info("writing %s", png_outfile)
                        img.save(png_outfile)

    print("dumped {}".format(bytefmt.humanize(total_length, style="binary")))


# EOF #