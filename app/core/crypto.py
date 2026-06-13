from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, TypeDecorator
from app.core.config import settings

_fernet = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode()) if settings.TOKEN_ENCRYPTION_KEY else None


class EncryptedString(TypeDecorator):
    """Columna String que se cifra con Fernet al guardar y se descifra al leer.

    Si TOKEN_ENCRYPTION_KEY no está definida, guarda en texto plano (solo
    aceptable en desarrollo). Al leer, un valor que no es un token Fernet
    válido se devuelve tal cual: cubre filas guardadas antes de activar el
    cifrado sin invalidar esas sesiones.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        if value is None or _fernet is None:
            return value
        return _fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: str | None, dialect) -> str | None:
        if value is None or _fernet is None:
            return value
        try:
            return _fernet.decrypt(value.encode()).decode()
        except InvalidToken:
            return value  # fila previa al cifrado
