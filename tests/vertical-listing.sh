#!/bin/bash

binDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

test_py=test_load_config.py

${binDir}/${test_py} \
    | sed -e "s/\(, drives={\)/\n\1/;s/\('[a-z][a-z]*': Drive\)/\n\n\1/g;s/)[}]/)\n\n}\n/g;s/,/\n\t,/g;s/\t\(, drives={\)/\1/"

