# From https://docs.python.org/3.5/extending/newtypes.html
#
# This file is part of the Python dbtidy module. It privides the setup.
#
# Copyright (c) 2007-2020  Andrew C. Starritt
#
# The quaternion module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# The quaternion module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the quaternion module.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact details:
# starritt@gmail.com
# PO Box 3118, Prahran East, Victoria 3181, Australia.
#

import sys
from distutils.core import setup
import re

with open("dbtidy/__init__.py", 'r') as f:
    version = re.search(r'__version__ = "(.*)"', f.read()).group(1)

setup(name="dbtidy",
      version=version,
      author="Andrew Starritt",
      author_email="andrew.starritt@gmail.com",
      license="GPL3",
      description=""" Provides a means to perfrom consistant EPICS database/template file formatting """,
      packages=["dbtidy"],
      install_requires=[],
      entry_points="""
          [console_scripts]
          dbtidy=dbtidy.main:main
      """
) 

# end
