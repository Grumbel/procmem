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

from procmem.memory_region import MemoryRegion, filter_memory_maps
from procmem.util import bytes_from_args
from procmem.hexdump import write_hex

def search(needle, haystack):
    results = []

    cur = 0
    while True:
        i = haystack.find(needle, cur)
        if i != -1:
            results.append(i)
            cur = i + 1
        else:
            break

    return results


def main_search(pid, args):
    infos = MemoryRegion.regions_from_pid(pid)
    infos = filter_memory_maps(args, infos)

    needle = bytes_from_args(args)

    mem_file = os.path.join("/proc", str(pid), "mem")

    if args.context == 0:
        show_context = False
    else:
        show_context = True
        before_context = args.before_context or args.context
        after_context = args.after_context or args.context

    for info in infos:
        with open(mem_file, 'rb', buffering=0) as fin:
                fin.seek(info.addr_beg)
                haystack = fin.read(info.length())
                addrs = search(needle, haystack)
                for addr in addrs:
                    print("found pattern at {:016x}".format(info.addr_beg + addr))
                    if show_context:
                        s = max(0, addr - before_context)
                        e = min(len(haystack), addr + len(needle) + after_context)
                        context = haystack[s:e]
                        write_hex(sys.stdout, context, info.addr_beg + s)
                        print()


# EOF #
