#!/bin/bash

# 配置数组：[CONTAINER_ID]:[TARGET]
TEST_CONFIGS=(
  "b6904dc5dfe7:libpng"
  "d681f8c41765:libsndfile"
  "5e5b4d6b163b:libtiff"
  "8d52393cc341:libxml2"
  "460cc8c8b126:lua"
  "e1e9f4a73bc6:openssl"
  "26b0644b283f:php"
  "41b61946fd21:poppler"
  "8786f46854d5:sqlite3"
)

# 定义 cycle 范围
CYCLES=(0 1)

# 遍历配置并执行 replay
for config in "${TEST_CONFIGS[@]}"; do
  IFS=":" read -r CONTAINER TARGET <<< "$config"
  echo "Running replay for $TARGET in $CONTAINER..."

  taskset -c 53-63 docker exec -i "$CONTAINER" bash -c "
    export TARGET=$TARGET
    # apt-get install -y python3-pip
    # export http_proxy=http://172.17.0.1:7890
    # export https_proxy=http://172.17.0.1:7890
    # pip install numpy
    for cycle in ${CYCLES[*]}; do
      for fuzzer in aflplusplus ultrafuzz aflteam afledge partionfuzz; do
        python3 /replay/crash-replay.py --threads=10 --workdir /out/magma-workdir/cycle-\$cycle \
          --experiment_out_dirs /out/\$fuzzer/\$cycle-\$fuzzer-\$TARGET/
      done
    done
  "
done


# python3 /replay/crash-replay.py --threads=1 --workdir /out/magma-workdir/cycle-0 \
#           --experiment_out_dirs /out/afledge/0-afledge-libxml2