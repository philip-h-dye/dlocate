import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import dlocate

# Theen, within the individual test modules, import the module like so:
#
#   from .context import dlocate
