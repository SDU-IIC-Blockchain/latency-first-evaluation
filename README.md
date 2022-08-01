
## Prerequisite
Download the solidity compiler [here](https://github.com/ethereum/solidity/releases) and place the executable at `/usr/local/bin/solc`.
Version: 0.8.15+commit.e14f2714.Linux.g++

## kernel.pid_max & ulimits

Linux kernel has a limitation on maximum number of process in order to prevent fork bombs.

For experiment 2, the client might start a huge number of clients, in which case it will reach the limitation.

Make sure the Linux kernel is running on 64-bit mode. The value must be a power of 2, e.g. 32768. The maximum value is 4194304 for a 64-bit kernel.

To avoid some strange behaviors, the following commands and experiment 2 should be run by root, instead of `sudo`. Use `sudo -s` command to switch to root account.

```bash
echo 4194304 > /proc/sys/kernel/pid_max
ulimit -u 4194304
ulimit -n 1027204
```

To make these option persists after reboot, edit `/etc/sysctl.conf` by adding the following line:

```ini
kernel.pid_max = 4194304
```

and `/etc/security/limits.conf` file by adding the following line:

```
* soft nproc 4194304
* hard nproc 4194304
* soft nofile 1027204
* hard nofile 1027204
```

Be sure to check all files at `/etc/sysctl.d/` and `/etc/security/limits.d/` in case your configuration be overridden.