#!/usr/bin/env bash
# Convenience entry point; the maintained runner is scripts/windows_test_runner.sh.
set -Eeuo pipefail
cd "$(dirname "$0")"
exec bash scripts/windows_test_runner.sh "$@"
