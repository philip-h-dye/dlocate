import unittest

from dlocate    import load_config

#------------------------------------------------------------------------------

class Test_Case ( unittest.TestCase ) :
    
    def test_config_updatedb ( self ) :
        config = load_config('updatedb')
        self.assertGreater ( len(config), 15 )

    def test_config_locate ( self ) :
        config = load_config('locate')
        self.assertGreater ( len(config), 15 )

#------------------------------------------------------------------------------
