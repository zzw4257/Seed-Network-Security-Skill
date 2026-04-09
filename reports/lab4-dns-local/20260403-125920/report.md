# lab4-dns-local 实验报告

## 实验总结

- Profile: `lab4-dns-local`
- Run ID: `20260403-125920`
- 目标 VM: `seed@localhost` over port `2345`
- 当前状态: `completed`
- 说明: 自动完成材料审查、前置环境验证、实验执行、证据采集与留档。

## 材料审查表

| 项目 | 路径 | 状态 | 说明 |
| --- | --- | --- | --- |
| 本地实验指导文档 | lab4-dns/DNS 攻击实验 - 本地攻击.md | 已找到 | 必需 |
| Labsetup 目录 | lab4-dns/Labsetup_DNS_Local  | 已找到 | 必需 |
| Compose 文件 | lab4-dns/Labsetup_DNS_Local /docker-compose.yml | 已找到 | 必需 |
| 本地攻击 Scapy 样例 | lab4-dns/Labsetup_DNS_Local /volumes/dns_sniff_spoof.py | 已找到 | 必需 |

## 前置环境表

| 检查项 | 结果 | 详情 |
| --- | --- | --- |
| SSH 连通性 | 通过 | seed@localhost:2345 |
| 操作系统 | 通过 | "Ubuntu 20.04.6 LTS" |
| sudo 密码 | 通过 | 使用测试密码 dees |
| Docker Compose | 通过 | /usr/local/bin/docker-compose |
| SEED 别名 | 通过 | dcbuild is aliased to `docker-compose build'<br>dcup is aliased to `docker-compose up'<br>dcdown is aliased to `docker-compose down'<br>dockps is aliased to `docker ps --format "{{.ID}}  {{.Names}}" | sort -k 2'<br>docksh is a function<br>docksh () <br>{ <br>    docker exec -it $1 /bin/bash<br>} |
| Python 运行时 | 通过 | /usr/bin/python3<br>Python 3.8.10 |
| Docker 环境洁净度 | 注意 | 运行容器数=5; 残留网络=net-10.8.0.0<br>net-10.9.0.0 |

## 逐任务执行记录

### 1. 读取容器数量

- 状态：ok

- 说明：检查远端当前运行中的容器数量

- 面向用户的命令表达：`dockps`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker ps -q | wc -l | tr -d '"'"' '"'"''`

- 关键输出：

```text
5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/01-读取容器数量.log`

### 2. 读取残留网络

- 状态：ok

- 说明：检查远端是否存在非默认 Docker 网络

- 面向用户的命令表达：`docker network ls`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker network ls --format '"'"'{{.Name}}'"'"' | grep -Ev '"'"'^(bridge|host|none)$'"'"' || true'`

- 关键输出：

```text
net-10.8.0.0
net-10.9.0.0
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/02-读取残留网络.log`

### 3. 检查 SSH

- 状态：ok

- 说明：验证远端 SSH 登录是否可用

- 面向用户的命令表达：`whoami`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc whoami`

- 关键输出：

```text
seed
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/03-检查-ssh.log`

### 4. 读取 OS 版本

- 状态：ok

- 说明：确认远端系统版本

- 面向用户的命令表达：`grep '^PRETTY_NAME=' /etc/os-release`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'grep '"'"'^PRETTY_NAME='"'"' /etc/os-release'`

- 关键输出：

```text
PRETTY_NAME="Ubuntu 20.04.6 LTS"
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/04-读取-os-版本.log`

### 5. 验证 sudo

- 状态：ok

- 说明：验证测试 VM 的 sudo 密码

- 面向用户的命令表达：`echo dees | sudo -S -k true && echo SUDO_OK`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'echo dees | sudo -S -k true && echo SUDO_OK'`

- 关键输出：

```text
SUDO_OK
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/05-验证-sudo.log`

### 6. 定位 docker-compose

- 状态：ok

- 说明：确认 docker-compose 命令存在

- 面向用户的命令表达：`command -v docker-compose`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'command -v docker-compose'`

- 关键输出：

```text
/usr/local/bin/docker-compose
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/06-定位-docker-compose.log`

### 7. 检查交互式别名

- 状态：ok

- 说明：确认 SEED VM 常用 Docker 别名在交互 shell 中可用

- 面向用户的命令表达：`bash -ic 'type dcbuild dcup dcdown dockps docksh'`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -ic 'type dcbuild dcup dcdown dockps docksh'`

- 关键输出：

```text
dcbuild is aliased to `docker-compose build'
dcup is aliased to `docker-compose up'
dcdown is aliased to `docker-compose down'
dockps is aliased to `docker ps --format "{{.ID}}  {{.Names}}" | sort -k 2'
docksh is a function
docksh () 
{ 
    docker exec -it $1 /bin/bash
}
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
bash: cannot set terminal process group (-1): Inappropriate ioctl for device
bash: no job control in this shell
```

- 证据：`evidence/07-检查交互式别名.log`

### 8. 检查远端 Python

- 状态：ok

- 说明：确认远端只依赖 python3

- 面向用户的命令表达：`command -v python3 && python3 --version`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'command -v python3 && python3 --version'`

- 关键输出：

```text
/usr/bin/python3
Python 3.8.10
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/08-检查远端-python.log`

### 9. 重建远端工作区

- 状态：ok

- 说明：清理并重建远端标准工作区

- 面向用户的命令表达：`mkdir -p /home/seed/seed-labs/lab4-dns-local/workspace`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'rm -rf /home/seed/seed-labs/lab4-dns-local/workspace && mkdir -p /home/seed/seed-labs/lab4-dns-local/workspace'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/09-重建远端工作区.log`

### 10. 迁移 Labsetup

- 状态：ok

- 说明：把标准化后的 Labsetup 复制到远端工作区

- 面向用户的命令表达：`scp -r Labsetup -> /home/seed/seed-labs/lab4-dns-local/workspace/labsetup`

- 实际执行：`scp -i /Users/zzw4257/.ssh/seed-way -P 2345 -o StrictHostKeyChecking=accept-new -r /var/folders/hg/v36fg5jx7_l9jzgv4ywz4pn80000gn/T/tmpbax8_qxu/labsetup seed@localhost:/home/seed/seed-labs/lab4-dns-local/workspace/`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/10-迁移-labsetup.log`

### 11. 上传本地 DNS 攻击脚本 - 建目录

- 状态：ok

- 说明：准备远端目录

- 面向用户的命令表达：`mkdir -p /home/seed/seed-labs/lab4-dns-local/workspace/labsetup/volumes`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'mkdir -p /home/seed/seed-labs/lab4-dns-local/workspace/labsetup/volumes'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/11-上传本地-dns-攻击脚本-建目录.log`

### 12. 上传本地 DNS 攻击脚本

- 状态：ok

- 说明：把自动生成的 Scapy 攻击脚本上传到远端 Labsetup

- 面向用户的命令表达：`scp dns_spoof_lab.py -> /home/seed/seed-labs/lab4-dns-local/workspace/labsetup/volumes/dns_spoof_lab.py`

- 实际执行：`scp -i /Users/zzw4257/.ssh/seed-way -P 2345 -o StrictHostKeyChecking=accept-new /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体/reports/lab4-dns-local/20260403-125920/evidence/generated/dns_spoof_lab.py seed@localhost:/home/seed/seed-labs/lab4-dns-local/workspace/labsetup/volumes/dns_spoof_lab.py`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/12-上传本地-dns-攻击脚本.log`

### 13. 关闭旧环境

- 状态：ok

- 说明：先用非破坏性方式收起旧的 compose 环境

- 面向用户的命令表达：`dcdown`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-local/workspace/labsetup && docker-compose down --remove-orphans || true'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
Stopping local-dns-server-10.9.0.53 ... 
Stopping seed-attacker              ... 
Stopping attacker-ns-10.9.0.153     ... 
Stopping seed-router                ... 
Stopping user-10.9.0.5              ... 
[4A[2K
Stopping seed-attacker              ... [32mdone[0m
[4B[3A[2K
Stopping attacker-ns-10.9.0.153     ... [32mdone[0m
[3B[5A[2K
Stopping local-dns-server-10.9.0.53 ... [32mdone[0m
...
```

- 证据：`evidence/13-关闭旧环境.log`

### 14. 清理残留同名容器

- 状态：ok

- 说明：移除历史运行留下的同名 lab 容器，避免 compose 因命名冲突失败

- 面向用户的命令表达：`docker rm -f <lab-containers>`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'for name in seed-router local-dns-server-10.9.0.53 user-10.9.0.5 seed-attacker attacker-ns-10.9.0.153; do docker rm -f "$name" >/dev/null 2>&1 || true; done'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/14-清理残留同名容器.log`

### 15. 清理残留 lab 网络

- 状态：ok

- 说明：移除当前 profile 的残留网络定义，让 compose 以受控方式重建网络

- 面向用户的命令表达：`docker network rm <lab-networks>`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'for name in net-10.8.0.0 net-10.9.0.0; do docker network rm "$name" >/dev/null 2>&1 || true; done'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/15-清理残留-lab-网络.log`

### 16. 构建镜像

- 状态：ok

- 说明：构建 Labsetup 里的镜像

- 面向用户的命令表达：`dcbuild`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-local/workspace/labsetup && docker-compose build'`

- 关键输出：

```text
Step 1/4 : FROM handsonsecurity/seed-server:bind
 ---> bbf95098dacf
Step 2/4 : COPY named.conf           /etc/bind/
 ---> Using cache
 ---> d31005ca8a6e
Step 3/4 : COPY named.conf.options   /etc/bind/
 ---> Using cache
 ---> 476dd3982c11
Step 4/4 : CMD service named start && tail -f /dev/null
 ---> Using cache
 ---> 96e69d219807
Successfully built 96e69d219807
Successfully tagged seed-local-dns-server:latest
Step 1/5 : FROM handsonsecurity/seed-ubuntu:large
...
```

- 证据：`evidence/16-构建镜像.log`

### 17. 启动环境

- 状态：ok

- 说明：启动 compose 环境并让容器后台运行

- 面向用户的命令表达：`dcup`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-local/workspace/labsetup && docker-compose up -d'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
Creating network "net-10.9.0.0" with the default driver
Creating network "net-10.8.0.0" with the default driver
Creating seed-router ... 
Creating user-10.9.0.5 ... 
Creating local-dns-server-10.9.0.53 ... 
Creating seed-attacker              ... 
Creating attacker-ns-10.9.0.153     ... 
[2A[2K
Creating seed-attacker              ... [32mdone[0m
[2B[5A[2K
Creating seed-router                ... [32mdone[0m
...
```

- 证据：`evidence/17-启动环境.log`

### 18. 检查运行容器

- 状态：ok

- 说明：确认 compose 启动后的容器状态

- 面向用户的命令表达：`dockps`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker ps --format '"'"'table {{.Names}}\t{{.Status}}'"'"''`

- 关键输出：

```text
NAMES                        STATUS
local-dns-server-10.9.0.53   Up 8 seconds
seed-attacker                Up 9 seconds
attacker-ns-10.9.0.153       Up 8 seconds
seed-router                  Up 8 seconds
user-10.9.0.5                Up 8 seconds
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/18-检查运行容器.log`

### 19. 基线检查 ns.attacker32.com

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short ns.attacker32.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short ns.attacker32.com'"'"''`

- 关键输出：

```text
10.9.0.153
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/19-基线检查-ns-attacker32-com.log`

### 20. 基线检查官方 www.example.com

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short www.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short www.example.com'"'"''`

- 关键输出：

```text
104.18.26.120
104.18.27.120
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/20-基线检查官方-www-example-com.log`

### 21. 基线检查攻击者权威结果

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short @ns.attacker32.com www.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short @ns.attacker32.com www.example.com'"'"''`

- 关键输出：

```text
1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/21-基线检查攻击者权威结果.log`

### 22. 定位路由器外网口

- 状态：ok

- 说明：找到 router 容器里连接 10.8.0.0/24 的接口

- 面向用户的命令表达：`相当于 docksh se 后执行: ip -o -4 addr show | awk '$4 ~ /^10\.8\.0\.11\/24/ {print $2; exit}'`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-router bash -lc '"'"'ip -o -4 addr show | awk '"'"'"'"'"'"'"'"'$4 ~ /^10\.8\.0\.11\/24/ {print $2; exit}'"'"'"'"'"'"'"'"''"'"''`

- 关键输出：

```text
eth0
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/22-定位路由器外网口.log`

### 23. 设置路由延迟

- 状态：ok

- 说明：在 router 外网口人为增加 200ms 延迟，降低合法响应抢先到达的概率

- 面向用户的命令表达：`相当于 docksh se 后执行: tc qdisc replace dev eth0 root netem delay 200ms && tc qdisc show dev eth0`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-router bash -lc '"'"'tc qdisc replace dev eth0 root netem delay 200ms && tc qdisc show dev eth0'"'"''`

- 关键输出：

```text
qdisc netem 8002: root refcnt 2 limit 1000 delay 200.0ms
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/23-设置路由延迟.log`

### 24. 定位桥接网卡

- 状态：ok

- 说明：找到 10.9.0.0/24 对应的 host bridge 接口，供嗅探使用

- 面向用户的命令表达：`ip -o -4 addr show | awk '$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'ip -o -4 addr show | awk '"'"'$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'"'"''`

- 关键输出：

```text
br-256929766fcf
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/24-定位桥接网卡.log`

### 25. 清空 DNS 缓存

- 状态：ok

- 说明：在本地 DNS 服务器上清空缓存，避免旧结果干扰攻击

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc flush`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc flush'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/25-清空-dns-缓存.log`

### 26. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/26-停止本地攻击后台脚本.log`

### 27. 后台启动 task1

- 状态：ok

- 说明：在攻击者容器里后台启动对应的 Scapy 攻击脚本，等待嗅探并伪造 DNS 响应

- 面向用户的命令表达：`相当于在 seed-attacker 内后台执行: python3 /volumes/dns_spoof_lab.py --task task1 --iface br-256929766fcf --timeout 25 >/volumes/task1.log 2>&1`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec -d seed-attacker bash -lc '"'"'python3 /volumes/dns_spoof_lab.py --task task1 --iface br-256929766fcf --timeout 25 >/volumes/task1.log 2>&1'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/27-后台启动-task1.log`

### 28. task1 触发 dig (attempt 1)

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short www.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short www.example.com'"'"''`

- 关键输出：

```text
1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/28-task1-触发-dig-attempt-1.log`

### 29. task1 导出缓存 (attempt 1)

- 状态：ok

- 说明：导出本地 DNS 服务器缓存以便留档分析

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db'"'"''`

- 关键输出：

```text
;
; Start view _default
;
;
; Cache dump of view '_default' (cache _default)
;
; using a 604800 second stale ttl
$DATE 20260327050002
; authanswer
.			1123199	IN NS	a.root-servers.net.
			1123199	IN NS	b.root-servers.net.
			1123199	IN NS	c.root-servers.net.
			1123199	IN NS	d.root-servers.net.
			1123199	IN NS	e.root-servers.net.
...
```

- 证据：`evidence/29-task1-导出缓存-attempt-1.log`

### 30. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/30-停止本地攻击后台脚本.log`

### 31. 读取 task1 攻击日志

- 状态：ok

- 说明：读取攻击者容器里自动生成的日志文件

- 面向用户的命令表达：`相当于 docksh se 后执行: cat /volumes/task1.log || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'cat /volumes/task1.log || true'"'"''`

- 关键输出：

```text
[task1] spoofed www.example.com. -> 10.9.0.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/31-读取-task1-攻击日志.log`

### 32. 定位桥接网卡

- 状态：ok

- 说明：找到 10.9.0.0/24 对应的 host bridge 接口，供嗅探使用

- 面向用户的命令表达：`ip -o -4 addr show | awk '$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'ip -o -4 addr show | awk '"'"'$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'"'"''`

- 关键输出：

```text
br-256929766fcf
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/32-定位桥接网卡.log`

### 33. 清空 DNS 缓存

- 状态：ok

- 说明：在本地 DNS 服务器上清空缓存，避免旧结果干扰攻击

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc flush`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc flush'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/33-清空-dns-缓存.log`

### 34. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/34-停止本地攻击后台脚本.log`

### 35. 后台启动 task2

- 状态：ok

- 说明：在攻击者容器里后台启动对应的 Scapy 攻击脚本，等待嗅探并伪造 DNS 响应

- 面向用户的命令表达：`相当于在 seed-attacker 内后台执行: python3 /volumes/dns_spoof_lab.py --task task2 --iface br-256929766fcf --timeout 25 >/volumes/task2.log 2>&1`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec -d seed-attacker bash -lc '"'"'python3 /volumes/dns_spoof_lab.py --task task2 --iface br-256929766fcf --timeout 25 >/volumes/task2.log 2>&1'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/35-后台启动-task2.log`

### 36. task2 触发 dig (attempt 1)

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short www.example.com && dig +short www.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short www.example.com && dig +short www.example.com'"'"''`

- 关键输出：

```text
1.2.3.5
1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/36-task2-触发-dig-attempt-1.log`

### 37. task2 导出缓存 (attempt 1)

- 状态：ok

- 说明：导出本地 DNS 服务器缓存以便留档分析

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db'"'"''`

- 关键输出：

```text
;
; Start view _default
;
;
; Cache dump of view '_default' (cache _default)
;
; using a 604800 second stale ttl
$DATE 20260327050011
; authanswer
.			1123197	IN NS	a.root-servers.net.
			1123197	IN NS	b.root-servers.net.
			1123197	IN NS	c.root-servers.net.
			1123197	IN NS	d.root-servers.net.
			1123197	IN NS	e.root-servers.net.
...
```

- 证据：`evidence/37-task2-导出缓存-attempt-1.log`

### 38. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/38-停止本地攻击后台脚本.log`

### 39. 读取 task2 攻击日志

- 状态：ok

- 说明：读取攻击者容器里自动生成的日志文件

- 面向用户的命令表达：`相当于 docksh se 后执行: cat /volumes/task2.log || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'cat /volumes/task2.log || true'"'"''`

- 关键输出：

```text
[task2] spoofed www.example.com. -> 10.9.0.53
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/39-读取-task2-攻击日志.log`

### 40. task2 缓存筛选 (attempt 1)

- 状态：ok

- 说明：筛出缓存里的关键记录，便于对比任务目标

- 面向用户的命令表达：`相当于 docksh lo 后执行: grep -n 'www.example.com\|1.2.3.5' /var/cache/bind/dump.db || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'grep -n '"'"'"'"'"'"'"'"'www.example.com\|1.2.3.5'"'"'"'"'"'"'"'"' /var/cache/bind/dump.db || true'"'"''`

- 关键输出：

```text
97:www.example.com.	863997	A	1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/40-task2-缓存筛选-attempt-1.log`

### 41. 定位桥接网卡

- 状态：ok

- 说明：找到 10.9.0.0/24 对应的 host bridge 接口，供嗅探使用

- 面向用户的命令表达：`ip -o -4 addr show | awk '$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'ip -o -4 addr show | awk '"'"'$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'"'"''`

- 关键输出：

```text
br-256929766fcf
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/41-定位桥接网卡.log`

### 42. 清空 DNS 缓存

- 状态：ok

- 说明：在本地 DNS 服务器上清空缓存，避免旧结果干扰攻击

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc flush`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc flush'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/42-清空-dns-缓存.log`

### 43. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/43-停止本地攻击后台脚本.log`

### 44. 后台启动 task3

- 状态：ok

- 说明：在攻击者容器里后台启动对应的 Scapy 攻击脚本，等待嗅探并伪造 DNS 响应

- 面向用户的命令表达：`相当于在 seed-attacker 内后台执行: python3 /volumes/dns_spoof_lab.py --task task3 --iface br-256929766fcf --timeout 25 >/volumes/task3.log 2>&1`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec -d seed-attacker bash -lc '"'"'python3 /volumes/dns_spoof_lab.py --task task3 --iface br-256929766fcf --timeout 25 >/volumes/task3.log 2>&1'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/44-后台启动-task3.log`

### 45. task3 触发 dig (attempt 1)

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short www.example.com && dig +short mail.example.com && dig +short @ns.attacker32.com mail.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short www.example.com && dig +short mail.example.com && dig +short @ns.attacker32.com mail.example.com'"'"''`

- 关键输出：

```text
1.2.3.5
1.2.3.6
1.2.3.6
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/45-task3-触发-dig-attempt-1.log`

### 46. task3 导出缓存 (attempt 1)

- 状态：ok

- 说明：导出本地 DNS 服务器缓存以便留档分析

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db'"'"''`

- 关键输出：

```text
;
; Start view _default
;
;
; Cache dump of view '_default' (cache _default)
;
; using a 604800 second stale ttl
$DATE 20260327050020
; authanswer
.			1123197	IN NS	a.root-servers.net.
			1123197	IN NS	b.root-servers.net.
			1123197	IN NS	c.root-servers.net.
			1123197	IN NS	d.root-servers.net.
			1123197	IN NS	e.root-servers.net.
...
```

- 证据：`evidence/46-task3-导出缓存-attempt-1.log`

### 47. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/47-停止本地攻击后台脚本.log`

### 48. 读取 task3 攻击日志

- 状态：ok

- 说明：读取攻击者容器里自动生成的日志文件

- 面向用户的命令表达：`相当于 docksh se 后执行: cat /volumes/task3.log || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'cat /volumes/task3.log || true'"'"''`

- 关键输出：

```text
[task3] spoofed www.example.com. -> 10.9.0.53
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/48-读取-task3-攻击日志.log`

### 49. task3 缓存筛选 (attempt 1)

- 状态：ok

- 说明：筛出缓存里的关键记录，便于对比任务目标

- 面向用户的命令表达：`相当于 docksh lo 后执行: grep -n 'example.com\|attacker32.com' /var/cache/bind/dump.db || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'grep -n '"'"'"'"'"'"'"'"'example.com\|attacker32.com'"'"'"'"'"'"'"'"' /var/cache/bind/dump.db || true'"'"''`

- 关键输出：

```text
68:ns.attacker32.com.	615597	\-AAAA	;-$NXRRSET
69:; attacker32.com. SOA ns.attacker32.com. admin.attacker32.com. 2008111001 28800 7200 2419200 86400
89:example.com.		777597	NS	ns.attacker32.com.
101:mail.example.com.	863997	A	1.2.3.6
103:www.example.com.	863997	A	1.2.3.5
267:; ns.attacker32.com [v4 TTL 1797] [v6 TTL 10797] [v4 success] [v6 nxrrset]
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/49-task3-缓存筛选-attempt-1.log`

### 50. 定位桥接网卡

- 状态：ok

- 说明：找到 10.9.0.0/24 对应的 host bridge 接口，供嗅探使用

- 面向用户的命令表达：`ip -o -4 addr show | awk '$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'ip -o -4 addr show | awk '"'"'$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'"'"''`

- 关键输出：

```text
br-256929766fcf
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/50-定位桥接网卡.log`

### 51. 清空 DNS 缓存

- 状态：ok

- 说明：在本地 DNS 服务器上清空缓存，避免旧结果干扰攻击

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc flush`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc flush'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/51-清空-dns-缓存.log`

### 52. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/52-停止本地攻击后台脚本.log`

### 53. 后台启动 task4

- 状态：ok

- 说明：在攻击者容器里后台启动对应的 Scapy 攻击脚本，等待嗅探并伪造 DNS 响应

- 面向用户的命令表达：`相当于在 seed-attacker 内后台执行: python3 /volumes/dns_spoof_lab.py --task task4 --iface br-256929766fcf --timeout 25 >/volumes/task4.log 2>&1`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec -d seed-attacker bash -lc '"'"'python3 /volumes/dns_spoof_lab.py --task task4 --iface br-256929766fcf --timeout 25 >/volumes/task4.log 2>&1'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/53-后台启动-task4.log`

### 54. task4 触发 dig (attempt 1)

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short www.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short www.example.com'"'"''`

- 关键输出：

```text
1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/54-task4-触发-dig-attempt-1.log`

### 55. task4 导出缓存 (attempt 1)

- 状态：ok

- 说明：导出本地 DNS 服务器缓存以便留档分析

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db'"'"''`

- 关键输出：

```text
;
; Start view _default
;
;
; Cache dump of view '_default' (cache _default)
;
; using a 604800 second stale ttl
$DATE 20260327050032
; authanswer
.			1123195	IN NS	a.root-servers.net.
			1123195	IN NS	b.root-servers.net.
			1123195	IN NS	c.root-servers.net.
			1123195	IN NS	d.root-servers.net.
			1123195	IN NS	e.root-servers.net.
...
```

- 证据：`evidence/55-task4-导出缓存-attempt-1.log`

### 56. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/56-停止本地攻击后台脚本.log`

### 57. 读取 task4 攻击日志

- 状态：ok

- 说明：读取攻击者容器里自动生成的日志文件

- 面向用户的命令表达：`相当于 docksh se 后执行: cat /volumes/task4.log || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'cat /volumes/task4.log || true'"'"''`

- 关键输出：

```text
[task4] spoofed www.example.com. -> 10.9.0.53
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/57-读取-task4-攻击日志.log`

### 58. task4 缓存筛选 (attempt 1)

- 状态：ok

- 说明：筛出缓存里的关键记录，便于对比任务目标

- 面向用户的命令表达：`相当于 docksh lo 后执行: grep -n 'google.com\|example.com\|attacker32.com' /var/cache/bind/dump.db || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'grep -n '"'"'"'"'"'"'"'"'google.com\|example.com\|attacker32.com'"'"'"'"'"'"'"'"' /var/cache/bind/dump.db || true'"'"''`

- 关键输出：

```text
84:example.com.		777597	NS	ns.attacker32.com.
96:www.example.com.	863997	A	1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/58-task4-缓存筛选-attempt-1.log`

### 59. 定位桥接网卡

- 状态：ok

- 说明：找到 10.9.0.0/24 对应的 host bridge 接口，供嗅探使用

- 面向用户的命令表达：`ip -o -4 addr show | awk '$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'ip -o -4 addr show | awk '"'"'$4 ~ /^10\.9\.0\.1\/24/ {print $2; exit}'"'"''`

- 关键输出：

```text
br-256929766fcf
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/59-定位桥接网卡.log`

### 60. 清空 DNS 缓存

- 状态：ok

- 说明：在本地 DNS 服务器上清空缓存，避免旧结果干扰攻击

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc flush`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc flush'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/60-清空-dns-缓存.log`

### 61. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/61-停止本地攻击后台脚本.log`

### 62. 后台启动 task5

- 状态：ok

- 说明：在攻击者容器里后台启动对应的 Scapy 攻击脚本，等待嗅探并伪造 DNS 响应

- 面向用户的命令表达：`相当于在 seed-attacker 内后台执行: python3 /volumes/dns_spoof_lab.py --task task5 --iface br-256929766fcf --timeout 25 >/volumes/task5.log 2>&1`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec -d seed-attacker bash -lc '"'"'python3 /volumes/dns_spoof_lab.py --task task5 --iface br-256929766fcf --timeout 25 >/volumes/task5.log 2>&1'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/62-后台启动-task5.log`

### 63. task5 触发 dig (attempt 1)

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short www.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short www.example.com'"'"''`

- 关键输出：

```text
1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/63-task5-触发-dig-attempt-1.log`

### 64. task5 导出缓存 (attempt 1)

- 状态：ok

- 说明：导出本地 DNS 服务器缓存以便留档分析

- 面向用户的命令表达：`相当于 docksh lo 后执行: rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db'"'"''`

- 关键输出：

```text
;
; Start view _default
;
;
; Cache dump of view '_default' (cache _default)
;
; using a 604800 second stale ttl
$DATE 20260327050041
; authanswer
.			1123198	IN NS	a.root-servers.net.
			1123198	IN NS	b.root-servers.net.
			1123198	IN NS	c.root-servers.net.
			1123198	IN NS	d.root-servers.net.
			1123198	IN NS	e.root-servers.net.
...
```

- 证据：`evidence/64-task5-导出缓存-attempt-1.log`

### 65. 停止本地攻击后台脚本

- 状态：failed

- 说明：确保攻击者容器里没有残留的后台嗅探进程

- 面向用户的命令表达：`相当于 docksh se 后执行: pkill -f dns_spoof_lab.py || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'pkill -f dns_spoof_lab.py || true'"'"''`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/65-停止本地攻击后台脚本.log`

### 66. 读取 task5 攻击日志

- 状态：ok

- 说明：读取攻击者容器里自动生成的日志文件

- 面向用户的命令表达：`相当于 docksh se 后执行: cat /volumes/task5.log || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'cat /volumes/task5.log || true'"'"''`

- 关键输出：

```text
[task5] spoofed www.example.com. -> 10.9.0.53
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/66-读取-task5-攻击日志.log`

### 67. task5 缓存筛选 (attempt 1)

- 状态：ok

- 说明：筛出缓存里的关键记录，便于对比任务目标

- 面向用户的命令表达：`相当于 docksh lo 后执行: grep -n 'attacker32.com\|example.net\|facebook.com\|1.2.3.4\|5.6.7.8\|3.4.5.6' /var/cache/bind/dump.db || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'grep -n '"'"'"'"'"'"'"'"'attacker32.com\|example.net\|facebook.com\|1.2.3.4\|5.6.7.8\|3.4.5.6'"'"'"'"'"'"'"'"' /var/cache/bind/dump.db || true'"'"''`

- 关键输出：

```text
85:			777598	NS	ns.attacker32.com.
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/67-task5-缓存筛选-attempt-1.log`

### 68. 收尾关闭环境

- 状态：ok

- 说明：在证据收集完成后关闭 compose 环境，避免脏状态残留

- 面向用户的命令表达：`dcdown`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-local/workspace/labsetup && docker-compose down --remove-orphans'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
Stopping local-dns-server-10.9.0.53 ... 
Stopping seed-attacker              ... 
Stopping attacker-ns-10.9.0.153     ... 
Stopping seed-router                ... 
Stopping user-10.9.0.5              ... 
[4A[2K
Stopping seed-attacker              ... [32mdone[0m
[4B[3A[2K
Stopping attacker-ns-10.9.0.153     ... [32mdone[0m
[3B[1A[2K
Stopping user-10.9.0.5              ... [32mdone[0m
...
```

- 证据：`evidence/68-收尾关闭环境.log`

## 结果与证据

### DNS 配置基线

ns.attacker32.com -> 10.9.0.153
www.example.com -> 104.18.26.120
104.18.27.120
@ns.attacker32.com www.example.com -> 1.2.3.5

### 任务 1：直接向用户伪造响应

第 1 次尝试成功。
用户侧 dig 结果:
1.2.3.5

攻击日志:
[task1] spoofed www.example.com. -> 10.9.0.5


### 任务 2：DNS 缓存投毒

                第 1 次尝试成功。
                两次 dig 输出:
                1.2.3.5
1.2.3.5

                缓存筛选:
                97:www.example.com.	863997	A	1.2.3.5


### 任务 3：伪造 NS 记录

                第 1 次尝试成功。
                dig 结果:
                1.2.3.5
1.2.3.6
1.2.3.6

                缓存筛选:
                68:ns.attacker32.com.	615597	\-AAAA	;-$NXRRSET
69:; attacker32.com. SOA ns.attacker32.com. admin.attacker32.com. 2008111001 28800 7200 2419200 86400
89:example.com.		777597	NS	ns.attacker32.com.
101:mail.example.com.	863997	A	1.2.3.6
103:www.example.com.	863997	A	1.2.3.5
267:; ns.attacker32.com [v4 TTL 1797] [v6 TTL 10797] [v4 success] [v6 nxrrset]


### 任务 4：伪造另一个域的 NS 记录

                第 1 次尝试完成。
                关键缓存记录:
                84:example.com.		777597	NS	ns.attacker32.com.
96:www.example.com.	863997	A	1.2.3.5

                观察: 缓存里保留了与当前查询域相关的记录，而与查询无关的 google.com 记录通常不会被接受。


### 任务 5：附加部分记录缓存

第 1 次尝试完成。
关键缓存记录:
85:			777598	NS	ns.attacker32.com.

观察: 与权威记录直接相关的 glue 记录更容易留下，而无关的额外条目不会稳定缓存。


## 实验成果留档

- `evidence/generated/dns_spoof_lab.py`

## 问题陈述

无

## 思考题与解释

- 本次报告将关键解释并入“结果与证据”章节，避免重复叙述。

## 附加 Quiz

1. 为什么任务 1 的伪造结果不会像缓存投毒那样长期生效？
2. 为什么任务 4 里试图顺带投毒 google.com 往往不会成功进入缓存？
3. 附加部分里的记录为什么有些会被缓存，有些不会？
