#!/bin/sh
# Usage: wg_up.sh DEV CONFIG_NAME [MTU]
# Creates (or recreates) a Wireguard tunnel interface on DEV, configured by the
# well-known config files stored at {{ wireguard_config_dir }}/CONFIG_NAME*
# This script must be run as root.
local cfgdir="{{ wireguard_config_dir }}"
local dev="$1"
local cfg="$2"
local mtu="${3:-}"

ip link show dev "$dev" >/dev/null || ip link add dev "$dev" type wireguard
[ -n "$mtu" ] && ip link set dev "$dev" mtu "$mtu"

read ipv4 <"$cfgdir"/"$cfg".ipv4
ip addr replace "$ipv4" dev "$dev"

wg setconf "$dev" "$cfgdir"/"$cfg".channel
ip link set dev "$dev" up

local routefile="$cfgdir"/"$cfg".routes
if [ -f "$routefile" ]; then
    while IFS= read -r route; do ip route replace $route; done <"$routefile"
fi
