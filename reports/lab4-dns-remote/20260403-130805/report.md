# lab4-dns-remote 实验报告

## 实验总结

- Profile: `lab4-dns-remote`
- Run ID: `20260403-130805`
- 目标 VM: `seed@localhost` over port `2345`
- 当前状态: `completed`
- 说明: 自动完成材料审查、前置环境验证、实验执行、证据采集与留档。

## 材料审查表

| 项目 | 路径 | 状态 | 说明 |
| --- | --- | --- | --- |
| 远程实验指导文档 | lab4-dns/DNS 攻击实验 - 远程攻击.md | 已找到 | 必需 |
| Labsetup 目录 | lab4-dns/Labsetup_DNS_Remote | 已找到 | 必需 |
| Compose 文件 | lab4-dns/Labsetup_DNS_Remote/docker-compose.yml | 已找到 | 必需 |
| Kaminsky C 骨架 | lab4-dns/Labsetup_DNS_Remote/Files/attack.c | 已找到 | 必需 |

## 前置环境表

| 检查项 | 结果 | 详情 |
| --- | --- | --- |
| SSH 连通性 | 通过 | seed@localhost:2345 |
| 操作系统 | 通过 | "Ubuntu 20.04.6 LTS" |
| sudo 密码 | 通过 | 使用测试密码 dees |
| Docker Compose | 通过 | /usr/local/bin/docker-compose |
| SEED 别名 | 通过 | dcbuild is aliased to `docker-compose build'<br>dcup is aliased to `docker-compose up'<br>dcdown is aliased to `docker-compose down'<br>dockps is aliased to `docker ps --format "{{.ID}}  {{.Names}}" | sort -k 2'<br>docksh is a function<br>docksh () <br>{ <br>    docker exec -it $1 /bin/bash<br>} |
| Python 运行时 | 通过 | /usr/bin/python3<br>Python 3.8.10 |
| Docker 环境洁净度 | 注意 | 运行容器数=4; 残留网络=seed-net |

## 逐任务执行记录

### 1. 读取容器数量

- 状态：ok

- 说明：检查远端当前运行中的容器数量

- 面向用户的命令表达：`dockps`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker ps -q | wc -l | tr -d '"'"' '"'"''`

- 关键输出：

```text
4
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
seed-net
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

- 面向用户的命令表达：`mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'rm -rf /home/seed/seed-labs/lab4-dns-remote/workspace && mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace'`

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

- 面向用户的命令表达：`scp -r Labsetup -> /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup`

- 实际执行：`scp -i /Users/zzw4257/.ssh/seed-way -P 2345 -o StrictHostKeyChecking=accept-new -r /var/folders/hg/v36fg5jx7_l9jzgv4ywz4pn80000gn/T/tmp7zdxlxg3/labsetup seed@localhost:/home/seed/seed-labs/lab4-dns-remote/workspace/`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/10-迁移-labsetup.log`

### 11. 关闭旧环境

- 状态：ok

- 说明：先用非破坏性方式收起旧的 compose 环境

- 面向用户的命令表达：`dcdown`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup && docker-compose down --remove-orphans || true'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
Stopping local-dns-server-10.9.0.53 ... 
Stopping seed-attacker              ... 
Stopping attacker-ns-10.9.0.153     ... 
Stopping user-10.9.0.5              ... 
[3A[2K
Stopping seed-attacker              ... [32mdone[0m
[3B[4A[2K
Stopping local-dns-server-10.9.0.53 ... [32mdone[0m
[4B[1A[2K
Stopping user-10.9.0.5              ... [32mdone[0m
[1B[2A[2K
...
```

- 证据：`evidence/11-关闭旧环境.log`

### 12. 清理残留同名容器

- 状态：ok

- 说明：移除历史运行留下的同名 lab 容器，避免 compose 因命名冲突失败

- 面向用户的命令表达：`docker rm -f <lab-containers>`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'for name in local-dns-server-10.9.0.53 user-10.9.0.5 seed-attacker attacker-ns-10.9.0.153; do docker rm -f "$name" >/dev/null 2>&1 || true; done'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/12-清理残留同名容器.log`

### 13. 清理残留 lab 网络

- 状态：ok

- 说明：移除当前 profile 的残留网络定义，让 compose 以受控方式重建网络

- 面向用户的命令表达：`docker network rm <lab-networks>`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'for name in seed-net; do docker network rm "$name" >/dev/null 2>&1 || true; done'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/13-清理残留-lab-网络.log`

### 14. 构建镜像

- 状态：ok

- 说明：构建 Labsetup 里的镜像

- 面向用户的命令表达：`dcbuild`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup && docker-compose build'`

- 关键输出：

```text
Step 1/4 : FROM handsonsecurity/seed-server:bind
 ---> bbf95098dacf
Step 2/4 : COPY named.conf           /etc/bind/
 ---> Using cache
 ---> b0cabfa86df9
Step 3/4 : COPY named.conf.options   /etc/bind/
 ---> Using cache
 ---> 71641d200455
Step 4/4 : CMD service named start && tail -f /dev/null
 ---> Using cache
 ---> 24569a484b73
Successfully built 24569a484b73
Successfully tagged seed-local-dns-server:latest
Step 1/5 : FROM handsonsecurity/seed-ubuntu:large
...
```

- 证据：`evidence/14-构建镜像.log`

### 15. 启动环境

- 状态：ok

- 说明：启动 compose 环境并让容器后台运行

- 面向用户的命令表达：`dcup`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup && docker-compose up -d'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
Creating network "seed-net" with the default driver
Creating user-10.9.0.5 ... 
Creating seed-attacker ... 
Creating local-dns-server-10.9.0.53 ... 
Creating attacker-ns-10.9.0.153     ... 
[3A[2K
Creating seed-attacker              ... [32mdone[0m
[3B[4A[2K
Creating user-10.9.0.5              ... [32mdone[0m
[4B[2A[2K
Creating local-dns-server-10.9.0.53 ... [32mdone[0m
...
```

- 证据：`evidence/15-启动环境.log`

### 16. 检查运行容器

- 状态：ok

- 说明：确认 compose 启动后的容器状态

- 面向用户的命令表达：`dockps`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker ps --format '"'"'table {{.Names}}\t{{.Status}}'"'"''`

- 关键输出：

```text
NAMES                        STATUS
attacker-ns-10.9.0.153       Up 8 seconds
seed-attacker                Up 8 seconds
local-dns-server-10.9.0.53   Up 8 seconds
user-10.9.0.5                Up 8 seconds
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/16-检查运行容器.log`

### 17. 基线检查 ns.attacker32.com

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

- 证据：`evidence/17-基线检查-ns-attacker32-com.log`

### 18. 基线检查官方 www.example.com

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

- 证据：`evidence/18-基线检查官方-www-example-com.log`

### 19. 基线检查攻击者权威结果

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

- 证据：`evidence/19-基线检查攻击者权威结果.log`

### 20. 查询合法权威 NS IP

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: for ns in $(dig +short NS example.com); do dig +short $ns; done | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | sort -u`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'for ns in $(dig +short NS example.com); do dig +short $ns; done | grep -E '"'"'"'"'"'"'"'"'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'"'"'"'"'"'"'"'"' | sort -u'"'"''`

- 关键输出：

```text
108.162.192.162
108.162.195.228
162.159.44.228
172.64.32.162
172.64.35.228
173.245.58.162
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/20-查询合法权威-ns-ip.log`

### 21. 上传 prepare_packets.py - 建目录

- 状态：ok

- 说明：准备远端目录

- 面向用户的命令表达：`mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/21-上传-prepare-packets-py-建目录.log`

### 22. 上传 prepare_packets.py

- 状态：ok

- 说明：把 Kaminsky 模板生成脚本上传到远端 Files

- 面向用户的命令表达：`scp prepare_packets.py -> /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files/prepare_packets.py`

- 实际执行：`scp -i /Users/zzw4257/.ssh/seed-way -P 2345 -o StrictHostKeyChecking=accept-new /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体/reports/lab4-dns-remote/20260403-130805/evidence/generated/prepare_packets.py seed@localhost:/home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files/prepare_packets.py`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/22-上传-prepare-packets-py.log`

### 23. 同步模板脚本到 volumes - 建目录

- 状态：ok

- 说明：准备远端目录

- 面向用户的命令表达：`mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/23-同步模板脚本到-volumes-建目录.log`

### 24. 同步模板脚本到 volumes

- 状态：ok

- 说明：让攻击者容器可直接访问模板生成脚本

- 面向用户的命令表达：`scp prepare_packets.py -> /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes/prepare_packets.py`

- 实际执行：`scp -i /Users/zzw4257/.ssh/seed-way -P 2345 -o StrictHostKeyChecking=accept-new /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体/reports/lab4-dns-remote/20260403-130805/evidence/generated/prepare_packets.py seed@localhost:/home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes/prepare_packets.py`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/24-同步模板脚本到-volumes.log`

### 25. 上传 attack.c - 建目录

- 状态：ok

- 说明：准备远端目录

- 面向用户的命令表达：`mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/25-上传-attack-c-建目录.log`

### 26. 上传 attack.c

- 状态：ok

- 说明：把补全后的 attack.c 上传到远端 Files

- 面向用户的命令表达：`scp attack.c -> /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files/attack.c`

- 实际执行：`scp -i /Users/zzw4257/.ssh/seed-way -P 2345 -o StrictHostKeyChecking=accept-new /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体/reports/lab4-dns-remote/20260403-130805/evidence/generated/attack.c seed@localhost:/home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/Files/attack.c`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/26-上传-attack-c.log`

### 27. 同步 attack.c 到 volumes - 建目录

- 状态：ok

- 说明：准备远端目录

- 面向用户的命令表达：`mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'mkdir -p /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/27-同步-attack-c-到-volumes-建目录.log`

### 28. 同步 attack.c 到 volumes

- 状态：ok

- 说明：让攻击者容器可直接编译 attack.c

- 面向用户的命令表达：`scp attack.c -> /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes/attack.c`

- 实际执行：`scp -i /Users/zzw4257/.ssh/seed-way -P 2345 -o StrictHostKeyChecking=accept-new /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体/reports/lab4-dns-remote/20260403-130805/evidence/generated/attack.c seed@localhost:/home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes/attack.c`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/28-同步-attack-c-到-volumes.log`

### 29. 清空 DNS 缓存

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

- 证据：`evidence/29-清空-dns-缓存.log`

### 30. 生成 Kaminsky 数据包模板

- 状态：ok

- 说明：在攻击者容器里用 Scapy 生成请求与响应模板

- 面向用户的命令表达：`相当于 docksh se 后执行: cd /volumes && python3 prepare_packets.py`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec seed-attacker bash -lc '"'"'cd /volumes && python3 prepare_packets.py'"'"''`

- 关键输出：

```text
Prepared ip_req.bin and ip_resp.bin with legitimate NS 108.162.192.162
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/30-生成-kaminsky-数据包模板.log`

### 31. 编译 attack.c

- 状态：ok

- 说明：在宿主机的挂载目录里编译补全后的 attack.c，避免依赖容器内缺失的 gcc

- 面向用户的命令表达：`gcc -O2 -o attack attack.c`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes && gcc -O2 -o attack attack.c'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/31-编译-attack-c.log`

### 32. 清空 DNS 缓存

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

- 证据：`evidence/32-清空-dns-缓存.log`

### 33. 运行 Kaminsky 攻击 attempt 1

- 状态：ok

- 说明：在宿主机上以 sudo 运行编译后的攻击程序，利用随机子域名反复触发并投毒

- 面向用户的命令表达：`echo dees | sudo -S timeout 30s ./attack`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes && echo dees | sudo -S timeout 30s ./attack > attack-run.log 2>&1 || true'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/33-运行-kaminsky-攻击-attempt-1.log`

### 34. 远程攻击缓存导出 attempt 1

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
$DATE 20260327050916
; authanswer
.			1123170	IN NS	a.root-servers.net.
			1123170	IN NS	b.root-servers.net.
			1123170	IN NS	c.root-servers.net.
			1123170	IN NS	d.root-servers.net.
			1123170	IN NS	e.root-servers.net.
...
```

- 证据：`evidence/34-远程攻击缓存导出-attempt-1.log`

### 35. 远程攻击缓存筛选 attempt 1

- 状态：ok

- 说明：筛选缓存中的关键 NS 记录

- 面向用户的命令表达：`相当于 docksh lo 后执行: grep -n 'attacker32.com\|example.com' /var/cache/bind/dump.db || true`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec local-dns-server-10.9.0.53 bash -lc '"'"'grep -n '"'"'"'"'"'"'"'"'attacker32.com\|example.com'"'"'"'"'"'"'"'"' /var/cache/bind/dump.db || true'"'"''`

- 关键输出：

```text
84:example.com.		777570	NS	ns.attacker32.com.
96:nprqb.example.com.	863991	A	1.2.3.4
98:qghon.example.com.	606581	\-A	;-$NXRRSET
99:; qghon.example.com. RRSIG NSEC ...
100:; qghon.example.com. NSEC \000.qghon.example.com. RRSIG NSEC TYPE128
101:; example.com. SOA elliott.ns.cloudflare.com. dns.cloudflare.com. 2400651045 10000 2400 604800 1800
102:; example.com. RRSIG SOA ...
104:wsugp.example.com.	606572	\-A	;-$NXRRSET
105:; wsugp.example.com. RRSIG NSEC ...
106:; wsugp.example.com. NSEC \000.wsugp.example.com. RRSIG NSEC TYPE128
107:; example.com. SOA elliott.ns.cloudflare.com. dns.cloudflare.com. 2400651045 10000 2400 604800 1800
108:; example.com. RRSIG SOA ...
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
...
```

- 证据：`evidence/35-远程攻击缓存筛选-attempt-1.log`

### 36. 读取 Kaminsky 攻击日志 attempt 1

- 状态：ok

- 说明：从宿主机挂载目录读取攻击程序日志

- 面向用户的命令表达：`tail -n 40 attack-run.log`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup/volumes && tail -n 40 attack-run.log || true'`

- 关键输出：

```text
triggering wsugp.example.com
triggering qghon.example.com
triggering nprqb.example.com
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/36-读取-kaminsky-攻击日志-attempt-1.log`

### 37. 验证远程攻击结果

- 状态：ok

- 说明：从用户容器执行 dig 验证命令

- 面向用户的命令表达：`相当于 docksh us 后执行: dig +short www.example.com && dig +short @ns.attacker32.com www.example.com`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'docker exec user-10.9.0.5 bash -lc '"'"'dig +short www.example.com && dig +short @ns.attacker32.com www.example.com'"'"''`

- 关键输出：

```text
1.2.3.5
1.2.3.5
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
```

- 证据：`evidence/37-验证远程攻击结果.log`

### 38. 收尾关闭环境

- 状态：ok

- 说明：在证据收集完成后关闭 compose 环境，避免脏状态残留

- 面向用户的命令表达：`dcdown`

- 实际执行：`ssh -i /Users/zzw4257/.ssh/seed-way -p 2345 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 seed@localhost bash -lc 'cd /home/seed/seed-labs/lab4-dns-remote/workspace/labsetup && docker-compose down --remove-orphans'`

- 关键输出：

```text
** WARNING: connection is not using a post-quantum key exchange algorithm.
** This session may be vulnerable to "store now, decrypt later" attacks.
** The server may need to be upgraded. See https://openssh.com/pq.html
Stopping attacker-ns-10.9.0.153     ... 
Stopping seed-attacker              ... 
Stopping local-dns-server-10.9.0.53 ... 
Stopping user-10.9.0.5              ... 
[3A[2K
Stopping seed-attacker              ... [32mdone[0m
[3B[4A[2K
Stopping attacker-ns-10.9.0.153     ... [32mdone[0m
[4B[1A[2K
Stopping user-10.9.0.5              ... [32mdone[0m
[1B[2A[2K
...
```

- 证据：`evidence/38-收尾关闭环境.log`

## 结果与证据

### DNS 配置基线

ns.attacker32.com -> 10.9.0.153
www.example.com -> 104.18.26.120
104.18.27.120
@ns.attacker32.com www.example.com -> 1.2.3.5

### 远程 Kaminsky 攻击结果

                第 1 次尝试成功。
                缓存筛选:
                84:example.com.		777570	NS	ns.attacker32.com.
96:nprqb.example.com.	863991	A	1.2.3.4
98:qghon.example.com.	606581	\-A	;-$NXRRSET
99:; qghon.example.com. RRSIG NSEC ...
100:; qghon.example.com. NSEC \000.qghon.example.com. RRSIG NSEC TYPE128
101:; example.com. SOA elliott.ns.cloudflare.com. dns.cloudflare.com. 2400651045 10000 2400 604800 1800
102:; example.com. RRSIG SOA ...
104:wsugp.example.com.	606572	\-A	;-$NXRRSET
105:; wsugp.example.com. RRSIG NSEC ...
106:; wsugp.example.com. NSEC \000.wsugp.example.com. RRSIG NSEC TYPE128
107:; example.com. SOA elliott.ns.cloudflare.com. dns.cloudflare.com. 2400651045 10000 2400 604800 1800
108:; example.com. RRSIG SOA ...

                用户侧 dig 对比:
                1.2.3.5
1.2.3.5


## 实验成果留档

- `evidence/generated/prepare_packets.py`
- `evidence/generated/attack.c`

## 问题陈述

无

## 思考题与解释

- 本次报告将关键解释并入“结果与证据”章节，避免重复叙述。

## 附加 Quiz

1. Kaminsky 攻击为什么要不断更换随机子域名？
2. 为什么远程缓存投毒要同时考虑速度和 Transaction ID？
3. 混合使用 Scapy 与 C 相比纯 Python 的核心收益是什么？
