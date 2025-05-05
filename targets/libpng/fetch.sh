#!/bin/bash
export http_proxy=http://172.17.0.1:7890
export https_proxy=http://172.17.0.1:7890

##
# Pre-requirements:
# - env TARGET: path to target work dir
##

git clone --no-checkout https://github.com/glennrp/libpng.git \
    "$TARGET/repo"
git -C "$TARGET/repo" checkout a37d4836519517bdce6cb9d956092321eca3e73b