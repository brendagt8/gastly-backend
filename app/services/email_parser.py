import re
from dataclasses import dataclass
from datetime import date
from email.utils import parseaddr


@dataclass
class ParsedTransaction:
    merchant: str
    amount: float
    bank: str
    card_last4: str | None
    date: date


# Cada banco tiene su propio formato de email de compra.
# Cada parser recibe el asunto y cuerpo del email y devuelve ParsedTransaction o None.

def _parse_santander(subject: str, body: str) -> ParsedTransaction | None:
    # Asunto: "Compra con tarjeta 4521 por $1,247.50 en HEB UNIVERSIDAD"
    pattern = r"tarjeta\s+(\d{4}).*?\$([0-9,]+\.?\d*)\s+en\s+(.+)"
    match = re.search(pattern, subject, re.IGNORECASE)
    if not match:
        # Intentar con cuerpo
        match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    card = match.group(1)
    amount = float(match.group(2).replace(",", ""))
    merchant = match.group(3).strip().split("\n")[0]
    return ParsedTransaction(merchant=merchant, amount=amount, bank="Santander", card_last4=card, date=date.today())


def _parse_bbva(subject: str, body: str) -> ParsedTransaction | None:
    # Asunto: "Compra BBVA: $385.00 DOMINOS PIZZA *4521"
    pattern = r"Compra BBVA[:\s]+\$([0-9,]+\.?\d*)\s+(.+?)\s+\*(\d{4})"
    match = re.search(pattern, subject, re.IGNORECASE)
    if not match:
        match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = float(match.group(1).replace(",", ""))
    merchant = match.group(2).strip()
    card = match.group(3)
    return ParsedTransaction(merchant=merchant, amount=amount, bank="BBVA", card_last4=card, date=date.today())


def _parse_nu(subject: str, body: str) -> ParsedTransaction | None:
    # Nu envía: "Tu compra de $269.00 en NETFLIX fue aprobada"
    pattern = r"compra de\s+\$([0-9,]+\.?\d*)\s+en\s+(.+?)\s+fue aprobada"
    match = re.search(pattern, subject, re.IGNORECASE)
    if not match:
        match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    amount = float(match.group(1).replace(",", ""))
    merchant = match.group(2).strip()
    return ParsedTransaction(merchant=merchant, amount=amount, bank="Nu", card_last4=None, date=date.today())


def _parse_banorte(subject: str, body: str) -> ParsedTransaction | None:
    # Banorte: "Movimiento tarjeta 4521: compra $780.15 GASOLINERA PEMEX"
    pattern = r"tarjeta\s+(\d{4}).*?compra\s+\$([0-9,]+\.?\d*)\s+(.+)"
    match = re.search(pattern, subject, re.IGNORECASE)
    if not match:
        match = re.search(pattern, body, re.IGNORECASE)
    if not match:
        return None
    card = match.group(1)
    amount = float(match.group(2).replace(",", ""))
    merchant = match.group(3).strip().split("\n")[0]
    return ParsedTransaction(merchant=merchant, amount=amount, bank="Banorte", card_last4=card, date=date.today())


def _parse_amex(subject: str, body: str) -> ParsedTransaction | None:
    # Amex México envía notificaciones tipo:
    #   Asunto: "Notificación de Cargo Aprobado en su Tarjeta American Express"
    #   Cuerpo:
    #     Cargo aprobado por: $1,234.56 MXN
    #     Establecimiento: SEPHORA POLANCO
    #     Tarjeta American Express terminación: 12345
    #
    # También maneja variantes en el asunto tipo:
    #   "Cargo aprobado por $1,234.56 MXN en SEPHORA POLANCO"
    text = f"{subject}\n{body}"

    amount_match = re.search(
        r"(?:cargo aprobado|monto|importe)[^$]*\$([0-9,]+\.?\d*)",
        text,
        re.IGNORECASE,
    )
    if not amount_match:
        amount_match = re.search(r"\$([0-9,]+\.\d{2})\s*MXN", text, re.IGNORECASE)
    if not amount_match:
        return None
    amount = float(amount_match.group(1).replace(",", ""))

    merchant_match = re.search(
        r"(?:establecimiento|comercio|en)[:\s]+([^\n\r]+)",
        text,
        re.IGNORECASE,
    )
    if not merchant_match:
        return None
    merchant = merchant_match.group(1).strip().rstrip(".,;")
    # Si el match capturó toda una línea con más contexto (e.g. "$X en MERCHANT terminación..."), recortar
    merchant = re.split(r"\s+terminaci[oó]n|\s+tarjeta", merchant, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    card = None
    card_match = re.search(r"terminaci[oó]n[:\s]+(\d{4,5})", text, re.IGNORECASE)
    if card_match:
        card = card_match.group(1)

    return ParsedTransaction(
        merchant=merchant,
        amount=amount,
        bank="American Express",
        card_last4=card,
        date=date.today(),
    )


# Registro de parsers por clave. La tabla bank_senders de la BD mapea cada
# correo remitente a una de estas claves: agregar un remitente nuevo de un
# banco ya soportado es un INSERT en la BD, sin tocar código.
PARSER_REGISTRY = {
    "santander": _parse_santander,
    "bbva": _parse_bbva,
    "nu": _parse_nu,
    "banorte": _parse_banorte,
    "amex": _parse_amex,
}


def parse_bank_email(
    sender: str,
    subject: str,
    body: str,
    email_date: date | None = None,
    sender_map: dict[str, str] | None = None,
) -> ParsedTransaction | None:
    """email_date es la fecha real de llegada del correo (internalDate de Gmail);
    si se proporciona, sustituye el date.today() de los parsers para que las
    transacciones sincronizadas días después conserven su fecha real.
    sender_map mapea correo remitente → parser_key (viene de la tabla bank_senders)."""
    result = None
    # El header From llega como 'Banco <alertas@banco.com>'; extraer solo la dirección
    sender_email = parseaddr(sender)[1] or sender
    parser_key = (sender_map or {}).get(sender_email.lower())
    parser = PARSER_REGISTRY.get(parser_key) if parser_key else None
    if parser:
        result = parser(subject, body)
    if result is None:
        # Si no reconocemos el remitente, intentamos todos los parsers
        for p in PARSER_REGISTRY.values():
            result = p(subject, body)
            if result:
                break
    if result and email_date:
        result.date = email_date
    return result
