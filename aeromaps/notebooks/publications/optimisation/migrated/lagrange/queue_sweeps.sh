#!/bin/zsh
# Concurrency limit. Each sweep is single-threaded (~100% of one core), and the
# machine has 4 performance cores. Measured: 5 concurrent -> ~30 min/run,
# 2 concurrent -> ~11-13 min/run, because the overflow lands on the efficiency
# cores. Keep (sweeps + other heavy processes) at or below 4.
LIMIT=${1:-3}
cd "$(dirname "$0")"
count() { ps -eo command | grep -cE '[p]ython[0-9.]* -u rerun_tight[.]py'; }
for c in B15 main B5 B75 pess; do
  # already running, or its ladder is complete? skip.
  ps -eo command | grep -q "[r]erun_tight.py $c" && { echo "skip $c (running)"; continue; }
  [ "$(ls results_tight/opt_${c}_*.hdf 2>/dev/null | wc -l | tr -d ' ')" -eq 11 ] && { echo "skip $c (done)"; continue; }
  while [ "$(count)" -ge $LIMIT ]; do sleep 30; done
  poetry run python -u rerun_tight.py $c > logs/tight_$c.log 2>&1 &
  echo "started $c at $(date +%H:%M:%S)"
  sleep 25
done
wait
echo "queue drained at $(date +%H:%M:%S)"
