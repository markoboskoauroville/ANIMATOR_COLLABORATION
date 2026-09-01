#!/usr/bin/env bash
# Wait for a frame to arrive from the watch folder instead of checking once.
#
#     tools/wait_for.sh 14-0-CLOUD-PLATE-v1
#
# The daemon needs a few seconds to commit and push, and GitHub needs a few more
# to serve it. Checking once inside that window reports a file as missing when it
# is simply in flight, which sends everybody looking for a bug that is not there.
# On 1.9.2026 a plate was declared missing eleven seconds before it appeared.
n="$1"; [ -z "$n" ] && { echo "usage: wait_for.sh <name without extension>"; exit 2; }
for i in $(seq 1 10); do
  git pull -q --rebase origin main 2>/dev/null
  f=$(find . -path ./.git -prune -o -name "$n.*" -print 2>/dev/null | head -1)
  if [ -n "$f" ]; then
    echo "$f  (after ${i} check$([ $i -gt 1 ] && echo s))"
    exit 0
  fi
  sleep 6
done
echo "NOT FOUND after 60 seconds of checking. Now it is worth looking at the daemon."
exit 1
