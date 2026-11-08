import hashlib

# 21-НҰСҚА (RAW_TX әдістемелік нұсқаулықтағы дұрыс мәнімен ауыстырылды)
RAW_TX = (
    "0100000001a7d28bef5691028027b2d537e7b18a80b58b3b8c66dab39ed361dc362b3b8126"
    "020000006a47304402206b62d20f7db3f11f5d816253facb063de0524e3560f603b6f634c"
    "f62b02444cb0220af990abba45cff893f37be58572bcae8a0bacf6b106e822ae01112d195"
    "c1faee012103f6a59064ea2fb79573e239efc9bb6979547cd634798148348b50d15d198ae"
    "c1cfeffffff022052a600000000001976a9145de14680f98db78a49dc862d38fb83fdc90d"
    "c86988ac20a10700000000001976a91408cf40d086ffd8f4611e110a5f9a38cf783c39498"
    "8ac00000000"
)

def read_varint(data, pos):
    """VarInt оқиды, (мән, жаңа позиция) қайтарады."""
    first = data[pos]
    if first < 0xfd:
        return first, pos + 1
    size = {0xfd: 2, 0xfe: 4, 0xff: 8}[first]
    value = int.from_bytes(data[pos + 1:pos + 1 + size], "little")
    return value, pos + 1 + size

def script_type(script):
    """scriptPubKey түрін анықтайды. (түр, пайдалы деректер) қайтарады."""
    # P2PKH: 76 a9 14 <20> 88 ac
    if (len(script) == 25 and script[0] == 0x76 and script[1] == 0xa9
            and script[2] == 0x14 and script[23] == 0x88 and script[24] == 0xac):
        return "P2PKH", script[3:23].hex()
    # P2PK: <33> ac
    if len(script) == 35 and script[0] == 0x21 and script[34] == 0xac:
        return "P2PK", script[1:34].hex()
    # P2SH: a9 14 <20> 87
    if len(script) == 23 and script[0] == 0xa9 and script[1] == 0x14 and script[22] == 0x87:
        return "P2SH", script[2:22].hex()
    # P2WPKH: 00 14 <20>
    if len(script) == 22 and script[0] == 0x00 and script[1] == 0x14:
        return "P2WPKH", script[2:22].hex()
    # P2WSH: 00 20 <32>
    if len(script) == 34 and script[0] == 0x00 and script[1] == 0x20:
        return "P2WSH", script[2:34].hex()
    # P2TR: 51 20 <32>
    if len(script) == 34 and script[0] == 0x51 and script[1] == 0x20:
        return "P2TR", script[2:34].hex()
    return "UNKNOWN", ""

def parse_tx(raw_hex):
    data = bytes.fromhex(raw_hex)
    pos = 0
    tx = {"inputs": [], "outputs": []}

    # 1) version (4 байт, little-endian)
    tx["version"] = int.from_bytes(data[pos:pos + 4], "little")
    pos += 4

    # 2) кірістер саны (VarInt)
    n_inputs, pos = read_varint(data, pos)

    # 3) әр кіріс
    for _ in range(n_inputs):
        inp = {}
        inp["prev_txid"] = data[pos:pos + 32][::-1].hex()   # кері айналдырамыз
        pos += 32
        inp["vout"] = int.from_bytes(data[pos:pos + 4], "little")
        pos += 4
        script_len, pos = read_varint(data, pos)
        inp["scriptSig"] = data[pos:pos + script_len].hex()
        pos += script_len
        inp["sequence"] = data[pos:pos + 4].hex()
        pos += 4
        tx["inputs"].append(inp)

    # 4) шығыстар саны (VarInt)
    n_outputs, pos = read_varint(data, pos)

    # 5) әр шығыс
    for _ in range(n_outputs):
        out = {}
        out["value_sat"] = int.from_bytes(data[pos:pos + 8], "little")
        pos += 8
        script_len, pos = read_varint(data, pos)
        script = data[pos:pos + script_len]
        out["scriptPubKey"] = script.hex()
        stype, payload = script_type(script)
        out["script_type"] = stype
        if payload:
            out["payload"] = payload
        pos += script_len
        tx["outputs"].append(out)

    # 6) locktime (4 байт)
    tx["locktime"] = int.from_bytes(data[pos:pos + 4], "little")
    pos += 4

    tx["size"] = len(data)
    tx["parsed_bytes"] = pos
    return tx

def calc_txid(raw_hex):
    """txid = қос SHA-256, байттар кері айналдырылады."""
    data = bytes.fromhex(raw_hex)
    h = hashlib.sha256(hashlib.sha256(data).digest()).digest()
    return h[::-1].hex()

def main():
    tx = parse_tx(RAW_TX)

    print("=" * 60)
    print("ТРАНЗАКЦИЯНЫ ТАЛДАУ НӘТИЖЕЛЕРІ (21-нұсқа)")
    print("=" * 60)
    print(f"version       : {tx['version']}")
    print(f"locktime      : {tx['locktime']}")
    print(f"size          : {tx['size']} байт")
    print(f"parsed_bytes  : {tx['parsed_bytes']} (size-қа тең болуы керек)")
    print()

    print(f"КІРІСТЕР: {len(tx['inputs'])}")
    for i, inp in enumerate(tx["inputs"]):
        print(f"  Input #{i}")
        print(f"    prev_txid : {inp['prev_txid']}")
        print(f"    vout      : {inp['vout']}")
        print(f"    scriptSig : {inp['scriptSig']}  ({len(inp['scriptSig'])//2} байт)")
        print(f"    sequence  : {inp['sequence']}")
    print()

    print(f"ШЫҒЫСТАР: {len(tx['outputs'])}")
    total_out = 0
    for i, out in enumerate(tx["outputs"]):
        print(f"  Output #{i}")
        print(f"    value      : {out['value_sat']} sat = {out['value_sat']/1e8:.8f} BTC")
        print(f"    scriptPubKey: {out['scriptPubKey']}  ({len(out['scriptPubKey'])//2} байт)")
        print(f"    type       : {out['script_type']}")
        if "payload" in out:
            key = "hash160" if out["script_type"] == "P2PKH" else "payload"
            print(f"    {key} : {out['payload']}")
        total_out += out["value_sat"]
    print()

    print(f"Шығыстар сомасы : {total_out} sat = {total_out/1e8:.8f} BTC")
    input_value = 11409000  # тапсырмадағы 0.11409000 BTC
    print(f"Кірістер сомасы : {input_value} sat = 0.11409000 BTC")
    fee = input_value - total_out
    print(f"Комиссия        : {fee} sat = {fee/1e8:.8f} BTC")
    print()
    print(f"txid            : {calc_txid(RAW_TX)}")

if __name__ == "__main__":
    main()