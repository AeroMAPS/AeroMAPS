#!/bin/zsh
# Status of the tight re-run sweeps. Run from this directory:  ./sweep_status.sh
cd "$(dirname "$0")"
BUDGETS=(3_8 3_6 3_4 3_2 3_0 2_8 2_6 2_4 2_2 2_0 mincarb)

print -P "%B=== tight sweeps -> results_tight/ ===%b"
done_total=0
for c in B15 main B5 B75 pess; do
  line=""
  for b in $BUDGETS; do
    if [[ -f results_tight/opt_${c}_${b}.hdf ]]; then line+="#"; ((done_total++))
    else line+="."; fi
  done
  if ps -eo command | grep -q "[r]erun_tight.py $c"; then
    el=$(ps -eo etime,command | grep "[r]erun_tight.py $c" | awk '{print $1}')
    state="RUNNING ${el}"
  elif [[ $line == *"#"* && $line != *"."* ]]; then state="done"
  elif ps -eo command | grep -q "[q]ueue_sweeps.sh"; then state="queued"
  else state="stopped"; fi
  printf "  %-5s [%s] %-16s\n" "$c" "$line" "$state"
done
echo "  order:  3.8 3.6 3.4 3.2 3.0 2.8 2.6 2.4 2.2 2.0 minCO2   ('#'=done)"
printf "  total:  %d/55\n" $done_total

echo
print -P "%B=== machine ===%b"
printf "  load average:%s  (4 performance cores)\n" "$(uptime | sed 's/.*averages*://')"
printf "  sweeps running: %s / 2 allowed\n" "$(ps -eo command | grep -cE '[p]ython[0-9.]* -u rerun_tight[.]py')"

echo
print -P "%B=== last finished run per case ===%b"
for c in B15 main B5 B75 pess; do
  last=$(grep -hE "^ *$c +(mincarb|[0-9.]+) " tight_$c.log 2>/dev/null | tail -1 | tr -s ' ' | cut -c1-95)
  [[ -n "$last" ]] && echo "  $last"
done

echo
print -P "%B=== problems ===%b"
found=0
for f in tight_*.log; do
  [[ -s $f ]] || continue
  msg=$(grep -oE "No space left on device|MDAConvergenceError|MemoryError|Traceback" $f | head -1)
  [[ -n "$msg" ]] && { echo "  $f: $msg"; found=1; }
done
(( found )) || echo "  none"
