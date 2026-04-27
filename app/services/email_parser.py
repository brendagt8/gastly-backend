import re
from dataclasses import dataclass
from datetime import date


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


PARSERS = [_parse_santander, _parse_bbva, _parse_nu, _parse_banorte]

BANK_SENDERS = {
    "alertas@notificaciones.santander.com.mx": _parse_santander,
    "notificaciones@bbva.com": _parse_bbva,
    "notificacoes@nubank.com.br": _parse_nu,
    "alertas@banorte.com": _parse_banorte,
}


def parse_bank_email(sender: str, subject: str, body: str) -> ParsedTransaction | None:
    parser = BANK_SENDERS.get(sender.lower())
    if parser:
        return parser(subject, body)
    # Si no reconocemos el remitente, intentamos todos los parsers
    for p in PARSERS:
        result = p(subject, body)
        if result:
            return result
    return None
