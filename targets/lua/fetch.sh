#!/bin/bash
export http_proxy=http://172.17.0.1:7890
export https_proxy=http://172.17.0.1:7890

##
# Pre-requirements:
# - env TARGET: path to target work dir
##

git clone --no-checkout https://github.com/lua/lua.git "$TARGET/repo"
git -C "$TARGET/repo" checkout dbdc74dc5502c2e05e1c1e2ac894943f418c8431