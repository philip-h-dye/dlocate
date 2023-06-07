#!/usr/bin/env python

import sys
import os
import signal
# import pty
import argparse

from plumbum import local, FG
from plumbum.commands.processes import ProcessExecutionError

from dlocate import core as dlocate

# ------------------------------------------------------------------------------

# Usage: updatedb [OPTION]...
# Update a mlocate database.
#
#   -f, --add-prunefs FS           omit also FS
#   -n, --add-prunenames NAMES     omit also NAMES
#   -e, --add-prunepaths PATHS     omit also PATHS
#   -U, --database-root PATH       the subtree to store in database (default "/")
#   -h, --help                     print this help
#   -o, --output FILE              database to update (default
#                                  `/usr/local/var/mlocate/mlocate.db')
#       --prune-bind-mounts FLAG   omit bind mounts (default "no")
#       --prunefs FS               filesystems to omit from database
#       --prunenames NAMES         directory names to omit from database
#       --prunepaths PATHS         paths to omit from database
#   -l, --require-visibility FLAG  check visibility before reporting files
#                                  (default "yes")
#   -v, --verbose                  print paths of files as they are found
#   -V, --version                  print version information
#
# The configuration defaults to values read from
# `/usr/local/etc/updatedb.conf'.
#
# Report bugs to mitr@redhat.com.

# ------------------------------------------------------------------------------


def prepend_drive_options(config, drive, remaining_args):

    options = dlocate.drive_options(config, drive)

    command = [config.app_exec,
               '--database-root={}'.format(os.path.expanduser(drive.root)),
               '--output=' + os.path.expanduser(options[0])]

    command.extend(options[1:] + remaining_args)

    return command

# ------------------------------------------------------------------------------


def main():

    parser = argparse.ArgumentParser(
        description='Update a mlocate database (a database of file names).',
        add_help=False)

    parser.add_argument(
        '--config-file',
        '--config',
        '--rc',
        help='Specifies the file name of the configuration file (rather than ~/.updatedb.rc)')

    parser.add_argument(
        '--drive',
        '-d',
        help='Specifies the name of an alternate drive or ' +
        'area to scan rather than "/".')

    parser.add_argument(
        '--show',
        action='store_true',
        default=False,
        help='Show command line before executing')

    parser.add_argument(
        '--print',
        action='store_true',
        default=False,
        help='Show database path then exit without doing any work.')

    options, remaining_args = parser.parse_known_args()

    if options.config_file is None:
        options.config_file = dlocate.default_config_file

    config = dlocate.load_config('updatedb', options.config_file)

    if options.drive is None:
        options.drive = config.default_drive

    drive_name = options.drive
    if drive_name in config.aliasdb:
        drive_name = config.aliasdb[drive_name]

    if drive_name not in config.drives:
        print(
            "Drive '{}' not recognized.  Is it present in the configuration file, '{}'." .format(
                drive_name, options.config_file ))
        return (1)

    if options.print :
        print(config.drives[drive_name].db_file)
        return 0

    command = prepend_drive_options(
        config, config.drives[drive_name], remaining_args)

    if options.show:
        print("+ '" + "' '".join(command) + "'")

    # pty.spawn ( command )
    # return ( 0 )

    argv = command[1:]
    command = command[0]
    command = local[command]

    try:

        try:
            command[argv] & FG
            return 0

        except KeyboardInterrupt:
            print("Keyboard Interrupt received, stopping ...  'updatedb'")
            if sys.platform == "win32":
                from win32api import GenerateConsoleCtrlEvent
                GenerateConsoleCtrlEvent(0, 0)  # send Ctrl+C to current TTY
            else:
                os.killpg(os.getpgrp(), signal.SIGINT)

    except KeyboardInterrupt:
        return 3

    except ProcessExecutionError as e:
        return e.retcode

# ------------------------------------------------------------------------------
