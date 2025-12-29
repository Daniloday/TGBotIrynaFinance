def parse_new_args(text: str) -> tuple[str | None, list[str]]:
    parts = (text or "").split()
    tokens = parts[1:]
    mentions = [t for t in tokens if t.startswith("@") and len(t) > 1]
    name_tokens = [t for t in tokens if not (t.startswith("@") and len(t) > 1)]
    name = " ".join(name_tokens).strip() or None
    return name, mentions
