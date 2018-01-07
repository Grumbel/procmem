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


class MemoryRegion:
    # address, perms, offset, dev, inode, pathname
    maps_re = re.compile(
        r'([0-9a-f]+)-([0-9a-f]+) ([r-])([w-])([x-])([ps]) ([0-9a-f]+) (\d+:\d+) (\d+) *(.*)\n',
        re.ASCII)

    @staticmethod
    def from_string(text):
        match = MemoryRegion.maps_re.match(text)
        if not match:
            raise Exception("parse error on line:\n{}".format(text))
        else:
            return MemoryRegion._from_match(match)

    @staticmethod
    def _from_match(match):
        """Create a MemoryRegion object from a string in the format found in /proc/$PID/maps"""
        addr_beg, addr_end, r, w, x, p, offset, dev, inode, pathname = match.groups()
        return MemoryRegion(addr_beg=int(addr_beg, 16),
                            addr_end=int(addr_end, 16),
                            readable=(r == "r"),
                            writable=(w == "w"),
                            executable=(x == "x"),
                            private=(p == "p"),
                            offset=int(offset, 16),
                            dev=dev,
                            inode=int(inode),
                            pathname=pathname)

    def __init__(self, addr_beg, addr_end, readable, writable, executable, private, offset, dev, inode, pathname):
        self.addr_beg = addr_beg
        self.addr_end = addr_end
        self.readable = readable
        self.writable = writable
        self.executable = executable
        self.private = private
        self.offset = offset
        self.dev = dev
        self.inode = inode
        self.pathname = pathname

    def length(self):
        return self.addr_end - self.addr_beg

    def perms(self):
        return "{}{}{}{}".format(
            "r" if self.readable else "-",
            "w" if self.writable else "-",
            "x" if self.executable else "-",
            "p" if self.private else "s")


# EOF #
