""" The module provides the command line interface to dbtidy.
    It parses areguments, and does backup file management.
"""

import os.path
import sys
import shutil
import traceback

from . import __version__
from . import common
from . import dbtidy_lib
from . import lexer


def process_argument(filename):
    try:
        backup = filename + ".~"

        print(filename)

        # Create a backup file.
        # Note: we copy, as opposed to do moving original to create the back up
        # and then creating a new file, and then process from the backup back to the
        # original file. In this way, filename remains the same file and gets updated.
        # This preserves attributes and, at least on Linux, the inode number, and any
        # file system hard linking to the file is preserved.
        #
        shutil.copy(filename, backup)

        # Save as a global, to support any diagnostic/error messages.
        #
        common.source_file_name = filename

        dbtidy_lib.process_file(backup, filename)

    except Exception:
        traceback.print_exc()


def print_version():
    """ Print version
    """
    vi = sys.version_info
    print("dbtidy version: %s  (python %s.%s.%s)" %
          (__version__, vi.major, vi.minor, vi.micro))


# The command line structure is too simple to warrent using Click.
#
def main():
    name = os.path.basename(sys.argv.pop(0))    # drop the program name

    if len(sys.argv) >= 1:
        if sys.argv[0] in ("-h", "--help"):
            print("""\
{name} version {version}

usage: {name} filenames...
       {name} -h, --help
       {name} -V, --version

{name} perform a standard layout formatting on one or more EPICS database,
template and/or dbd files. Prior to formating, a backup copy of each file
is created with the name '<filename>.~'.

Note: {name} does not handle extended fields and extended info structures
very well (yet).

Copyright (c) 2007-2022  Andrew C. Starritt

Transcoded from original Ada dbtidy program to Python in 2020, which
itself was based loosely on my Delphi Pascal tidy program.
""".format(version=__version__, name=name))
            return

        if sys.argv[0] in ("-V", "--version"):
            print_version()
            return

    print_version()

    for filename in sys.argv:
        process_argument(filename)

    if len(sys.argv) == 0:
        print("no files specified")
    else:
        print("complete")

# end
