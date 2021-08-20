#!/bin/bash

set -euf -o pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Change these to match your set up.
MAC='58:93:d8:ab:cd:ef'
GRAPHITE_HOST='127.0.0.1'
PREFIX="airthings.waveplus.office"

cd "$DIR"
pipenv run python3 ./collect.py "$MAC" "$GRAPHITE_HOST" "$PREFIX"
