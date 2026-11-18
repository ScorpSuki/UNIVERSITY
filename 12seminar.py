
import hashlib
import numpy as np

# ==========================================
# BUCKET КЛАСЫ (ФАЙЛДАҒЫ БЕРІЛГЕН КОД)
# ==========================================

class Bucket:
    PRICE = {
        "standard": 0.023,
        "cool": 0.0125,
        "archive": 0.004
    }

    def __init__(self, name, versioning=False):
        self.name = name
        self.versioning = versioning
        self.objects = {}

    def put(self, key, data, age_days=0):
        v = {
            "data": data,
            "class": "standard",
            "age": age_days,
            "acl": "private",
            "md5": hashlib.md5(data).hexdigest()
        }

        if self.versioning:
            self.objects.setdefault(key, []).append(v)
        else:
            self.objects[key] = [v]

    def get(self, key, version=-1):
        return self.objects[key][version]["data"]

    def list(self, prefix=""):
        return sorted(
            k for k in self.objects if k.startswith(prefix)
        )

    def set_class(self, key, cls):
        self.objects[key][-1]["class"] = cls

    def set_acl(self, key, acl):
        self.objects[key][-1]["acl"] = acl

    def can_read(self, role, key):
        return (
            role == "owner"
            or self.objects[key][-1]["acl"] == "public"
        )

    def delete(self, key):
        del self.objects[key]

    def monthly_cost(self):
        return sum(
            len(v["data"]) / 1e9 * self.PRICE[v["class"]]
            for o in self.objects.values()
            for v in o
        )


# ==========================================
# 7-НҰСҚАНЫҢ ПАРАМЕТРЛЕРІ
# ==========================================

ds, ext, N, size_mb = "server-logs", ".log", 40, 1

cool_days = 30
archive_days = 90

rng = np.random.default_rng(1)

b = Bucket("project-data", versioning=True)

print("7-НҰСҚА")
print("Деректер атауы:", ds)
print("Файл саны:", N)
print("Бір файл көлемі:", size_mb, "МБ")


# ==========================================
# 1-ТАПСЫРМА. ДЕРЕКТЕРДІ ЖҮКТЕУ
# ==========================================

print("\n1. ДЕРЕКТЕРДІ ЖҮКТЕУ")

for i in range(N):
    key = f"{ds}/2025/{i % 12 + 1:02d}/file_{i}{ext}"

    b.put(
        key,
        rng.bytes(size_mb * 1_000_000),
        age_days=int(rng.integers(0, 365))
    )

keys = b.list()

ages = [
    b.objects[k][-1]["age"]
    for k in keys
]

total_size = sum(
    len(b.get(k)) for k in keys
) / 1_000_000

print("Объект саны:", len(keys))
print("Жалпы көлемі:", total_size, "МБ")
print("Ең ескі объект:", max(ages), "күн")
print("Ең жаңа объект:", min(ages), "күн")


# ==========================================
# 2-ТАПСЫРМА. САҚТАУ КЛАСЫ ЖӘНЕ ШЫҒЫН
# ==========================================

print("\n2. САҚТАУ КЛАСЫ ЖӘНЕ ШЫҒЫН")

old_cost = b.monthly_cost()

print("Бастапқы айлық шығын:",
      round(old_cost, 6), "$")

for k in keys:
    age = b.objects[k][-1]["age"]

    if age >= archive_days:
        b.set_class(k, "archive")

    elif age >= cool_days:
        b.set_class(k, "cool")

new_cost = b.monthly_cost()

saving = (old_cost - new_cost) / old_cost * 100

print("Standard файлдар саны:", sum(
    b.objects[k][-1]["class"] == "standard" for k in keys
))

print("Cool файлдар саны:", sum(
    b.objects[k][-1]["class"] == "cool" for k in keys
))

print("Archive файлдар саны:", sum(
    b.objects[k][-1]["class"] == "archive" for k in keys
))

print("Жаңа айлық шығын:", round(new_cost, 6), "$")
print("Үнемдеу пайызы:", round(saving, 2), "%")

print("1000 есе дерек үшін бастапқы шығын:",
      round(old_cost * 1000, 3), "$")

print("1000 есе дерек үшін жаңа шығын:",
      round(new_cost * 1000, 3), "$")


# ==========================================
# 3-ТАПСЫРМА. ДЕРЕКТЕРДІ БАСҚАРУ
# ==========================================

print("\n3. ДЕРЕКТЕРДІ БАСҚАРУ")

# а) Наурыз айындағы файлдарды тізімдеу

march_files = b.list(f"{ds}/2025/03/")

print("\nНаурыз айындағы файлдар:")
for f in march_files:
    print(f)

print("Наурыз айындағы объект саны:",
      len(march_files))


# б) Versioning және ескі нұсқаны қалпына келтіру

key = keys[0]

old_data = b.get(key, version=0)
old_age = b.objects[key][0]["age"]

print("\nЕскі файл көлемі:", len(old_data), "байт")

# Файлды жаңа дерекпен қайта жазу
b.put(key, b"NEW SERVER LOG DATA", age_days=0)

print("Жаңа нұсқа:", b.get(key))

# Ескі нұсқаны оқу
restored_data = b.get(key, version=0)

print("Ескі нұсқа оқылды:", restored_data == old_data)

# Ескі деректі жаңа ағымдағы нұсқа ретінде қалпына келтіру
b.put(key, restored_data, age_days=old_age)

print("Қалпына келтірілген дерек:",
      b.get(key) == old_data)


# в) Қолжетімділікті басқару

public_key = keys[1]
private_key = keys[2]

b.set_acl(public_key, "public")

print("\nPublic файлға guest қолжетімділігі:",
      b.can_read("guest", public_key))

print("Private файлға guest қолжетімділігі:",
      b.can_read("guest", private_key))


# ==========================================
# 4-ТАПСЫРМА. MD5 АРҚЫЛЫ ТҰТАСТЫҚТЫ ТЕКСЕРУ
# ==========================================

print("\n4. ДЕРЕКТЕРДІҢ ТҰТАСТЫҒЫН ТЕКСЕРУ")

def check_integrity():
    damaged = []

    for k in b.list():
        data = b.get(k)
        saved_md5 = b.objects[k][-1]["md5"]

        calculated_md5 = hashlib.md5(data).hexdigest()

        if calculated_md5 != saved_md5:
            damaged.append(k)

    return damaged


# Барлық файлды тексеру

damaged_before = check_integrity()

print("Бұзылған файлдар саны (бастапқы):",
      len(damaged_before))


# Бір файлды әдейі бұзу

corrupt_key = keys[3]

data = bytearray(b.get(corrupt_key))

data[0] = (data[0] + 1) % 256

b.objects[corrupt_key][-1]["data"] = bytes(data)

print("\nӘдейі бұзылған файл:", corrupt_key)


# Қайта тексеру

damaged_after = check_integrity()

print("Бұзылған файлдар саны (қайта тексеру):",
      len(damaged_after))

print("Анықталған бұзылған файлдар:", damaged_after)


# ==========================================
# 5-ТАПСЫРМА. ҚОРЫТЫНДЫ
# ==========================================

print("\n5. ҚОРЫТЫНДЫ")

print("Барлық кезең сәтті орындалды.")
print("Lifecycle арқылы үнемдеу:",
      round(saving, 2), "%")
print("Versioning ескі деректерді қалпына келтірді.")
print("MD5 бұзылған файлды анықтады.")
