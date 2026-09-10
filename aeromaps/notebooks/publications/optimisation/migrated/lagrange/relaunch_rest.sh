#!/bin/zsh
cd "$(dirname "$0")"
# Stagger the remaining sweeps: five simultaneous process constructions exhausted
# a transient resource last time; two are already running, so add the rest slowly.
for c in B75 B15 pess; do
  poetry run python rerun_tight.py $c > logs/tight_$c.log 2>&1 &
  echo "launched $c pid $!"
  sleep 180
done
wait
