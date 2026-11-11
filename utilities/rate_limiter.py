import time
import threading
from functools import wraps
from flask import request, jsonify, flash, redirect, render_template, make_response

class InMemoryRateLimiter:
    """
    Controlador de tasa de peticiones (Rate Limiter) en memoria y seguro para concurrencia (thread-safe).
    Protege endpoints críticos contra fuerza bruta y ataques de denegación de servicio (DoS).
    """
    def __init__(self):
        self._requests = {}  # key -> list of timestamps
        self._lock = threading.Lock()

    def _get_client_ip(self):
        # Manejo de proxies (Render, AWS ALB, Nginx)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.remote_addr or '127.0.0.1'

    def is_rate_limited(self, endpoint_key: str, max_requests: int, window_seconds: int):
        now = time.time()
        client_ip = self._get_client_ip()
        full_key = f"{endpoint_key}:{client_ip}"

        with self._lock:
            # Limpiar entradas expiradas periódicamente
            timestamps = self._requests.get(full_key, [])
            cutoff = now - window_seconds
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                oldest_in_window = valid_timestamps[0]
                retry_after = int(oldest_in_window + window_seconds - now) + 1
                return True, max(1, retry_after)

            valid_timestamps.append(now)
            self._requests[full_key] = valid_timestamps

            # Limpieza global si la estructura crece demasiado
            if len(self._requests) > 10000:
                keys_to_delete = [k for k, v in self._requests.items() if not v or v[-1] < cutoff]
                for k in keys_to_delete:
                    del self._requests[k]

            return False, 0

    def limit(self, max_requests: int = 5, window_seconds: int = 60, key: str = None):
        """
        Decorador para limitar peticiones a una ruta específica.
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Solo aplicar límites a métodos de escritura o autenticación sensible (POST/PUT/DELETE)
                if request.method in ('POST', 'PUT', 'DELETE'):
                    rule_key = key or request.endpoint or request.path
                    is_limited, retry_after = self.is_rate_limited(rule_key, max_requests, window_seconds)
                    
                    if is_limited:
                        is_api = (
                            request.path.startswith('/api/') or 
                            request.is_json or 
                            request.headers.get('Accept') == 'application/json'
                        )
                        
                        if is_api:
                            resp = jsonify({
                                'success': False,
                                'error': 'Demasiadas solicitudes. Por favor intente más tarde.',
                                'retry_after': retry_after
                            })
                            resp.status_code = 429
                            resp.headers['Retry-After'] = str(retry_after)
                            return resp
                        
                        flash(f'Demasiados intentos desde esta red. Por favor espere {retry_after} segundos.', 'error')
                        resp = make_response(render_template('inicio_sesion.html'), 429)
                        resp.headers['Retry-After'] = str(retry_after)
                        return resp

                return f(*args, **kwargs)
            return decorated_function
        return decorator

# Instancia singleton para la aplicación
limiter = InMemoryRateLimiter()

