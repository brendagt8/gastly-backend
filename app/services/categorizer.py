import anthropic
from app.core.config import settings

CATEGORIES = ["despensa", "salidas", "gasolina", "salud", "suscripciones", "ropa", "otros"]

SYSTEM_PROMPT = """Eres un clasificador de gastos personales para usuarios mexicanos.
Tu única tarea es asignar UNA categoría a cada transacción bancaria.

Categorías disponibles:
- despensa: supermercados, tiendas de abarrotes, OXXO, Walmart, HEB, Soriana, Chedraui
- salidas: restaurantes, cafeterías, bares, comida rápida, antros, entretenimiento
- gasolina: gasolineras, estacionamientos, casetas, Uber/Didi si es transporte
- salud: farmacias, hospitales, clínicas, médicos, laboratorios, ópticas
- suscripciones: Netflix, Spotify, Disney+, HBO, Amazon Prime, servicios digitales mensuales
- ropa: tiendas de ropa, zapaterías, Zara, H&M, Nike, Adidas
- otros: todo lo que no encaje en las categorías anteriores

Responde ÚNICAMENTE con el nombre de la categoría, sin explicación ni puntuación."""


async def categorize(merchant: str, bank: str) -> str:
    if not settings.ANTHROPIC_API_KEY:
        return _rule_based_fallback(merchant)

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Comercio: {merchant}\nBanco: {bank}"}],
    )
    result = message.content[0].text.strip().lower()
    return result if result in CATEGORIES else "otros"


def _rule_based_fallback(merchant: str) -> str:
    m = merchant.upper()
    if any(k in m for k in ["HEB", "WALMART", "SORIANA", "CHEDRAUI", "OXXO", "SEVEN", "SUPER", "MERCADO", "BODEGA"]):
        return "despensa"
    if any(k in m for k in ["PEMEX", "TOTAL GAS", "GASOLINERA", "BP", "SHELL", "G500"]):
        return "gasolina"
    if any(k in m for k in ["FARMACIA", "GUADALAJARA", "SIMILARES", "BENAVIDES", "HOSPITAL", "CLINICA", "DR ", "DRA "]):
        return "salud"
    if any(k in m for k in ["NETFLIX", "SPOTIFY", "DISNEY", "HBO", "AMAZON PRIME", "APPLE", "GOOGLE ONE", "YOUTUBE"]):
        return "suscripciones"
    if any(k in m for k in ["ZARA", "H&M", "NIKE", "ADIDAS", "PULL&BEAR", "STRADIVARIUS", "BERSHKA"]):
        return "ropa"
    if any(k in m for k in ["STARBUCKS", "MCDONALD", "DOMINO", "PIZZA", "RESTAURANT", "SUSHI", "TACO", "BURGER", "KFC"]):
        return "salidas"
    return "otros"
