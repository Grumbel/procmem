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


from typing import Any, Optional, BinaryIO

import os

from procmem.memory_region import MemoryRegion


class Memory:

    @staticmethod
    def from_pid(pid: int, mode: str = "rb") -> 'Memory':
        return Memory(pid, mode)

    def __init__(self, pid: int, mode: str = "rb") -> None:
        self.pid: int = pid
        self.mode: str = mode
        self._regions: Optional[list[MemoryRegion]] = None
        self.mem_fb: BinaryIO

        self.procdir = os.path.join("/proc", str(pid))
        self.mem_file = os.path.join(self.procdir, "mem")
        self.maps_file = os.path.join(self.procdir, "smaps")

    def __enter__(self) -> 'Memory':
        self.mem_fp = open(self.mem_file, self.mode, buffering=0)
        return self

    def __exit__(self, *exc: Any) -> None:
        self.mem_fp.close()

    def read(self, start: int, end: int) -> Optional[bytes]:
        self.mem_fp.seek(start)
        return self.mem_fp.read(end - start)  # type: ignore

    def write(self, addr: int, data: bytes) -> None:
        self.mem_fp.seek(addr)
        self.mem_fp.write(data)

    def regions(self) -> list[MemoryRegion]:
        if self._regions is not None:
            return self._regions
        else:
            self._regions = MemoryRegion.regions_from_file(self.maps_file)
            assert self._regions is not None
            return self._regions


# EOF #
