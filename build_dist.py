import os
import sys
import shutil
import zipfile
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'MercAPP_IS2_Frontend'))
DIST_ROOT = os.path.join(BASE_DIR, 'dist_package')
PACKAGE_FOLDER = os.path.join(DIST_ROOT, 'MercAPP_IS2_Windows')
ZIP_OUTPUT = os.path.join(BASE_DIR, 'MercAPP_IS2_Windows.zip')

def clean_old():
    print("[1/5] Limpiando carpetas de empaquetado anteriores...")
    if os.path.exists(DIST_ROOT):
        shutil.rmtree(DIST_ROOT, ignore_errors=True)
    if os.path.exists(ZIP_OUTPUT):
        os.remove(ZIP_OUTPUT)
    os.makedirs(PACKAGE_FOLDER, exist_ok=True)

def copy_application_files():
    print("[2/5] Copiando archivos de la aplicacion...")
    # 1. Backend source files & directories
    for item in ['app.py', 'launcher.py', 'requirements.txt', '.env', 'mercapp.ico', 'iniciar_mercapp.bat']:
        src = os.path.join(BASE_DIR, item)
        if os.path.exists(src):
            shutil.copy2(src, PACKAGE_FOLDER)

    for folder in ['controllers', 'dtos', 'models', 'repositories', 'services', 'utilities', 'uploads']:
        src = os.path.join(BASE_DIR, folder)
        dst = os.path.join(PACKAGE_FOLDER, folder)
        if os.path.exists(src):
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    # 2. Copiar base de datos SQLite mercapp.db
    db_src = os.path.join(BASE_DIR, 'mercapp.db')
    if os.path.exists(db_src):
        shutil.copy2(db_src, os.path.join(PACKAGE_FOLDER, 'mercapp.db'))
        print("  - Base de datos local mercapp.db copiada.")

    # 3. Frontend folder (MercAPP_IS2_Frontend)
    dst_frontend = os.path.join(PACKAGE_FOLDER, 'MercAPP_IS2_Frontend')
    for sub in ['templates', 'static']:
        src_sub = os.path.join(FRONTEND_DIR, sub)
        dst_sub = os.path.join(dst_frontend, sub)
        if os.path.exists(src_sub):
            shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print("  - Plantillas y recursos estáticos copiados.")

def create_launcher_and_readme():
    print("[3/5] Creando accesos directos y manual de instrucciones...")
    
    # Batch directo en la raiz del paquete
    bat_content = """@echo off
title MercAPP IS2 - Punto de Venta
cd /d "%~dp0"

echo ========================================================
echo        Iniciando MercAPP IS2 (Punto de Venta)
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Iniciando con Python...
    python launcher.py
    goto FIN
)

if exist "venv\\Scripts\\python.exe" (
    echo [INFO] Utilizando entorno virtual local...
    "venv\\Scripts\\python.exe" launcher.py
    goto FIN
)

echo [ERROR] No se detecto instalacion de Python en este equipo.
echo Por favor instala Python 3.10 o superior (marcando 'Add Python to PATH').
pause

:FIN
"""
    with open(os.path.join(PACKAGE_FOLDER, 'INICIAR_MERCAPP.bat'), 'w', encoding='utf-8') as f:
        f.write(bat_content)

    readme_content = """============================================================
           MercAPP IS2 — Sistema de Punto de Venta (POS)
============================================================

INSTRUCCIONES DE USO:
------------------------------------------------------------
1. Para iniciar el sistema:
   Haz doble clic en: INICIAR_MERCAPP.bat

2. MercAPP iniciará el servidor local de alto rendimiento (Waitress)
   y abrirá automáticamente la ventana de aplicación en modo
   escritorio (usando Microsoft Edge o Google Chrome sin barras
   de navegación para emular una aplicación nativa de POS).

3. Funcionamiento Offline:
   MercAPP IS2 funciona 100% de manera autónoma y local
   utilizando la base de datos SQLite 'mercapp.db'. No requiere
   conexión a internet para el cobro, escaneo, tickets ni arqueos.
   Cuando exista conexión, las notificaciones y correos se
   sincronizan automáticamente.

4. Acceso por defecto:
   - URL Local: http://127.0.0.1:5001/pos
   - Credenciales de Administrador:
     Email: tu correo registrado o configurado
   - Asistente de Voz Merki:
     Presiona el botón de Merki o di 'Oye Merki' en la caja.
    - Licencia del Sistema:
      Contraseña maestra de desbloqueo y renovación (60 días): Foreroyulian321.2026

============================================================
"""
    with open(os.path.join(PACKAGE_FOLDER, 'LEEME_INSTRUCCIONES.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)

def build_zip():
    print("[4/5] Comprimiendo paquete en formato .ZIP (compatible con WinRAR y Windows)...")
    with zipfile.ZipFile(ZIP_OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PACKAGE_FOLDER):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DIST_ROOT)
                zf.write(full_path, rel_path)
    
    size_mb = os.path.getsize(ZIP_OUTPUT) / (1024 * 1024)
    print(f"[5/5] Paquete ZIP generado: {ZIP_OUTPUT} ({size_mb:.2f} MB)")
    
    # WinRAR generation if installed
    winrar_exe = r'C:\Program Files\WinRAR\Rar.exe'
    rar_output = os.path.join(BASE_DIR, 'MercAPP_IS2_Windows.rar')
    if os.path.exists(winrar_exe):
        print("  - Detectado WinRAR en el sistema, generando archivo .RAR...")
        if os.path.exists(rar_output):
            os.remove(rar_output)
        res = subprocess.run([winrar_exe, 'a', '-r', '-ep1', rar_output, PACKAGE_FOLDER], capture_output=True)
        if res.returncode == 0 and os.path.exists(rar_output):
            rar_size_mb = os.path.getsize(rar_output) / (1024 * 1024)
            print(f"  - Paquete .RAR generado exitosamente: {rar_output} ({rar_size_mb:.2f} MB)")
        else:
            print(f"  - Nota WinRAR: {res.stderr.decode('latin1', errors='ignore')}")

if __name__ == '__main__':
    clean_old()
    copy_application_files()
    create_launcher_and_readme()
    build_zip()
    print("\nProceso de empaquetado finalizado con exito!")
