"""Seeds. Every random choice descends from one hex seed through named
branches, so any entity or sighting can be regenerated exactly."""
from __future__ import annotations

import hashlib
import random


def derive(seed: str, *labels: object) -> str:
    h = hashlib.sha256(seed.encode())
    for label in labels:
        h.update(b"/")
        h.update(str(label).encode())
    return h.hexdigest()[:16]


def rng(seed: str, *labels: object) -> random.Random:
    return random.Random(int(derive(seed, *labels), 16))
