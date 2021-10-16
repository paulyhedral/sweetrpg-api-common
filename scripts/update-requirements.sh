#!/bin/bash

set -e

scriptdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

pushd ${scriptdir}/..

for d in dev docs pkg tests; do
    pip-compile requirements/$d.in
done

popd
