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
    
    # 1. Copiar ejecutable nativo MercAPP.exe si existe
    exe_src = os.path.join(BASE_DIR, 'dist', 'MercAPP.exe')
    if os.path.exists(exe_src):
        shutil.copy2(exe_src, os.path.join(PACKAGE_FOLDER, 'MercAPP.exe'))
        print("  - Ejecutable binario nativo MercAPP.exe copiado.")

    # 2. Copiar base de datos SQLite mercapp.db
    db_src = os.path.join(BASE_DIR, 'mercapp.db')
    if os.path.exists(db_src):
        shutil.copy2(db_src, os.path.join(PACKAGE_FOLDER, 'mercapp.db'))
        print("  - Base de datos local mercapp.db copiada.")

    # 3. Copiar archivos clave de configuracion e iconos
    for item in ['mercapp.ico', '.env']:
        src = os.path.join(BASE_DIR, item)
        if os.path.exists(src):
            shutil.copy2(src, PACKAGE_FOLDER)

    # 4. Carpeta de uploads (para imagenes de productos y categorias)
    uploads_dir = os.path.join(PACKAGE_FOLDER, 'uploads')
    os.makedirs(os.path.join(uploads_dir, 'products'), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, 'categories'), exist_ok=True)

def create_launcher_and_readme():
    print("[3/5] Creando accesos directos y manual de instrucciones...")
    
    # Batch directo en la raiz del paquete para compatibilidad
    bat_content = """@echo off
title MercAPP IS2 - Punto de Venta
cd /d "%~dp0"

echo ========================================================
echo        Iniciando MercAPP IS2 (Punto de Venta)
echo ========================================================
echo.

if exist "MercAPP.exe" (
    echo [INFO] Iniciando ejecutable MercAPP.exe...
    start "" "MercAPP.exe"
    exit /b
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [INFO] Iniciando con Python...
    python launcher.py
    exit /b
)

echo [ERROR] No se encontro MercAPP.exe ni Python instalado.
pause
"""
    with open(os.path.join(PACKAGE_FOLDER, 'INICIAR_MERCAPP.bat'), 'w', encoding='utf-8') as f:
        f.write(bat_content)

    readme_content = """============================================================
           MercAPP IS2 — Sistema de Punto de Venta (POS)
============================================================

INSTRUCCIONES DE USO:
------------------------------------------------------------
1. Para iniciar el sistema:
   Simplemente haz doble clic en: MercAPP.exe
   (o en INICIAR_MERCAPP.bat).
   No requiere instalar Python ni configurar librerías.

2. MercAPP iniciará automáticamente el servidor local de alto
   rendimiento y abrirá la ventana de aplicación en modo quiosco
   de escritorio (sin barras de navegación para emular un POS nativo).

3. Licencia del Sistema:
   - Contraseña maestra de desbloqueo y renovación (60 días):
     Foreroyulian321.2026
   - Al abrir por primera vez, ingresa la clave para activar
     tu periodo bimensual de uso.

4. Funcionamiento Offline:
   MercAPP IS2 funciona 100% de manera autónoma y local
   utilizando la base de datos SQLite 'mercapp.db'. No requiere
   conexión a internet para el cobro, escaneo, tickets ni arqueos.

5. Asistente de Voz Inteligente Merki:
   Presiona el botón de Merki en la caja o di 'Oye Merki'
   para activar comandos rápidos por voz.

============================================================
"""
    with open(os.path.join(PACKAGE_FOLDER, 'LEEME_INSTRUCCIONES.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)

def build_zip():
    print("[4/5] Comprimiendo paquete en formato .ZIP...")
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
