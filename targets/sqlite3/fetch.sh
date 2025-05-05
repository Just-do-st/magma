#!/bin/bash
export http_proxy=http://172.17.0.1:7890
export https_proxy=http://172.17.0.1:7890

##
# Pre-requirements:
# - env TARGET: path to target work dir
##

curl "https://www.sqlite.org/src/tarball/sqlite.tar.gz?r=8c432642572c8c4b" \
  -o "$OUT/sqlite.tar.gz" && \
mkdir -p "$TARGET/repo" && \
tar -C "$TARGET/repo" --strip-components=1 -xzf "$OUT/sqlite.tar.gz"