import re, sys
from collections import Counter

THRESHOLD = 3

PATTERN = re.compile(r"EventID=(\d+) Account=(\S+) SourceIP=(\S+)")


def parse_line(line):
    m = PATTERN.search(line)
    if not m:
        return None
    event_id, user, ip = m.group(1), m.group(2), m.group(3)
    if event_id == "4625":
        return ("failed", user, ip)
    elif event_id == "4624":
        return ("accepted", user, ip)
    return None


def count_failed(lines):
    counts = Counter()
    for line in lines:
        parsed = parse_line(line)
        if parsed and parsed[0] == "failed":
            counts[parsed[2]] += 1
    return counts


def suspicious_ips(counts, threshold):
    return sorted(ip for ip, c in counts.items() if c >= threshold)


def compromised(lines, ips):
    result = set()
    bad = set(ips)
    for line in lines:
        parsed = parse_line(line)
        if parsed and parsed[0] == "accepted" and parsed[2] in bad:
            result.add((parsed[1], parsed[2]))
    return sorted(result)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    with open("security_log.txt", encoding="utf-8") as f:
        lines = f.read().splitlines()
    print("Жол саны:", len(lines))
    counts = count_failed(lines)
    print("1. Сәтсіз әрекеттер (IP бойынша):", dict(counts))
    bad = suspicious_ips(counts, THRESHOLD)
    print("2. Күдікті IP:", bad)
    print("3. Бұзылған тіркелгі (пайдаланушы, IP):", compromised(lines, bad))