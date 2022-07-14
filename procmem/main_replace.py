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


import argparse

from procmem.memory import Memory
from procmem.memory_region import filter_memory_maps
from procmem.pack import text2bytes
from procmem.main_search import search


def main_replace(pid: int, args: argparse.Namespace) -> None:
    needle = text2bytes(args.NEEDLE, args.type)
    data = text2bytes(args.DATA, args.type)

    with Memory.from_pid(pid, mode='r+b') as mem:
        infos = mem.regions()
        infos = filter_memory_maps(args, infos)

        for info in infos:
            haystack = mem.read(info.addr_beg, info.addr_end)
            assert haystack is not None
            addrs = search(needle, haystack)

            for addr in addrs:
                assert data is not None
                mem.write(info.addr_beg + addr, data)
                print("replaced data at {:016x}".format(info.addr_beg + addr))


# EOF #
