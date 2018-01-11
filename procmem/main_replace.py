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

from procmem.memory_region import MemoryRegion, filter_memory_maps
from procmem.pack import text2bytes
from procmem.main_search import search


def main_replace(pid, args):
    infos = MemoryRegion.regions_from_pid(pid)
    infos = filter_memory_maps(args, infos)

    needle = text2bytes(args.NEEDLE, args.type)
    data = text2bytes(args.DATA, args.type)

    mem_file = os.path.join("/proc", str(pid), "mem")

    for info in infos:
        with open(mem_file, 'r+b', buffering=0) as fp:
            fp.seek(info.addr_beg)
            haystack = fp.read(info.length())
            addrs = search(needle, haystack)

            for addr in addrs:
                fp.seek(info.addr_beg + addr)
                fp.write(data)
                print("replaced data at {:016x}".format(info.addr_beg + addr))


# EOF #