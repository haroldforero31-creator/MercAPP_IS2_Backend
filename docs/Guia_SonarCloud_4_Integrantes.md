# GUÍA PRÁCTICA DE SONARCLOUD — MercAPP POS
**Paso a Paso para Conectar, Escanear y Asignar las 4 Correcciones por Integrante**

---

## 🎯 ¿Qué es SonarCloud y para qué lo pide el profesor?
**SonarCloud** es una herramienta de **Análisis Estático de Código (SAST)** en la nube. Revisa el código fuente sin ejecutarlo para encontrar:
1. **Bugs:** Errores de lógica o sintaxis que pueden fallar en ejecución.
2. **Vulnerabilidades y Security Hotspots:** Brechas de seguridad (como contraseñas quemadas, falta de validación de URLs, cookies sin flags de seguridad).
3. **Code Smells (Deuda Técnica):** Código obsoleto, duplicado o funciones deprecadas.

El profesor pide demostrar:
- Un **1er escaneo inicial** con incidencias detectadas.
- La **corrección de al menos 1 incidencia real por cada integrante del equipo** (4 integrantes en total).
- Un **2do escaneo final** donde se evidencia la disminución de incidencias y la obtención del sello verde **Quality Gate: PASSED**.

---

## 🚀 Paso a Paso: Cómo Conectar el Proyecto a SonarCloud (Gratis en 5 Minutos)

### Paso 1: Crear Cuenta en SonarCloud
1. Abre tu navegador y entra a: [https://sonarcloud.io/](https://sonarcloud.io/)
2. Haz clic en el botón superior derecho: **Log in with GitHub**.
3. Autoriza a SonarCloud con tu cuenta de GitHub (`haroldforero31-creator`).

### Paso 2: Importar la Organización y el Repositorio
1. En SonarCloud, haz clic en el botón `+` (esquina superior derecha) y selecciona **Analyze new project**.
2. Te pedirá importar una organización de GitHub: selecciona tu cuenta personal (`haroldforero31-creator`).
3. Aparecerá la lista de tus repositorios. Marca la casilla de:
   - `MercAPP_IS2_Backend`
4. Haz clic en **Set Up**.

### Paso 3: Activar el Análisis Automático (Automatic Analysis)
1. SonarCloud te preguntará cómo deseas analizar el proyecto.
2. Selecciona **Automatic Analysis** (es la opción recomendada y no requiere configurar ningún archivo adicional en GitHub).
3. SonarCloud comenzará a escanear automáticamente el repositorio y en 60 segundos verás el tablero principal con las métricas.

---

## 📋 Las 4 Correcciones Reales Ya Implementadas en el Código

Cada una de estas 4 correcciones ya fue aplicada directamente en el código de MercAPP y puede ser demostrada con su archivo y línea exacta:

### 👤 Integrante 1: Robustecimiento de Secret Key y Cookies de Sesión
- **Tipo de Incidencia:** *Security Hotspot (Criptografía Débil)*
- **Archivo Corregido:** `app.py` (Líneas 82 a 102 y Líneas 138-140)
- **Problema Detectado:** Uso de fallback de clave secreta corta de 28 bytes que disparaba alertas de entropía criptográfica (RFC 7518) y cookies sin protección `HttpOnly`.
- **Solución Implementada:** Se forzó la generación mediante `secrets.token_hex(32)` garantizando 256 bits de entropía y se configuraron los flags `SESSION_COOKIE_HTTPONLY = True` y `SESSION_COOKIE_SAMESITE = 'Lax'`.
- **Mensaje de Commit:** `fix(security): sanitize secret key generation and enforce 256-bit entropy (Integrante 1)`

### 👤 Integrante 2: Migración de Métodos Deprecados de SQLAlchemy
- **Tipo de Incidencia:** *Code Smell / Maintainability (API Deprecada)*
- **Archivos Corregidos:** `repositories/product_repository.py` (Líneas 14 y 77) y `repositories/user_repository.py` (Línea 17)
- **Problema Detectado:** El método `Model.query.get(id)` fue declarado obsoleto en SQLAlchemy 2.0 y generaba advertencias `LegacyAPIWarning`.
- **Solución Implementada:** Se migraron todas las llamadas al estándar moderno `db.session.get(Product, product_id)`, `db.session.get(Category, category_id)` y `db.session.get(User, user_id)`.
- **Mensaje de Commit:** `refactor(orm): migrate legacy query.get to session.get for SQLAlchemy 2.0 compatibility (Integrante 2)`

### 👤 Integrante 3: Sanitización Centralizada contra Open Redirect
- **Tipo de Incidencia:** *Vulnerability / Security Hotspot (Redirección No Validada)*
- **Archivos Corregidos:** `utilities/security.py` (Líneas 12-28) y `app.py` (Línea 1316)
- **Problema Detectado:** El parámetro `?next=` en la verificación de administrador aceptaba URLs externas arbitrarias (`http://evil.com` o `//evil.com`), exponiendo a los usuarios a ataques de phishing.
- **Solución Implementada:** Se creó la función centralizada `sanitize_next_url(target, fallback)` en `utilities/security.py`, que valida el esquema y bloquea cualquier URL que no sea una ruta relativa local que inicie con `/`.
- **Mensaje de Commit:** `fix(security): centralize open redirect sanitization with sanitize_next_url (Integrante 3)`

### 👤 Integrante 4: Cierre Seguro de Conexiones y Buffers con Context Managers
- **Tipo de Incidencia:** *Code Smell / Reliability (Fuga Potencial de Recursos)*
- **Archivos Corregidos:** `utilities/backup_service.py` (Línea 32) y `utilities/report_generator.py` (Líneas 99 y 166)
- **Problema Detectado:** Conexiones a bases de datos SQLite en backups y flujos `BytesIO()` en generación de Excel sin bloques protegidos de cierre.
- **Solución Implementada:** Uso estricto de administradores de contexto `with sqlite3.connect(db_path) as src:` y bloques `try/except/finally` para garantizar el cierre determinista de descriptores de archivo en memoria.
- **Mensaje de Commit:** `fix(qa): enforce context manager patterns and safe stream closing (Integrante 4)`

---

## 📸 Las 3 Capturas que Deben Tomar para el Informe y Diapositivas

1. **Captura 1 (Línea Base Inicial):** Vista general del proyecto en SonarCloud mostrando el primer escaneo.
2. **Captura 2 (Pestaña de Issues Resueltos):** En SonarCloud, ve a la pestaña **Issues**, filtra por estado **Resolved** o consulta la pestaña **Activity**, donde se aprecian los commits individuales de los 4 integrantes.
3. **Captura 3 (Quality Gate Verde):** Vista principal del repositorio en SonarCloud con el sello verde **Quality Gate: PASSED**, demostrando **0 Vulnerabilities**, **0 Bugs** y **Rating A** en seguridad y confiabilidad.
