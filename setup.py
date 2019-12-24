# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import glob
import shutil
import sys
from distutils.core import setup

import requests

import py2exe  # NOQA: F401
try:
	import speechlight
except ImportError:
	speechlight = None
	print("Warning, Speechlight not found.")

from constants import APP_NAME, APP_VERSION, AUTHOR
from manifest import MANIFEST_TEMPLATE, RT_MANIFEST

# If run without args, build executables, in quiet mode.
if len(sys.argv) == 1:
	sys.argv.append("py2exe")
	sys.argv.append("-q")

try:
	# py2exe 0.6.4 introduced a replacement modulefinder.
	# This means we have to add package paths there, not to the built-in one.
	# If this new modulefinder gets integrated into Python, then we might be able to revert this some day.
	# if this doesn't work, try import modulefinder
	try:
		import py2exe.mf as modulefinder
	except ImportError:
		import modulefinder
	import dateutil
	for p in dateutil.__path__[1:]:
		modulefinder.AddPackagePath("dateutil", p)
except ImportError:
	pass


class Target(object):
	def __init__(self, **kw):
		self.__dict__.update(kw)
		# for the versioninfo resources
		self.version = APP_VERSION
		self.company_name = ""
		self.copyright = AUTHOR
		self.name = APP_NAME


program = Target(
	# used for the versioninfo resource
	description="{} {}".format(APP_NAME, APP_VERSION),
	# what to build
	script="{}.pyw".format(APP_NAME),
	other_resources=[(RT_MANIFEST, 1, MANIFEST_TEMPLATE % dict(prog=APP_NAME))],
	dest_base=APP_NAME
)


excludes = [
	"_gtkagg",
	"_tkagg",
	"bsddb",
	"curses",
	"pywin.debugger",
	"pywin.debugger.dbgcon",
	"pywin.dialogs",
	"tcl",
	"Tkconstants",
	"Tkinter",
	"pdbunittest",
	"difflib",
	"pyreadline",
	"optparse",
	"pickle",
]


packages = [
	"bs4",
	"calendar",
	"dateutil",
	"googlemaps",
	"requests",
	"encodings.hex_codec",
	"encodings.ascii",
	"encodings.utf_8",
]

if speechlight is not None:
	packages.append("speechlight")

dll_excludes = [
	"libgdk-win32-2.0-0.dll",
	"libgobject-2.0-0.dll",
	"tcl84.dll",
	"tk84.dll",
	"MSVCP90.dll",
	"mswsock.dll",
	"powrprof.dll",
	"python23.dll",
	"_sre.pyd",
	"_winreg.pyd",
	"unicodedata.pyd",
	"zlib.pyd",
	"wxc.pyd",
	"wxmsw24uh.dll",
	"w9xpopen.exe",
]


options = {
	"py2exe": {
		"dist_dir": "{} V{}".format(APP_NAME, APP_VERSION),
		"bundle_files": 2,
		"ascii": True,
		"compressed": True,
		"optimize": 2,
		"excludes": excludes,
		"packages": packages,
		"dll_excludes": dll_excludes,
	}
}


# Remove the build folder if it exists.
shutil.rmtree("build", ignore_errors=True)
# do the same for dist folder if it exists.
shutil.rmtree(options["py2exe"]["dist_dir"], ignore_errors=True)


data_files = [
	(".", [requests.certs.where()]),
	("sounds", glob.glob("sounds\\*"))
]

if speechlight is not None:
	data_files.append(("speech_libs", glob.glob("{}\\*.dll".format(speechlight.where()))))

setup(
	options=options,
	zipfile=None,
	windows=[program],
	data_files=data_files,
)

# Remove the build folder since we no longer need it.
shutil.rmtree("build", ignore_errors=True)
