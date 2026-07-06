"""Helper to resolve localized text for a requested locale."""


def pick(default: str, english: str | None, locale: str) -> str:
    """Return the English override when asked and available, else the default (Spanish)."""
    if locale == "en" and english:
        return english
    return default
