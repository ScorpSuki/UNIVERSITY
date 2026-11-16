import random, sys
from datetime import datetime, timedelta

# ---- нұсқа параметрлері (кестеден алыңыз) ----
NN = "07"                    # нұсқа нөмірі (екі таңба)
ATTACKER = "203.0.113.17"    # шабуылдаушы IP
TARGET = "bob"             # нысана пайдаланушы
THRESHOLD = 3                # күдікті деп санайтын сәтсіз әрекет шегі
FAILS = 7                    # шабуылдаушының сәтсіз әрекеттер саны

USERS = ["alice", "bob", "carol", "dave", "erik"]
SCANNER = "198.51.100.77"


def generate_log(path):
    rnd = random.Random(int(NN))
    start = datetime(2026, 11, 12, 9, 0, 0)
    events = []

    def add(sec, event_id, user, ip):
        t = (start + timedelta(seconds=sec)).strftime("%Y-%m-%d %H:%M:%S")
        events.append((sec, f"{t} EventID={event_id} Account={user} "
                            f"SourceIP={ip} LogonType=3"))

    for i, u in enumerate(USERS):
        for _ in range(2):
            add(rnd.randint(0, 3600), 4624, u, f"192.168.1.{10 + i}")
    add(rnd.randint(0, 3600), 4625, "bob", "192.168.1.11")
    for _ in range(THRESHOLD - 1):
        add(rnd.randint(0, 3600), 4625, "Administrator", SCANNER)
    sec = 1800
    for _ in range(FAILS):
        sec += rnd.randint(2, 6)
        add(sec, 4625, TARGET, ATTACKER)
    add(sec + 5, 4624, TARGET, ATTACKER)
    events.sort()
    with open(path, "w", encoding="utf-8") as f:
        for _, line in events:
            f.write(line + "\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    generate_log("security_log.txt")
    print("security_log.txt жасалды")
