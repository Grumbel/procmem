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


from typing import Optional

import struct


INT_DEFS = [
    ("b", ["int8", "i8"]),
    ("B", ["uint8", "ui8"]),
    ("h", ["int16", "i16"]),
    ("H", ["uint16", "ui16"]),
    ("i", ["int32", "i32"]),
    ("I", ["uint32", "ui32"]),
    ("l", ["int64", "i64"]),
    ("L", ["uint64", "ui64"]),
    ("q", ["int64", "i128"]),
    ("Q", ["uint64", "ui128"]),
]


FLOAT_DEFS = [
    ("f", ["float", "f"]),
    ("d", ["double", "d"]),
]


def find_def(ctype: str, defs: list[tuple[str, list[str]]]) -> Optional[str]:
    for d, arr in defs:
        if ctype in arr:
            return d
    return None


def text2bytes(text: str, ctype: str) -> bytes:
    if ctype == "bytes" or ctype == "b":
        return bytes.fromhex(text)

    if ctype == "string" or ctype == "s":
        return text.encode()

    if ctype == "string0" or ctype == "s0":
        return text.encode() + b'\x00'

    endian = ""
    if ctype[0] in ["<", ">", "=", "@", "!"]:
        endian = ctype[0]
        ctype = ctype[1:]

    int_type = find_def(ctype, INT_DEFS)
    if int_type is not None:
        return struct.pack(endian + int_type[0], int(text))

    float_type = find_def(ctype, FLOAT_DEFS)
    if float_type is not None:
        return struct.pack(endian + float_type[0], float(text))

    raise RuntimeError(f"invalid ctype spec: '{ctype}'")


# EOF #
