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


from typing import TextIO, Optional, Iterator

import io
import sys
from contextlib import contextmanager


@contextmanager
def redirect(stdin: Optional[TextIO] = None) -> Iterator[tuple[TextIO, TextIO]]:
    """Temporarily redirect stdout, stderr and optionally stdin into
    StringIO() objects, thus allowing the testing of functions that
    make use of them without cluttering up the output.

    Example:

       stdio = io.String("This is stdin input.")
       with stdio.redirect(stdio) as (stdout, stderr):
           main(["prog", "--fake", "--argv", "--arguments"])
       print("stdout:", stdout.read())
       print("stderr:", stderr.read())

    """

    old_in, old_out, old_err = sys.stdin, sys.stdout, sys.stderr
    new_out, new_err = io.StringIO(), io.StringIO()
    new_in = sys.stdin if stdin is None else stdin
    try:
        sys.stdin, sys.stdout, sys.stderr = new_in, new_out, new_err
        yield new_out, new_err
        sys.stdout.seek(0)
        sys.stderr.seek(0)
    finally:
        sys.stdin, sys.stdout, sys.stderr = old_in, old_out, old_err


# EOF #
