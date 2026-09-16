"""Shared Markdown-with-frontmatter parsing/serialization for the corpus.

Used by both app.rag.index (read-only, for embedding) and app.admin.corpus
(read/write, for the admin panel) so the two never drift out of sync.
"""
FRONTMATTER_KEYS = ["title", "source", "url", "section"]


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) != 3:
        return {}, raw
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, parts[2].strip()


def serialize_document(meta: dict, body: str) -> str:
    lines = ["---"]
    for key in FRONTMATTER_KEYS:
        value = (meta.get(key) or "").replace("\n", " ").strip()
        lines.append(f'{key}: "{value}"' if value else f"{key}:")
    lines.append("---")
    lines.append(body.strip())
    return "\n".join(lines) + "\n"
