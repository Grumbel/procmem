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
import re
import struct
import sys

import bytefmt


def chunk_iter(lst, size):
    return (lst[p:p + size] for p in range(0, len(lst), size))


class MemoryRegion:
    # address, perms, offset, dev, inode, pathname
    maps_re = re.compile(
        r'([0-9a-f]+)-([0-9a-f]+) ([r-])([w-])([x-])([ps]) ([0-9a-f]+) ([0-9a-f]+:[0-9a-f]+) (\d+) *(.*)\n',
        re.ASCII)
    info_re = re.compile(r'^([A-Za-z_]+): *(\d+) kB$', re.ASCII)

    @staticmethod
    def regions_from_pid(pid):
        infos = []
        maps_path = os.path.join("/proc/", str(pid), "smaps")

        pagemap_path = os.path.join("/proc/{}/pagemap".format(pid))

        with open(pagemap_path, 'rb', buffering=0) as pagemap_io, \
             open(maps_path, 'r') as fin:
            while True:
                info = MemoryRegion.from_smaps_io(fin)
                if info is not None:
                    # info._process_pagemap(pagemap_io)
                    infos.append(info)
                else:
                    break

        return infos

    def _process_pagemap(self, io):
        assert False, "work in progress"
        PAGE_RAM = (1<<63)  # page is present in RAM
        PAGE_SWAP = (1<<62)  # page is in swap space
        PAGE_FILE = (1<<61) # page is a file-mapped page or a shared anonymous page
        # 60–56 (since Linux 3.11) Zero
        PAGE_SOFT_DIRTY= (1<<55)  # PTE is soft-dirty (see the kernel source file Documentation/vm/soft-dirty.txt).

        # If the page is present in RAM (bit 63), then these bits
        # provide the page frame number, which can be used to index
        # /proc/kpageflags and /proc/kpagecount. If the page is
        # present in swap (bit 62), then bits 4-0 give the swap type,
        # and bits 54-5 encode the swap offset.
        FRAME_MASK=0x3fffffffffffff

        # io.seek(self.addr_beg // 8)
        l = (self.addr_end - self.addr_beg) // 4096 * 8
        io.seek(self.addr_beg//4096 * 8)
        print("PAGEMAP {} {}".format(l, self))
        buf = io.read(l)
        for b in chunk_iter(buf, 8):
            v = struct.unpack("Q".format(len(buf)//8)[0], b)[0]
            print("    {} {} {} {}".format(
                "RAM" if (v & PAGE_RAM) else " - ",
                "SWP" if (v & PAGE_SWAP) else " - ",
                "FIL" if (v & PAGE_FILE) else " - ",
                (v & FRAME_MASK)
            ))

    @staticmethod
    def from_smaps_io(fin):
        line = fin.readline()
        if line == '':
            return None

        region = MemoryRegion.from_string(line)

        while True:
            line = fin.readline()
            assert line != ''
            if line.startswith("VmFlags:"):
                break
            region._add_info_from_string(line)
        region._add_vmflags_from_string(line)

        return region

    def _add_info_from_string(self, text):
        """Parse additional info from /proc/$PID/smaps"""
        match = MemoryRegion.info_re.match(text)
        assert match is not None

        name = match.group(1)
        kb_count = int(match.group(2))
        self.info[name] = kb_count * 1024

    def _add_vmflags_from_string(self, text):
        assert text.startswith("VmFlags:")
        self.vmflags = text[8:].split()

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

        self.info = {}
        self.vmflags = []

    def length(self):
        return self.addr_end - self.addr_beg

    def perms(self):
        return "{}{}{}{}".format(
            "r" if self.readable else "-",
            "w" if self.writable else "-",
            "x" if self.executable else "-",
            "p" if self.private else "s")

    def __str__(self):
        return "{:012x}-{:012x}  {:>10}  {}  {}".format(
            self.addr_beg, self.addr_end,
            bytefmt.humanize(self.length(), style="binary"),
            self.perms(),
            self.pathname)


# EOF #
