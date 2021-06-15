#!/usr/bin/env bash
# Usage: gen_channel_conf.sh <management channel ip> <user channel ip>
# The management/user channel IPs are addresses for the device on that channel.
# They must not conflict with another device's IP allocation on the channel subnet.

mgmt_ipv4="$1"
user_ipv4="$2"

config_dir=/root/.config/chameleon
mkdir -p "$config_dir"
pushd "$config_dir"

mgmt_key="$(wg genkey)"
user_key="$(wg genkey)"

# Management channel config

if [ ! -e mgmt.channel ]; then
  cat >mgmt.channel <<EOF
[Interface]
PrivateKey = $mgmt_key

[Peer]
PublicKey = 88w0zYhwnVxq9BXNwrinYRpEqmrNujCFdWigTf/MTXE=
AllowedIPs = 10.0.0.2/32, 10.20.111.10/32, 10.20.111.11/32
Endpoint = 129.114.34.129:51820
PersistentKeepalive = 25
EOF

fi
echo "$mgmt_ipv4"/24 >mgmt.ipv4
echo "10.20.110.0/23 via 10.0.0.2" >mgmt.routes

# User channel config
if [ ! -e user.channel ]; then
  cat >user.channel <<EOF
[Interface]
PrivateKey = $user_key

[Peer]
PublicKey = Vc8OzWeU3uSZgUs7xw1uG55r3YmvHxQnyPwOwq5dfQM=
AllowedIPs = 10.0.1.0/24
Endpoint = 129.114.34.129:57513
PersistentKeepalive = 25
EOF

fi
echo "$user_ipv4"/24 >user.ipv4

cat <<EOF
Management channel:
  Peer: $(wg pubkey <<<"$mgmt_key")
  Allowed-IPs: ${mgmt_ipv4}/32

User channel:
  Peer: $(wg pubkey <<<"$user_key")
  Allowed-IPs: ${user_ipv4}/32
EOF
