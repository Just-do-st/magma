#!/bin/bash
set -eu

# 定义测试程序配置数组（格式：[PUT]:[HARNESS]）
TEST_CONFIGS=(
    # 格式：[PUT]:[HARNESS]:[PRE_ARG]:[POST_ARG]
    "libpng:libpng_read_fuzzer"
    "libsndfile:sndfile_fuzzer"
    "libtiff:tiff_read_rgba_fuzzer"
    "libxml2:xmllint"
    "lua:lua"
    "openssl:server"
    "php:parser"
    "poppler:pdf_fuzzer"
    "sqlite3:sqlite3_fuzz"
)


for config in "${TEST_CONFIGS[@]}"; do
    IFS=':' read -r PUT HARNESS <<< "$config"

    TARGET=${PUT} PROGRAM=${HARNESS} MAGMA_ROOT="/home/sutong/magma" FUZZER=aflplusplus FUZZARGS="" ARGS="" SHARED=./workdir POLL=5 AFFINITY=31 ENTRYPOINT=bash TIMEOUT=24h /home/sutong/magma/tools/captain/start.sh

    echo "-----------------------------------"
done