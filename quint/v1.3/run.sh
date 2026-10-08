#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
spec=${KOGEN_SPEC:?Set KOGEN_SPEC to the root of the Kogen specification repository}
for slice in approve gate recovery session; do
  XSPEC_SLICE="$root/$slice" XSPEC_BUILD="${TMPDIR:-/tmp}/kogen-v13-quint-$slice" python3 "$spec/quint/prototype/harness/xspec.py" spec
 done
