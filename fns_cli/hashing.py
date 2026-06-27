"""Fast Note Sync CLI - Hashing utilities."""


def compute_path_hash(path_str):
    """Compute 32-bit path hash matching FNS server implementation.

    Uses polynomial rolling hash on Unicode code points: h = h * 31 + rune,
    then convert to signed int32. (Go strings iterate over runes, not bytes.)
    """
    h = 0
    for ch in path_str:
        h = ((h * 31) + ord(ch)) & 0xFFFFFFFF
    # Convert to signed 32-bit integer
    if h >= 0x80000000:
        h -= 0x100000000
    return str(h)
