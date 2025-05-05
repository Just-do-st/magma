#!/bin/bash
export http_proxy=http://172.17.0.1:7890
export https_proxy=http://172.17.0.1:7890

##
# Pre-requirements:
# - env TARGET: path to target work dir
##

git clone --no-checkout https://github.com/libsndfile/libsndfile.git \
    "$TARGET/repo"
git -C "$TARGET/repo" checkout 86c9f9eb7022d186ad4d0689487e7d4f04ce2b29