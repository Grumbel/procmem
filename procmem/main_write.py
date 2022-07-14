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
from procmem.pack import text2bytes


def main_write(pid: int, args: argparse.Namespace) -> None:
    address = int(args.address, 16)

    data = text2bytes(args.DATA, args.type)
    assert data is not None

    with Memory.from_pid(pid, mode='wb') as mem:
        mem.write(address, data)


# EOF #
