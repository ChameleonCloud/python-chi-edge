#!/bin/sh
# Usage: gen_key.sh DEST [PRIV_KEY]
# Saves a private key to a destination DEST. If PRIV_KEY is provided,
# this is used as the saved key; otherwise, one is generated via `wg genkey`.

# set to empty string as init.
privkey=""

# load saved key if file exists and nonempty
if [ -s "$1" ]; then
  # test if saved file is valid
  if cat "$1" | wg pubkey > /dev/null 2>&1; then
    privkey="$(cat "$1")"
  fi
fi

# load privkey from argument
arg_privkey="${2:-}"
# if key is provided as arg, override any saved key
if [ -n "$arg_privkey" ]; then
  privkey="${arg_privkey}"
fi

# generate a new key if none present
if [ -z "$privkey" ]; then
  privkey="$(wg genkey)"
fi
code=0

# check if privkey has changed
if [ -f "$1" ]; then
  if ! grep -q "$privkey" "$1"; then code=2; fi
else
  code=2
fi

# write new privkey to file
echo "$privkey" >"$1"
chmod 400 "$1"
cat "$1"
exit "$code"
