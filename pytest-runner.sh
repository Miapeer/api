#!/bin/bash

if pytest -m only --collect-only -q 2>/dev/null | grep "no tests collected"; then
  pytest "$@"
else
  pytest -m only "$@"
fi
