# ScatterBackup - A chaotic backup solution
# Copyright (C) 2015 Ingo Ruhnke <grumbel@gmail.com>
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
from decimal import Decimal


units = {
    "B": 1,

    "kB": 1000**1,
    "MB": 1000**2,
    "GB": 1000**3,
    "TB": 1000**4,
    "PB": 1000**5,
    "EB": 1000**6,
    "ZB": 1000**7,
    "YB": 1000**8,

    "kiB": 1024**1,
    "MiB": 1024**2,
    "GiB": 1024**3,
    "TiB": 1024**4,
    "PiB": 1024**5,
    "EiB": 1024**6,
    "ZiB": 1024**7,
    "YiB": 1024**8
}


def size2bytes(text: str) -> int:
    """Convert a text string (e.g. "582.5MB") to a byte count. kB=1000, kiB=1024"""

    m = re.match(r"^\s*([0-9]+|[0-9]+\.[0-9]+)\s*([A-Za-z]+|)\s*$", text)
    if m:
        value, unit = m.groups()
        if unit == "":
            return int(value)
        elif unit in units:
            return int(Decimal(value) * units[unit])
        else:
            raise Exception("unknown unit {!r} in {!r}".format(unit, text))
    else:
        raise Exception("couldn't interpret {!r}".format(text))


def bytes2human_decimal(count):
    """Returns size formated as a human readable string"""

    if count < 1000:
        return "{}B".format(count)
    elif count < 1000 ** 2:
        return "{:.2f}kB".format(count / 1000**1)
    elif count < 1000 ** 3:
        return "{:.2f}MB".format(count / 1000**2)
    elif count < 1000 ** 4:
        return "{:.2f}GB".format(count / 1000**3)
    elif count < 1000 ** 5:
        return "{:.2f}TB".format(count / 1000**4)
    elif count < 1000 ** 6:
        return "{:.2f}TB".format(count / 1000**5)
    elif count < 1000 ** 7:
        return "{:.2f}EB".format(count / 1000**8)
    elif count < 1000 ** 8:
        return "{:.2f}ZB".format(count / 1000**9)
    else:  # count < 1000 ** 9
        return "{:.2f}YB".format(count / 1000**10)


def bytes2human_binary(count):
    """Returns size formated as a human readable string"""

    if count < 1024:
        return "{}B".format(count)
    elif count < 1024 ** 2:
        return "{:.2f}KiB".format(count / 1024**1)
    elif count < 1024 ** 3:
        return "{:.2f}MiB".format(count / 1024**2)
    elif count < 1024 ** 4:
        return "{:.2f}GiB".format(count / 1024**3)
    elif count < 1024 ** 5:
        return "{:.2f}TiB".format(count / 1024**4)
    elif count < 1024 ** 6:
        return "{:.2f}PiB".format(count / 1024**5)
    elif count < 1024 ** 7:
        return "{:.2f}EiB".format(count / 1024**8)
    elif count < 1024 ** 8:
        return "{:.2f}ZiB".format(count / 1024**9)
    else:  # count < 1024 ** 9
        return "{:.2f}YiB".format(count / 1024**10)


# EOF #
