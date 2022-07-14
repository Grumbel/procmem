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
import os

import bytefmt


def main_statm(pid: int, args: argparse.Namespace) -> None:
    filename = os.path.join("/proc", str(pid), "statm")
    with open(filename, "r") as fin:
        content = fin.read()
    size, resident, shared, text, lib, data, dt = [int(x) for x in content.split()]
    page_size = 4096
    print(("{:>10}  total program size\n"
           "{:>10}  resident set size\n"
           "{:>10}  shared size\n"
           "{:>10}  text\n"
           # "{:>10}  lib (unused,always 0)\n"
           "{:>10}  data + stack"
           # "{:>10}  dirty pages (unused, always 0)"
           "")
          .format(*[bytefmt.humanize(x * page_size, style="binary")
                    for x in [size, resident, shared, text, data]]))


# EOF #
