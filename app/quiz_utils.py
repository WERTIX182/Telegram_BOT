from __future__ import annotations

import hashlib
import random


SHUFFLE_VERSION = "quiz-shuffle-v1"


def stable_option_order(
    *,
    attempt_id: int,
    item_id: str,
    question_index: int,
    option_count: int,
) -> tuple[int, ...]:
    """Return a reproducible canonical-index order for one saved attempt."""
    if option_count < 1:
        raise ValueError("A quiz must contain at least one option")
    seed_material = (
        f"{SHUFFLE_VERSION}:{attempt_id}:{item_id}:{question_index}:{option_count}"
    )
    digest = hashlib.sha256(seed_material.encode("utf-8")).digest()
    randomizer = random.Random(int.from_bytes(digest, "big"))
    indices = list(range(option_count))
    randomizer.shuffle(indices)
    return tuple(indices)

