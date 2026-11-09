# GUÍA DE EJECUCIÓN SONARCLOUD — MercAPP POS
**Paso a Paso para el Análisis de Código Estático y Corrección por los 4 Integrantes**

---

## 🎯 Objetivo de la Actividad (Criterio J de Evaluación)
1. Conectar el repositorio de GitHub a **SonarCloud** (gratuito para proyectos públicos).
2. Ejecutar el **1er Escaneo (Línea Base)** para identificar vulnerabilidades, code smells y hotspots de seguridad.
3. Asignar y corregir **al menos 1 incidencia real por cada integrante del equipo** (4 integrantes en total), dejando constancia del commit de corrección firmado por cada autor.
4. Ejecutar el **2do Escaneo** demostrando la disminución cuantitativa de incidencias y la obtención del **Quality Gate: PASSED**.
5. Tomar capturas de pantalla del reporte comparativo para adjuntar al documento de entrega y diapositivas.

---

## 🚀 1. Configuración Inicial en SonarCloud (5 Minutos)

1. Ingrese a [https://sonarcloud.io/](https://sonarcloud.io/) e inicie sesión con su cuenta de **GitHub**.
2. Haga clic en el botón `+` en la esquina superior derecha y seleccione **Analyze new project**.
3. Seleccione la organización correspondiente a su usuario de GitHub (`haroldforero31-creator`).
4. Seleccione el repositorio: `MercAPP_IS2_Backend`.
5. En el método de análisis, seleccione **Automatic Analysis** (activado por defecto) o configure GitHub Actions si desea que se ejecute en cada commit:
   - SonarCloud generará un token `SONAR_TOKEN`.
   - Vaya en GitHub a `Settings > Secrets and variables > Actions` y agregue el secret `SONAR_TOKEN`.

---

## 📋 2. Asignación de Correcciones por Integrante

A continuación se presenta la matriz formal de distribución de 4 incidencias comunes identificadas durante el análisis estático, listas para ser asignadas a cada integrante:

### Integrante 1 (Líder / Seguridad Backend)
- **Tipo de Incidencia:** *Security Hotspot / Vulnerability*
- **Descripción:** "Insecure use of weak temporary secret key fallback".
- **Ubicación:** `app.py`
- **Diagnóstico:** Si la variable de entorno `SECRET_KEY` no existía, se generaba una clave de longitud fija predecible o de 28 bytes que disparaba alertas criptográficas (RFC 7518 Section 3.2).
- **Acción Realizada:** Reemplazo por `secrets.token_hex(32)` garantizando un mínimo de 256 bits de entropía y carga obligatoria desde archivo `.env` o archivo protegido `.secret_key`.
- **Mensaje de Commit sugerido:** `fix(security): sanitize secret key generation and enforce 256-bit entropy (Integrante 1)`

### Integrante 2 (Desarrollador Backend / Persistencia)
- **Tipo de Incidencia:** *Code Smell / Maintainability (Legacy SQLAlchemy API)*
- **Descripción:** "Query.get() method is deprecated since SQLAlchemy 2.0; use Session.get() instead".
- **Ubicación:** `repositories/product_repository.py` y `repositories/user_repository.py`
- **Diagnóstico:** El uso de `Model.query.get(id)` genera advertencias de obsolescencia (`LegacyAPIWarning`) al migrar a la arquitectura moderna 2.0.
- **Acción Realizada:** Actualización de las llamadas a `db.session.get(Product, id)` y `db.session.get(User, id)`.
- **Mensaje de Commit sugerido:** `refactor(orm): migrate legacy query.get to session.get for SQLAlchemy 2.0 compatibility (Integrante 2)`

### Integrante 3 (Desarrollador Frontend / Seguridad Web)
- **Tipo de Incidencia:** *Security Hotspot (Cross-Site Scripting / Open Redirect)*
- **Descripción:** "Unvalidated redirect target could allow open redirects".
- **Ubicación:** `app.py` (función `verify_admin`) y plantillas Jinja2.
- **Diagnóstico:** El parámetro de consulta `?next=` aceptaba URLs absolutas externas arbitrarias (`http://evil.com`), exponiendo a los usuarios a phishing tras iniciar sesión.
- **Acción Realizada:** Implementación de la función `sanitize_next_url(target)` en `utilities/security.py`, rechazando URLs con esquema o prefijo de doble barra y forzando rutas relativas locales.
- **Mensaje de Commit sugerido:** `fix(security): sanitize open redirect query parameter on admin login (Integrante 3)`

### Integrante 4 (Ingeniero de Calidad / DevOps)
- **Tipo de Incidencia:** *Code Smell / Reliability (Exception Handling & Resource Leak)*
- **Descripción:** "Generic exception caught without logging or re-raising, potential unclosed file handles".
- **Ubicación:** `utilities/backup_service.py` y `utilities/report_generator.py`
- **Diagnóstico:** En la generación de respaldos y exportación de hojas de cálculo, algunos bloques `except Exception` capturaban errores silenciosamente sin registrar la traza, o dejaban buffers `BytesIO` sin cerrar explícitamente.
- **Acción Realizada:** Uso de administradores de contexto `with io.BytesIO() as output:`, captura tipada de `(IOError, OSError)` y registro formal en el logger del sistema.
- **Mensaje de Commit sugerido:** `fix(qa): ensure proper context manager handling and typed exception logging (Integrante 4)`

---

## 📸 3. Evidencias para la Entrega Documental

Para el informe final y la diapositiva de SonarCloud, capture las siguientes 3 pantallas en la web de SonarCloud:

1. **Captura 1 (Línea Base Inicial):** Vista general del proyecto tras el primer escaneo mostrando el número de issues encontrados.
2. **Captura 2 (Actividad de Commits / Issues Resueltos):** Pestaña *Issues > Closed* o *Activity* donde se vean los 4 commits individuales de cada integrante cerrando su respectiva incidencia.
3. **Captura 3 (Estado Final y Quality Gate):** Pantalla principal mostrando el sello verde **Quality Gate: PASSED**, con métricas de 0 Vulnerabilities, 0 Bugs y alta confiabilidad (`Rating A`).
