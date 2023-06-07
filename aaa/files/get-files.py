#!/usr/bin/env python

import os
import sys

def get_files(startpath):
    collected = [ ]
    for root, dirs, files in os.walk(startpath):
        for file in files :            
            collected.append ( os.path.join ( root, file ) )
    return collected

print ( "\n".join ( get_files('example') ) )
