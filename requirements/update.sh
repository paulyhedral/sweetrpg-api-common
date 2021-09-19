#!/bin/bash

set -e

scriptdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pushd ${scriptdir}

for d in docs pkg tests dev; do
    pip-compile ./$d.in
done

popd
