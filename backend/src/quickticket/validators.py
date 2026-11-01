def filter_string_field(value: str) -> str:
    """Strip whitespace and filter out non-printable characters."""
    value = value.strip()
    return "".join(c for c in value if c.isprintable())
