#!/usr/bin/env python3
import json
import gzip


def load_candidates(path):
    open_func = gzip.open if str(path).endswith(".gz") else open
    mode = "rt" if str(path).endswith(".gz") else "r"
    with open_func(path, mode, encoding="utf-8") as f:
        raw = f.read().strip()
    if raw.startswith("["):
        return json.loads(raw)
    return [json.loads(line) for line in raw.splitlines() if line]
