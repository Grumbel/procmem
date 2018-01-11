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

from procmem.memory_region import MemoryRegion


class Memory:

    @staticmethod
    def from_pid(pid, mode="rb"):
        return Memory(pid, mode)

    def __init__(self, pid, mode="rb"):
        self.pid = pid
        self.mode = mode
        self.procdir = os.path.join("/proc", str(pid))
        self.mem_file = os.path.join(self.procdir, "mem")
        self.maps_file = os.path.join(self.procdir, "smaps")
        self._regions = None

    def __enter__(self):
        self.mem_fp = open(self.mem_file, self.mode, buffering=0)
        return self

    def __exit__(self, *exc):
        self.mem_fp.close()

    def read(self, start, end):
        self.mem_fp.seek(start)
        return self.mem_fp.read(end - start)

    def write(self, addr, data):
        self.mem_fp.seek(addr)
        self.mem_fp.write(data)

    def regions(self):
        if self._regions is not None:
            return self._regions
        else:
            self._regions = MemoryRegion.regions_from_file(self.maps_file)
            return self._regions


# EOF #
