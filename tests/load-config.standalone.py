#!/bin/python

import sys

#------------------------------------------------------------------------------

# from .context         import dlocate
# from dlocate  import load_config

sys.path.insert(0,'.')
sys.path.insert(0,'..')
# 
from dlocate    import load_config

#------------------------------------------------------------------------------

if __name__ == '__main__' :

    if True :
        config = load_config('updatedb')
        print (config)
        print ('')

    if True :
        print ('')
        print ('')
    
    if True :
        config = load_config('locate')
        print (config)
        print ('')

#------------------------------------------------------------------------------
