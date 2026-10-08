#!/bin/sh
cd "$(dirname "$0")"
EBIN=${KOGEN_EBIN:?Set KOGEN_EBIN to the Kogen development ebin directory}
exec elixir -pa "$EBIN" adapter.exs
