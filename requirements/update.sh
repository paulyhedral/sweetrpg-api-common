#!/bin/bash

set -e

scriptdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pushd ${scriptdir}

for d in docs app tests dev; do
    pip-compile ./$d.in
done

popd
