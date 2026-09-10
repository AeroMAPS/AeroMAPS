#!/bin/zsh
cd "$(dirname "$0")"
for c in main B5 B75 B15 pess; do
  poetry run python rerun_tight.py $c > logs/tight_$c.log 2>&1 &
  sleep 120
done
wait
