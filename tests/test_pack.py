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

import unittest

from procmem.pack import text2bytes


class PackTestCase(unittest.TestCase):

    def test_text2bytes(self) -> None:
        self.assertEqual(text2bytes("de ad", "bytes"), b'\xde\xad')
        self.assertEqual(text2bytes("StringTest", "string"), b'StringTest')
        self.assertEqual(text2bytes("StringTest", "string0"), b'StringTest\x00')

        self.assertEqual(text2bytes("5", "<i16"), b'\x05\x00')
        self.assertEqual(text2bytes("5", ">i16"), b'\x00\x05')

        self.assertEqual(text2bytes("5", "<int16"), b'\x05\x00')
        self.assertEqual(text2bytes("5", ">int16"), b'\x00\x05')

        self.assertEqual(text2bytes("5", "<int32"), b'\x05\x00\x00\x00')
        self.assertEqual(text2bytes("5", ">int32"), b'\x00\x00\x00\x05')

        self.assertEqual(text2bytes("12345.67", "<float"), b'\xae\xe6@F')
        self.assertEqual(text2bytes("12345.67", "<double"), b')\\\x8f\xc2\xd5\x1c\xc8@')


# EOF #
