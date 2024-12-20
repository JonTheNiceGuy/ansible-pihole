#!/bin/bash
cd "$(dirname "$0")"
outfile="/tmp/$(date +%Y%m%d)-ansible-pihole.out"
touch "$outfile"
/usr/local/bin/ansible-playbook -i hosts site.yml > "$outfile" 2>&1
if grep -qE "(changed|failed|fail|fatal):" "$outfile"; then
  cat "$outfile"
  echo "See $outfile for details"
else
  rm "$outfile"
fi
