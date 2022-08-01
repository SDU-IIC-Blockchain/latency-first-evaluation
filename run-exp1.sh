#!/usr/bin/env bash
set -e
ETH_EXP_SCRIPTS_FOLDER="/root/go-ethereum-for-experiment-scripts/Experiments"

state_size_factors=(1 10 20 30 50)
performance_factors=(10 20 50 100 200 500 1000)
repeat_count=30

source ./venv/bin/activate
mkdir -p ./result/

echo note: please manually run ./clear_output.sh and also clear ./result folder before running this script

for state_size_factor in "${state_size_factors[@]}"; do
  for performance_factor in "${performance_factors[@]}"; do
    # https://stackoverflow.com/a/22819516
    sed -i 's/\(uint256 constant PerformanceFactor =\)\(.*\)/\1'"${performance_factor}"';/' ./contracts/transfer.sol
    sed -i 's/\(uint256 constant StateSizeFactor =\)\(.*\)/\1'"${state_size_factor}"';/' ./contracts/transfer.sol

    (cd "$ETH_EXP_SCRIPTS_FOLDER" && ./init_geth.sh)
    echo "exp-p${performance_factor}-s${state_size_factor}" | (cd "$ETH_EXP_SCRIPTS_FOLDER" && ./run_geth.sh)
    echo 'sleep 5s...'
    sleep 5s
    for i in $(seq 1 $repeat_count); do
      python3 ./exp1.py
    done
    echo 'sleep 30s...'
    sleep 30s
    cp "$ETH_EXP_SCRIPTS_FOLDER/output/exp-p${performance_factor}-s${state_size_factor}.txt" ./result/
    xz ./result/"exp-p${performance_factor}-s${state_size_factor}.txt"
    (cd "$ETH_EXP_SCRIPTS_FOLDER" && ./kill_geth.sh)
  done
done
