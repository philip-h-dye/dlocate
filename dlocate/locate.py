#!/usr/bin/env python

import sys
import os
import signal
# import pty
import argparse

from pkg_resources import load_entry_point

from plumbum import local, FG
from plumbum.commands.processes import ProcessExecutionError

from dlocate import core as dlocate

# ------------------------------------------------------------------------------

# Usage: locate [OPTION]... [PATTERN]...
# Search for entries in a mlocate database.
#
#   -A, --all              only print entries that match all patterns
#   -b, --basename         match only the base name of path names
#   -c, --count            only print number of found entries
#   -d, --database DBPATH  use DBPATH instead of default database (which is
#                          /usr/local/var/mlocate/mlocate.db)
#   -e, --existing         only print entries for currently existing files
#   -L, --follow           follow trailing symbolic links when checking file
#                          existence (default)
#   -h, --help             print this help
#   -i, --ignore-case      ignore case distinctions when matching patterns
#   -l, --limit, -n LIMIT  limit output (or counting) to LIMIT entries
#   -m, --mmap             ignored, for backward compatibility
#   -P, --nofollow, -H     don't follow trailing symbolic links when checking file
#                          existence
#   -0, --null             separate entries with NUL on output
#   -S, --statistics       don't search for entries, print statistics about each
#                          used database
#   -q, --quiet            report no error messages about reading databases
#   -r, --regexp REGEXP    search for basic regexp REGEXP instead of patterns
#       --regex            patterns are extended regexps
#   -s, --stdio            ignored, for backward compatibility
#   -V, --version          print version information
#   -w, --wholename        match whole path name (default)
#
# Report bugs to mitr@redhat.com.

# ------------------------------------------------------------------------------


def update_database(config_file, drive, show):

    sys.argv = ['dupdatedb', '--config-file', config_file, '--drive', drive]

    if show:
        sys.argv += ['--show']

    return (load_entry_point('dlocate', 'console_scripts', 'dupdatedb')())

# ------------------------------------------------------------------------------


def prepend_drive_options(config, drive, remaining_args):

    options = dlocate.drive_options(config, drive)

    command = [config.app_exec, '--database=' + os.path.expanduser(options[0])]

    command.extend(options[1:] + remaining_args)

    return command

# ------------------------------------------------------------------------------


def main():

    # config = dlocate.load_config('locate')
    # # print ( str(config) + '\n' ) ; exit(0)

    parser = argparse.ArgumentParser(
        description="Search an mlocate database '(a database of file names).'",
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
        '--update',
        '-u',
        action='store_true',
        default=False,
        help='Update before search.  Run updatedb for the ' +
        'drive, then locate.')

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

    config = dlocate.load_config('locate', options.config_file)
    
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

    if options.update:
        update_database(options.config_file, drive_name, options.show)

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
            print("Keyboard Interrupt received, stopping ...  'locate'")
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
