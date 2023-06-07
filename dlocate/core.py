# ------------------------------------------------------------------------------

import sys
import pty
import os
import io
import platform

import argparse

import inspect

# ------------------------------------------------------------------------------

from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from collections import namedtuple

# ------------------------------------------------------------------------------

# A pointer to the module object instance itself - to assign 'Config' & 'Drive'
_module = sys.modules[__name__]

# ------------------------------------------------------------------------------

default_applications = {
    'updatedb': '/usr/local/bin/updatedb', 'locate': '/usr/local/bin/locate'
}

# defaults   = { 'db_file_model'  :  '/usr/local/var/mlocate/mlocate{}.db'

defaults = {
    'db_file_model': '/usr/local/var/mlocate/{}.db',
    'default_drive': 'all'
}

# Assigned with options in load_config() based on application name
Config = None
Drive = None

# ------------------------------------------------------------------------------

# Usage: updatedb [OPTION]...
# Update a mlocate database.
#
options = {
    'updatedb':
    ['add_prunefs'             # --add-prunefs FS           omit also FS
     , 'add_prunenames'          # --add-prunenames NAMES     omit also NAMES
     , 'add_prunepaths'          # --add-prunepaths PATHS     omit also PATHS
     # --database-root PATH       the subtree to store in database (default "/")
     , 'database_root', 'output'                  # --output FILE              database to update (default ...)
     , 'prune_bind_mounts'       # --prune-bind-mounts FLAG   omit bind mounts (default "no")
     , 'prunefs'                 # --prunefs FS               filesystems to omit from database
     , 'prunenames'              # --prunenames NAMES         directory names to omit from database
     , 'prunepaths'              # --prunepaths PATHS         paths to omit from database
     , 'require_visibility'      # --require-visibility FLAG  check visibility before reporting files
     , 'verbose'                 # --verbose                  print paths of files as they are found
     ]    #
    # *** Not applicable - or at least I can't imagine how these could be useful in a configuration file.
    #
    # *** Not applicable - or at least I can't imagine why either would be useful in a configuration file.
    #   -h, --help                     print this help
    #   -V, --version                  print version information
    #
    # The configuration defaults to values read from
    # `/usr/local/etc/updatedb.conf'.
    #
    # Report bugs to mitr@redhat.com.
    #
    #   Usage: locate [OPTION]... [PATTERN]...
    #   Search for entries in a mlocate database.
    #
    , 'locate':
    [   'all'                     # --all              only print entries that match all patterns
      , 'basename'                # --basename         match only the base name of path names
      , 'count'                   # --count            only print number of found entries in db
      , 'database'                # --database DBPATH  use DBPATH instead of default database (...)
      , 'existing'                # --existing         only print entries for currently existing files
      , 'follow'                  # --follow           follow trailing symbolic links when checking file existence (default)
      , 'ignore_case'             # --ignore-case      ignore case distinctions when matching patterns
      , 'limit'                   # --limit, -n LIMIT  limit output (or counting) to LIMIT entries
      , 'nofollow'                # --nofollow, -H     don't follow trailing symbolic links when checking file existence
      , 'null'                    # --null             separate entries with NUL on output
      , 'statistics'              # --statistics       don't search for entries, print statistics about each used database
      , 'quiet'                   # --quiet            report no error messages about reading databases
      , 'regexp'                  # --regexp REGEXP    search for basic regexp REGEXP instead of extended regexps
      , 'wholename'               # --wholename        match whole path name (default)
     ]
}
#
# *** Not applicable - or at least I can't imagine how these could be useful in a configuration file.
#   -m, --mmap             ignored, for backward compatibility
#   -s, --stdio            ignored, for backward compatibility
#   -h, --help             print this help
#   -V, --version          print version information
#
#   Report bugs to mitr@redhat.com.

# ------------------------------------------------------------------------------

default_config_file = '~/.updatedb.rc'

# ------------------------------------------------------------------------------

# {'drive': [ {'root': '/', 'name': 'slash', 'add_prunepaths': '/a /b ...'}
#           , {'root': '/c', 'name': 'c', 'add_prunepaths': '/c/-/cygwin'}
#           , {'root': '/c/-', 'name': 'dash', 'add_prunepaths': '/c/-/cygwin'}
#           , {'root': '/c/Anaconda/mini', 'name': 'conda'}
#           , ...
#           ]


def z_if_none(x):
    return ' ' + x if x is not None else ''


def optmix(data, opt, outer):
    inner = None
    if opt in data:
        inner = data[opt]
    if not opt.startswith('add_'):
        return inner if (inner is not None) else outer
    # additive
    if outer is None:
        return inner
    return outer + z_if_none(inner)


def parse_a_drive(ctx, data):
    if 'name' not in data or 'root' not in data:
        print('Warning:  drive found without name or root :')
        print('- - - - -')
        print(data)
        print('- - - - -')
        return None
    if 'alias' not in data:
        data['alias'] = []
    else:
        data['alias'] = data['alias'].split(' ')
    args = [data['name'], data['root'], data['alias']]
    # for option in defaults.keys() + ctx['options'] :
    for option in list(defaults.keys()) + ctx['options']:
        # args.append ( data [ option ] if ( option in data ) else ctx['globals'][option] )
        args.append(optmix(data, option, ctx['globals'][option]))

    # Add 'db_file' value
    option = 'db_file_model'
    db_file_model = optmix(data, option, ctx['globals'][option])
    args.append(db_file_model.format(data['name']))

    drive = Drive(*args)
    # print(drive)
    # print('')
    return drive


def parse_drives(ctx, list):
    drives = {}
    aliasdb = {}
    for drive_data in list:
        drive = parse_a_drive(ctx, drive_data)
        if drive is not None:
            drives[drive.name] = drive
            for alias in drive.alias:  # often empty as aliases aren't common
                if alias in aliasdb:
                    print('Warning:  duplicate drive alias encountered - ignoring.')
                    print(
                        '*** existing alias :  %s => %s' %
                        (alias, aliasdb[alias]))
                    print(
                        '*** duplicate alias :  %s => %s' %
                        (alias, drive.name))
                else:
                    aliasdb[alias] = drive.name
    # print 'Aliases : {'
    # for alias in sorted ( aliasdb.keys() ) :
    #     print ( "  %-30s  =>  %s" % ( alias, aliasdb[alias] ) )
    # print '}'
    return (drives, aliasdb)

# ------------------------------------------------------------------------------

def parse_an_application(ctx, data):
    # Allow only for '<name> : <exec>'
    if len(data) != 1:
        # Warning ...
        return (None, None)
    return (list(data.keys())[0], list(data.values())[0])


def parse_applications(ctx, applications, list):
    for elt in list:
        name, exe = parse_an_application(ctx, elt)
        if name is not None:
            applications[name] = exe
    return applications

# ------------------------------------------------------------------------------


def load_config(app_name, config_file = None):

    if not config_file :
        config_file = default_config_file

    os_name = platform.system()
    if os_name.startswith('CYGWIN_') :
        os_name = 'Cygwin'
    
    # print ( 'load_config("%s") :' % ( app_name ) )

    ctx = {'app_name': app_name, 'options': options[app_name], 'globals': {}}

    _module.Config = namedtuple('Config',
                                ['app_name',
                                 'app_exec',
                                 'drives',
                                 'aliasdb'] + list(defaults.keys()) + ctx['options'])

    _module.Drive = namedtuple('Drive', ['name', 'root', 'alias']
                               + list(defaults.keys()) + ctx['options'] + ['db_file'])

    # 'io.open' was 'file'
    data = load(
        stream=io.open(
            os.path.expanduser(config_file),
            'r'),
        Loader=Loader)

    # extract OS keys to top level
    if os_name not in data['os'] :
        raise ValueError(f"OS name '{os_name}' not found under 'os' in {config_file}")
    data.update(data['os'][os_name])
    del data['os']

    args = []

    for key in defaults.keys():
        ctx['globals'][key] = data[key] if (key in data) else defaults[key]
        args.append(ctx['globals'][key])

    for opt in ctx['options']:
        ctx['globals'][opt] = data[opt] if (opt in data) else None
        args.append(ctx['globals'][opt])

    drives = []
    aliasdb = []
    app_exe = default_applications.copy()
    
    for key in data:  # !@# .iterkeys() :
        if key == 'drives':
            (drives, aliasdb) = parse_drives(ctx, data[key])
        if key == 'applications':
            app_exe = parse_applications(ctx, app_exe, data[key])

    args.insert(0, aliasdb)
    args.insert(0, drives)
    args.insert(0, app_exe[app_name])
    args.insert(0, app_name)

    return Config(*args)

# ------------------------------------------------------------------------------

def drive_options(config, drive):

    # drive_specifier = ''
    # if drive.name != config.default_drive :
    drive_specifier = drive.name
    if False:  # True :
        drive_specifier = '.' + drive_specifier

    drive_option = drive._asdict()
    drive_keys = list(drive_option.keys())

    options = [ drive.db_file ]

    # drive_keys.remove ( 'name' )
    # drive_keys.remove ( 'alias' )
    # drive_keys.remove ( 'root' )
    for key in ['root', 'name', 'alias', 'db_file'] + list(defaults.keys()):
        drive_keys.remove(key)

    for key in drive_keys:
        value = drive_option[key]
        if value is not None:
            values = [ ]
            for elt in value.split(' '):
                values.append ( os.path.expanduser(elt) )
            values = ' '.join(values)
            options.append('--' + key.replace('_', '-') + f"={values}")

    return options

# ------------------------------------------------------------------------------

if __name__ == '__main__':

    if True:
        config = load_config('updatedb')
        print(config)
        print('')

    if True:
        print('')
        print('')

    if True:
        config = load_config('locate')
        print(config)
        print('')

# ------------------------------------------------------------------------------
