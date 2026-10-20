#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Work only in the supplied new worktree; never rewrite application history.
set -eu
mode=$1
state=$2
case "$mode" in
  prepare)
    test ! -e "$state" || { echo 'State worktree must not already exist.' >&2; exit 1; }
    if git ls-remote --exit-code --heads origin refs/heads/lpa-data > /dev/null; then
      git fetch origin refs/heads/lpa-data
      git worktree add --detach "$state" FETCH_HEAD
    else
      result=$?
      test "$result" -eq 2 || exit "$result"
      git worktree add --detach "$state" HEAD
      git -C "$state" switch --orphan lpa-data
    fi
    ;;
  save)
    test -f "$state/.git" || { echo 'Expected a dedicated Git worktree.' >&2; exit 1; }
    git -C "$state" add --all
    if ! git -C "$state" diff --cached --quiet; then
      git -C "$state" -c user.name='github-actions[bot]' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
        commit -m 'data: record local observations and forecast verification'
      # No force push: a concurrent writer must cause a failure, not data loss.
      git -C "$state" push origin HEAD:refs/heads/lpa-data
    fi
    ;;
  *) echo 'Usage: data-branch.sh prepare|save NEW_STATE_DIRECTORY' >&2; exit 1 ;;
esac
