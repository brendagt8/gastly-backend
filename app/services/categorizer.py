import anthropic
from app.core.config import settings
from app.models.category import Category

PROMPT_TEMPLATE = """Eres un clasificador de gastos personales para usuarios mexicanos.
Tu única tarea es asignar UNA categoría a cada transacción bancaria.

Categorías disponibles:
{category_lines}

Responde ÚNICAMENTE con el nombre de la categoría, sin explicación ni puntuación."""

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


async def categorize(merchant: str, bank: str, categories: list[Category]) -> str:
    """Asigna una categoría usando Claude Haiku; si no hay API key o la
    llamada falla, usa las keywords de cada categoría como fallback.
    `categories` viene de la BD ordenada por sort_order."""
    valid = {c.id for c in categories}
    default = "otros" if "otros" in valid else (categories[-1].id if categories else "otros")

    if not settings.ANTHROPIC_API_KEY:
        return _rule_based_fallback(merchant, categories, default)

    category_lines = "\n".join(f"- {c.id}: {c.description}" for c in categories)
    try:
        message = await _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=20,
            system=PROMPT_TEMPLATE.format(category_lines=category_lines),
            messages=[{"role": "user", "content": f"Comercio: {merchant}\nBanco: {bank}"}],
        )
    except anthropic.AnthropicError:
        # Si la API falla (rate limit, red, etc.) no rompemos el sync: usamos reglas
        return _rule_based_fallback(merchant, categories, default)
    result = message.content[0].text.strip().lower()
    return result if result in valid else default


def _rule_based_fallback(merchant: str, categories: list[Category], default: str) -> str:
    m = merchant.upper()
    for c in categories:
        if any(k in m for k in c.keyword_list()):
            return c.id
    return default
