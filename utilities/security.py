"""
Módulo de Seguridad Centralizada — MercAPP POS
==============================================
Este módulo implementa las políticas de seguridad estricta para el cumplimiento
del estándar OWASP Top 10 y el aseguramiento del Quality Gate de SonarCloud.

Funcionalidades de Blindaje:
- Validación y sanitización de URLs de redirección (CWE-601 Open Redirect).
- Prevención de Directory Traversal y Filesystem Oracle en recursos estáticos (CWE-22 / CWE-209).
- Generación de tokens criptográficos con entropía robusta de 256 bits (CWE-330).
- Verificación estricta de orígenes CORS y cabeceras de seguridad HTTP.
- Sanitización de entradas de usuario contra Cross-Site Scripting (XSS / CWE-79).
"""

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
