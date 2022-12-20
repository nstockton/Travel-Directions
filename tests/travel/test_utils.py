# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


# Future Modules:
from __future__ import annotations

# Built-in Modules:
import os
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

# Travel Directions Modules:
from travel import utils


class TestUtils(TestCase):
	def test_padList(self) -> None:
		lst: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
		padding: int = 0
		# Non-fixed padding with 0's on the right.
		# Returned list will be of length >= *count*.
		self.assertEqual(utils.padList([], padding, count=12, fixed=False), [0] * 12)
		self.assertEqual(utils.padList(lst, padding, count=12, fixed=False), lst + [0] * 3)
		self.assertEqual(utils.padList(lst, padding, count=5, fixed=False), lst)
		# Fixed padding with 0's on the right.
		# Returned list will be of length == *count*.
		self.assertEqual(utils.padList([], padding, count=12, fixed=True), [0] * 12)
		self.assertEqual(utils.padList(lst, padding, count=12, fixed=True), lst + [0] * 3)
		self.assertEqual(utils.padList(lst, padding, count=5, fixed=True), lst[:5])

	@patch("travel.utils._imp")
	@patch("travel.utils.sys")
	def test_getFreezer(self, mockSys: Mock, mockImp: Mock) -> None:
		del mockSys.frozen
		del mockSys._MEIPASS
		del mockSys.importers
		mockImp.is_frozen.return_value = True
		self.assertEqual(utils.getFreezer(), "tools/freeze")
		mockImp.is_frozen.return_value = False
		self.assertIs(utils.getFreezer(), None)
		mockSys.importers = True
		self.assertEqual(utils.getFreezer(), "old_py2exe")
		del mockSys.importers
		for item in ("windows_exe", "console_exe", "dll"):
			mockSys.frozen = item
			self.assertEqual(utils.getFreezer(), "py2exe")
		mockSys.frozen = "macosx_app"
		self.assertEqual(utils.getFreezer(), "py2app")
		mockSys.frozen = True
		self.assertEqual(utils.getFreezer(), "cx_freeze")
		mockSys.frozen = "some undefined freezer"
		self.assertEqual(utils.getFreezer(), "unknown some undefined freezer")
		mockSys._MEIPASS = "."
		self.assertEqual(utils.getFreezer(), "pyinstaller")

	def test_isFrozen(self) -> None:
		self.assertIs(utils.isFrozen(), False)

	@patch("travel.utils.isFrozen")
	def test_getDirectoryPath(self, mockIsFrozen: Mock) -> None:
		subdirectory: tuple[str, ...] = ("level1", "level2")
		frozenDirName: str = os.path.dirname(sys.executable)
		frozenOutput: str = os.path.realpath(os.path.join(frozenDirName, *subdirectory))
		mockIsFrozen.return_value = True
		self.assertEqual(utils.getDirectoryPath(*subdirectory), frozenOutput)
		unfrozenDirName: str = os.path.join(os.path.dirname(utils.__file__), os.path.pardir)
		unfrozenOutput: str = os.path.realpath(os.path.join(unfrozenDirName, *subdirectory))
		mockIsFrozen.return_value = False
		self.assertEqual(utils.getDirectoryPath(*subdirectory), unfrozenOutput)

	def test_getDataPath(self) -> None:
		subdirectory: tuple[str, ...] = ("level1", "level2")
		output: str = os.path.realpath(
			os.path.join(utils.getDirectoryPath(utils.DATA_DIRECTORY), *subdirectory)
		)
		self.assertEqual(utils.getDataPath(*subdirectory), output)
