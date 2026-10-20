#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Merge upstream without rewriting the public branch; never push failed changes.
set -eu
cd "$(dirname "$0")/.."
[ "$(git branch --show-current)" = lpa ] || { echo 'Switch to lpa first.' >&2; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo 'Working tree must be clean.' >&2; exit 1; }
if ! git remote get-url upstream >/dev/null 2>&1; then
    git remote add upstream https://github.com/jjdeharo/meteo-local.git
fi
case "$(git remote get-url upstream)" in
    https://github.com/jjdeharo/meteo-local.git|git@github.com:jjdeharo/meteo-local.git) ;;
    *) echo 'Unexpected upstream remote; inspect it first.' >&2; exit 1 ;;
esac
git fetch upstream main
git merge --no-edit upstream/main
TZ=Europe/Madrid python3 -m unittest discover -s tests -b
python3 -m unittest discover -s lpa/tests -v
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT
python3 -m lpa.build "$build_dir"
printf '%s\n' 'Checks passed. Review git log and git diff upstream/main...lpa, then git push origin lpa.'
