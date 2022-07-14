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
import sys

import bytefmt

from procmem.memory_region import MemoryRegion, filter_memory_maps


vmflags_to_doc = {
    "rd": "readable",
    "wr": "writable",
    "ex": "executable",
    "sh": "shared",
    "mr": "may read",
    "mw": "may write",
    "me": "may execute",
    "ms": "may share",
    "gd": "stack segment grows down",
    "pf": "pure PFN range",
    "dw": "disabled write to the mapped file",
    "lo": "pages are locked in memory",
    "io": "memory mapped I/O area",
    "sr": "sequential read advise provided",
    "rr": "random read advise provided",
    "dc": "do not copy area on fork",
    "de": "do not expand area on remapping",
    "ac": "area is accountable",
    "nr": "swap space is not reserved for the area",
    "ht": "area uses huge tlb pages",
    "nl": "non-linear mapping",
    "ar": "architecture specific flag",
    "dd": "do not include area into core dump",
    "sd": "soft-dirty flag",
    "mm": "mixed map area",
    "hg": "huge page advise flag",
    "nh": "no-huge page advise flag",
    "mg": "mergeable advise flag",
}


def main_info(pid: int, args: argparse.Namespace) -> None:
    if args.raw:
        filename = os.path.join("/proc", str(pid), "smaps")
        with open(filename, "r") as fin:
            sys.stdout.write(fin.read())
    else:
        infos = MemoryRegion.regions_from_pid(pid)
        infos = filter_memory_maps(args, infos)
        total = 0
        for info in infos:
            total += info.length()
            print(info)
            if args.verbose:
                for k, v in info.info.items():
                    print("    {:18}: {:>10}".format(k, bytefmt.humanize(v, style="binary")))

                if False:
                    print("    {:18}: {}".format("VmFlags", " ".join(info.vmflags)))  # type: ignore[unreachable]
                else:
                    print("    {}:".format("VmFlags"))
                    for flag in info.vmflags:
                        print("        {} - {}".format(flag, vmflags_to_doc[flag]))
                print()
        print("-" * 72)
        print("Total: {} - {} bytes".format(bytefmt.humanize(total, style="binary"), total))


# EOF #
