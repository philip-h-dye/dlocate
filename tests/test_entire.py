import unittest
import sys
import os

import tempfile
import filecmp
import shutil

from pathlib import Path

from plumbum import local, FG, BG, RETCODE

from plumbum.cmd import find, diff, cat, wc, sort

from dlocate.updatedb import main as update
from dlocate.locate import main as locate

#------------------------------------------------------------------------------

test_name = 'example'
directories_name = 'directories'
files_name = 'files'

test_name_exists = os.access( test_name, os.W_OK )

expect_dir = os.path.join( 'tests/expect', test_name )

expected_directories_path = os.path.join( expect_dir, directories_name )
expected_files_path = os.path.join( expect_dir, files_name )

#------------------------------------------------------------------------------

test_home = os.path.join ( os.getcwd(), test_name )

test_home_exists = os.access( test_home, os.W_OK )

# os.environ['HOME'] = test_home
local.env.home = test_home

# test_home_dirs_ok = os.access( test_home, os.W_OK )

#------------------------------------------------------------------------------

scratch_dir_obj = tempfile.TemporaryDirectory()
scratch_dir = scratch_dir_obj.name

writable_scratch_dir = os.access( scratch_dir, os.W_OK )

#------------------------------------------------------------------------------

def get_files ( startpath, prune_paths ):
    collected = [ ]
    for root, dirs, files in os.walk(startpath):
        collected.append(root)
        if root in prune_paths :
            continue
        for file in files :
            path = os.path.join ( root, file )
            for prune in prune_paths :
                if path.startswith(prune+'/') :
                    continue
            collected.append ( path )
    return collected

def sorted_files ( startpath, prune_paths = None ) :
    return sorted ( get_files ( startpath, prune_paths ) )

def file_lines ( file ) :
    stdout = ( cat[file] | wc['-l'] )()
    stdout = stdout.strip()
    return int ( stdout )

def lines ( file ) :
    with open(file, 'r') as f :
        return f.read().splitlines()

def remove_tree_or_file(path):
    print(f": removing '{path}'")
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

#------------------------------------------------------------------------------

class Test_Case ( unittest.TestCase ) :

    def execute ( self, args, output_file = None ) :
        ( retcode, stdout, stderr ) = local[ args[0] ].run( args[1:] )
        if output_file :
            with open(output_file, 'w') as f :
                if stdout :
                    f.write ( stdout )
                if stderr :
                    f.write ( "[stderr]\n" )
                    f.write ( stderr )
        if retcode :                
            self.assertFalse ( f"Command failed:  {' '.join(args)}\n\n{stdout}\n\n[stderr]\n{stderr}" )

    def execute_fg ( self, args ) :
        retcode = local[ args[0] ][ args[1:] ] & RETCODE ( FG = True )
        if retcode :                
            self.assertFalse ( f"Command failed:  {' '.join(args)}" )

    def execute_and_compare ( self, what, args ) :
        scratch_file = os.path.join( scratch_dir, what )
        expect_file  = os.path.join( expect_dir, what )
        self.execute ( args, scratch_file )
        if not filecmp.cmp ( scratch_file, expect_file ) :
            diff[ expect_file, scratch_file ] & FG ( retcode = None )
            self.assertFalse ("List of files found does not match expected.")

    def execute_sort_and_compare ( self, what, args ) :
        scratch_file = os.path.join( scratch_dir, what )
        scratch_sorted = os.path.join( scratch_dir, what+'.sorted' )
        expect_file  = os.path.join( expect_dir, what )
        expect_sorted = os.path.join( expect_dir, what+'.sorted' )
        (cat[expect_file] | sort > expect_sorted) & FG ( retcode = None )
        self.execute ( args, scratch_file )
        (cat[scratch_file] | sort > scratch_sorted) & FG ( retcode = None )
        if not filecmp.cmp ( expect_sorted, scratch_sorted ) :
            diff[ expect_sorted, scratch_sorted ] & FG ( retcode = None )
            self.assertFalse ("List of files found does not match expected.")

    def count_database_entries ( self, args = None ) :
        if not args :
            args = [ '-r', '.' ]
        cmd = local['scripts/dlocate']
        stdout = ( cmd[args] | wc['-l'] ) ()
        stdout = stdout.strip()
        return int ( stdout )

    # restore to pristine state
    def pristine(self):
        found = sorted_files ( test_name, prune_paths = [ 'example/var', 'example/alt' ] )
        expect = sorted ( lines(expected_directories_path) + lines(expected_files_path) )
        with open('log/error/found', 'w') as f :
            f.write( "\n".join(found+['']) )
        with open('log/error/expect', 'w') as f :
            f.write( "\n".join(expect+['']) )
        while len(found) and len(expect) :
            print(f": '{found[-1]}' vs '{expect[-1]}'")
            if found[-1] == expect[-1] :
                found.pop()
                expect.pop()
                continue
            if found[-1] > expect[-1] :
                remove_tree_or_file(found[-1])
                found.pop()
            else :
                print(f"*** missing '{expect[-1]}'")
                # recreate ...
                expect.pop()
        for elt in found :
            remove_tree_or_file(elt)
            pass
        for elt in expect :
            print(f"*** missing '{elt}'")
            # recreate ...

    def setUp(self) :

        self.pristine()

        self.initial = {}

        # delete all mlocate_database files
        self.execute ( [ 'find', test_name, '-name', '*.db', '-delete' ] )

        # verify against expected directories
        self.execute_sort_and_compare ( 'directories', [ 'find', test_name, '-type', 'd' ] )
        self.initial['directories_path'] = os.path.join(expect_dir, 'directories')
        self.initial['directories_n'] = file_lines ( self.initial['directories_path'])
        self.assertEqual ( self.initial['directories_n'], 8 )

        # verify against expected files
        self.execute_sort_and_compare ( 'files', [ 'find', test_name, '-type', 'f' ] )
        self.initial['files_path'] = os.path.join(expect_dir, 'files')
        self.initial['files_n'] = file_lines ( self.initial['files_path'])
        self.assertEqual ( self.initial['files_n'], 17 )

        self.initial['elements_n'] = self.initial['directories_n'] + self.initial['files_n']

    # restore to pristine state
    def tearDown(self):
        # pristine(self)
        pass

    def initial_index_and_count(self):
        self.execute_fg ( ['scripts/dupdatedb', '--show', '--require-visibility', '0'] )

        db_file = os.path.join(test_home, 'var/mlocate/entire.db' )
        self.assertTrue ( os.path.exists ( db_file ), f"mlocate database '{db_file}' not created." )

        n_entries = self.count_database_entries()
        self.assertEqual ( n_entries, self.initial['elements_n'] - 2 )
        # -2 due to entire's pruning of paths ~/var ~/alt

    def SKIP_test_home ( self ) :
        self.execute_fg ( ['eargs', 'HOME' ] )
        self.assertFalse ( True )

    def test_index_and_count ( self ) :
        self.initial_index_and_count()

    def test_add_some_files ( self ) :

        self.initial_index_and_count()

        new_dir = os.path.join ( test_name, 'zzz' )
        os.makedirs(new_dir)
        self.assertTrue ( os.access ( new_dir, os.W_OK ),
                          f"New directory '{new_dir}' either does not exist or is not writable'")
        for name in [ '111', '333', '555', '777', '999' ] :
            file = os.path.join(new_dir, name)
            Path(file).touch()
            self.assertTrue ( os.access ( file, os.W_OK ),
                          f"New file '{file}' either does not exist or is not writable'")

        # reindex
        self.execute_fg ( ['scripts/dupdatedb', '--show', '--require-visibility', '0'] )
        db_file = os.path.join(test_home, 'var/mlocate/entire.db' )
        self.assertTrue ( os.path.exists ( db_file ), f"mlocate database '{db_file}' not created." )

        n_entries = self.count_database_entries()
        self.assertEqual ( n_entries, self.initial['elements_n'] - 2 + 6 )
        # -2 due to entire's pruning of paths ~/var ~/alt

#------------------------------------------------------------------------------
