#!/bin/sh
# Usage: gen_key.sh DEST [PRIV_KEY]
# Saves a private key to a destination DEST. If PRIV_KEY is provided,
# this is used as the saved key; otherwise, one is generated via `wg genkey`.
echo "${2:-$(wg genkey)}" >"$1"
chmod 400 "$1"
