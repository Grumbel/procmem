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


from typing import IO

import string

from procmem.itertools import chunk_iter


PRINTABLE_CHARS = set([ord(c) for c in string.digits + string.ascii_letters + string.punctuation])


def write_hex(fout: IO[str], buf: bytes, offset: int, width: int = 16) -> None:
    """Write the content of 'buf' out in a hexdump style

    Args:
        fout: file object to write to
        buf: the buffer to be pretty printed
        offset: the starting offset of the buffer
        width: how many bytes should be displayed per row
    """

    skipped_zeroes = 0
    for i, chunk in enumerate(chunk_iter(buf, width)):
        # zero skipping
        if chunk == (b"\x00" * width):
            skipped_zeroes += 1
            continue
        elif skipped_zeroes != 0:
            fout.write("  -- skipped zeroes: {}\n".format(skipped_zeroes))
            skipped_zeroes = 0

        # starting address of the current line
        fout.write("{:016x}  ".format(i * width + offset))

        # bytes column
        column = "  ".join([" ".join(["{:02x}".format(c) for c in subchunk])
                            for subchunk in chunk_iter(chunk, 8)])
        w = width * 2 + (width - 1) + ((width // 8) - 1)
        if len(column) != w:
            column += " " * (w - len(column))
        fout.write(column)

        # ASCII character column
        fout.write("  |")
        for c in chunk:
            if c in PRINTABLE_CHARS:
                fout.write(chr(c))
            else:
                fout.write(".")
        if len(chunk) < width:
            fout.write(" " * (width - len(chunk)))
        fout.write("|")

        fout.write("\n")


# EOF #
