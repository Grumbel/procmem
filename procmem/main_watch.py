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


import time
import sys

from procmem.memory import Memory
from procmem.hexdump import write_hex


def main_watch(pid, args):
    beg = args.range.start
    end = args.range.stop

    print("watching pid {}".format(pid))
    with Memory.from_pid(pid) as mem:
        oldstate = None
        while True:
            newstate = mem.read(beg, end)
            if oldstate != newstate:
                print("^-- change detected --")
                write_hex(sys.stdout.buffer, newstate, beg)
                sys.stdout.buffer.flush()
                oldstate = newstate
            time.sleep(0.1)


# EOF #
