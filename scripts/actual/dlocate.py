#!/usr/bin/env python
# EASY-INSTALL-ENTRY-SCRIPT: 'dlocate','console_scripts','dlocate'
__requires__ = 'dlocate'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('dlocate', 'console_scripts', 'dlocate')()
    )
