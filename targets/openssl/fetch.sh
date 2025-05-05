#!/bin/bash
export http_proxy=http://172.17.0.1:7890
export https_proxy=http://172.17.0.1:7890

##
# Pre-requirements:
# - env TARGET: path to target work dir
##

git clone --no-checkout https://github.com/openssl/openssl.git \
    "$TARGET/repo"
git -C "$TARGET/repo" checkout 3bd5319b5d0df9ecf05c8baba2c401ad8e3ba130

cp "$TARGET/src/abilist.txt" "$TARGET/repo/abilist.txt"
