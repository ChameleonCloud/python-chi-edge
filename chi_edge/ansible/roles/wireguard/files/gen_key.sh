#!/bin/sh
# Usage: gen_key.sh DEST [PRIV_KEY]
# Saves a private key to a destination DEST. If PRIV_KEY is provided,
# this is used as the saved key; otherwise, one is generated via `wg genkey`.
privkey="${2:-}"
if [ -n "$privkey" ]; then
  if [ -f "$1" ]; then
    privkey="$(cat "$1")"
  else
    privkey="$(wg genkey)"
  fi
fi
code=0
if [ -f "$1" ]; then
  if ! grep -q "$privkey" "$1"; then code=2; fi
else
  code=2
fi
echo "$privkey" >"$1"
chmod 400 "$1"
cat "$1"
exit "$code"
