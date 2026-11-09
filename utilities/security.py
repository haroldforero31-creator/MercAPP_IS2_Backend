from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse

def hash_password(password: str) -> str:
    """Genera hash seguro para contraseñas."""
    return generate_password_hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash almacenado."""
    return check_password_hash(password_hash, password)

def sanitize_next_url(target: str, fallback: str = '/') -> str:
    """
    Sanitiza una URL de redirección para evitar Open Redirect.
    Solo permite rutas relativas que empiecen con '/' (no '//' ni esquemas externos).
    """
    if not target or not isinstance(target, str):
        return fallback
    target = target.strip()
    # Rechazar URLs con esquema (http://, https://, javascript:, etc.)
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return fallback
    # Rechazar doble slash (//evil.com)
    if target.startswith('//'):
        return fallback
    # Solo aceptar rutas que empiecen con /
    if not target.startswith('/'):
        return fallback
    return target
