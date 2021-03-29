#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


# Future Modules:
from __future__ import annotations

# Built-in Modules:
import logging
import sys
import traceback

# Travel Directions Modules:
import src.main


VERSION: str
try:
	import travel_directions_version  # type: ignore[import]
except ImportError:
	VERSION = "Unknown Version"
else:
	VERSION = travel_directions_version.VERSION
finally:
	VERSION += f" - Python {'.'.join(str(i) for i in sys.version_info[:3])} {sys.version_info.releaselevel}"


if __name__ == "__main__":
	try:
		src.main.main(VERSION)
	except Exception:
		traceback.print_exc()
		logging.exception("OOPS!")
	finally:
		logging.info("Shutting down.")
		logging.shutdown()
