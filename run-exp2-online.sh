#!/usr/bin/env bash
set -e

# gaslimit = 0x1ffffff

ETH_EXP_SCRIPTS_FOLDER="/root/go-ethereum-for-experiment-scripts/Experiments"
repeat_count=30
account_num=1000 # you need more CPU cores to allow more clients submit transactions at the same time (literally)

source ./venv/bin/activate
mkdir -p ./result/exp2-online/

echo note: please manually run ./clear_output.sh and also clear ./result folder before running this script

# kill old scripts
ps -ef | grep -i "SCREEN -dm bash -c python3 ./exp2-" | grep -v 'grep' | awk '{print $2}' | xargs kill || true

for ii in $(seq 0 1 $repeat_count); do
  state_size_factor=10
  performance_factor=1000 # you need more CPU cores to allow more clients submit transactions at the same time (literally)
  sed -i 's/\(uint256 constant PerformanceFactor =\)\(.*\)/\1'"${performance_factor}"';/' ./contracts/transfer.sol
  sed -i 's/\(uint256 constant StateSizeFactor =\)\(.*\)/\1'"${state_size_factor}"';/' ./contracts/transfer.sol

  (cd "$ETH_EXP_SCRIPTS_FOLDER" && ./init_geth.sh)
  echo "exp2-online-count$ii" | (cd "$ETH_EXP_SCRIPTS_FOLDER" && ./run_geth.sh)
  echo 'sleep 5s...' && sleep 5s

  ACCOUNT_NUM=$account_num python3 ./exp2-init.py

  for i in $(seq 0 2 $(expr $account_num - 1)); do
    MY_ID=$i screen -dm bash -c 'python3 ./exp2-online.py | tee ./result/exp2-online/exp2-online-'$i-count-$ii.txt
    echo -n "Starting ($i/$account_num)             "
    printf "\r"
    sleep 0.01s
  done

  while true; do
    num=$(ps -ef | grep -i "SCREEN -dm bash -c python3 ./exp2-online.py" | grep -v 'grep' | wc -l)
    echo -n "Numbers remaining: $num                "
    printf "\r"
    if [ $num -eq 0 ]; then
      break
    fi
  done
  echo 'sleep 60s...' && sleep 60s

  cp "$ETH_EXP_SCRIPTS_FOLDER/output/exp2-online-count$ii.txt" ./result/exp2-online/
  xz ./result/exp2-online/"exp2-online-count$ii.txt"
  (cd "$ETH_EXP_SCRIPTS_FOLDER" && ./kill_geth.sh)
done
