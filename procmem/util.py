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


def bytes_from_args(args):
    if args.bytes is not None:
        return bytes.fromhex(args.bytes)
    elif args.string is not None:
        return args.string.encode("UTF-8")
    elif args.string0 is not None:
        return args.string0.encode("UTF-8") + b"\0"

    assert False


# EOF #
