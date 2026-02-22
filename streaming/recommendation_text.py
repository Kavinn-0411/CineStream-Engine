"""Shared text feature for NB recommendation (train + infer must match)."""


def training_example_text(user_id: int, genres: str | None, title: str | None) -> str:
    """Bag-of-words style string: user token + genres + title (lowercased)."""
    g = (genres or "").replace(",", " ").lower().strip()
    t = (title or "").lower().strip()
    return f"u{int(user_id)} {g} {t}".strip()
