import os
import shutil
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))
staging_parent = os.path.join(base_dir, 'staging')
staging_dir = os.path.join(staging_parent, 'MercAPP_IS2_Windows')

if os.path.exists(staging_parent):
    shutil.rmtree(staging_parent)
os.makedirs(staging_dir, exist_ok=True)

# 1. Copiar ejecutable recién compilado con PyInstaller
shutil.copy2(os.path.join(base_dir, 'dist', 'MercAPP.exe'), os.path.join(staging_dir, 'MercAPP.exe'))
print('1. Copiado MercAPP.exe')

# 2. Copiar plantillas actualizadas (50 plantillas completas)
shutil.copytree(os.path.join(base_dir, 'templates'), os.path.join(staging_dir, 'templates'), dirs_exist_ok=True)
num_tpl = len(os.listdir(os.path.join(staging_dir, 'templates')))
print(f'2. Copiadas {num_tpl} plantillas en templates/')

# 3. Copiar recursos estáticos (CSS, JS, imágenes, fuentes)
shutil.copytree(os.path.join(base_dir, 'static'), os.path.join(staging_dir, 'static'), dirs_exist_ok=True)
print('3. Copiados recursos en static/')

# 4. Copiar base de datos inicial, icono y configuración .env
for filename in ['mercapp.db', 'mercapp.ico', '.env']:
    src = os.path.join(base_dir, filename)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(staging_dir, filename))
        print(f'4. Copiado {filename}')

# 5. Crear INICIAR_MERCAPP.bat
bat_lines = [
    "@echo off",
    "title MercAPP IS2 - Punto de Venta",
    'cd /d "%~dp0"',
    "echo ========================================================",
    "echo        Iniciando MercAPP IS2 (Punto de Venta)",
    "echo ========================================================",
    "echo.",
    'if exist "MercAPP.exe" (',
    "    echo [INFO] Iniciando ejecutable MercAPP.exe...",
    '    start "" "MercAPP.exe"',
    "    exit /b",
    ")",
    "where python >nul 2>nul",
    "if %ERRORLEVEL% equ 0 (",
    "    echo [INFO] Iniciando con Python...",
    "    python launcher.py",
    "    exit /b",
    ")",
    "echo [ERROR] No se encontro MercAPP.exe ni Python instalado.",
    "pause"
]
with open(os.path.join(staging_dir, 'INICIAR_MERCAPP.bat'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(bat_lines) + '\n')
print('5. Creado INICIAR_MERCAPP.bat')

# 6. Crear LEEME_INSTRUCCIONES.txt
leeme = """========================================================
           MercAPP IS2 - Sistema POS de Escritorio
========================================================

INSTRUCCIONES DE USO:
1. Haz doble clic en 'INICIAR_MERCAPP.bat' o directamente en 'MercAPP.exe'.
2. El sistema iniciará automáticamente el servidor local de alta velocidad y abrirá tu navegador web en http://127.0.0.1:5000.
3. Operación 100% offline garantizada sobre SQLite WAL local.
4. Generación de reportes (Excel .xlsx y PDF) totalmente funcional.
5. El envío de correos opera con la configuración del archivo .env.

Requisitos: Windows 10 o Windows 11 (64-bit). No requiere instalar Python ni dependencias externas.
"""
with open(os.path.join(staging_dir, 'LEEME_INSTRUCCIONES.txt'), 'w', encoding='utf-8') as f:
    f.write(leeme)
print('6. Creado LEEME_INSTRUCCIONES.txt')

# 7. Comprimir con Rar.exe
rar_exe = r"C:\Program Files\WinRAR\Rar.exe"
target_rar_backend = os.path.join(base_dir, 'MercAPP_IS2_Windows.rar')
target_rar_deploy = os.path.abspath(os.path.join(base_dir, '..', 'MercAPP_Deploy', 'MercAPP_IS2_Windows.rar'))

if os.path.exists(target_rar_backend):
    os.remove(target_rar_backend)
if os.path.exists(target_rar_deploy):
    os.remove(target_rar_deploy)

print(f'7. Comprimiendo {staging_dir} con WinRAR...')
cmd = [rar_exe, 'a', '-r', '-ep1', '-m3', target_rar_backend, staging_dir]
subprocess.run(cmd, check=True)
print(f'-> Creado exitosamente: {target_rar_backend} ({os.path.getsize(target_rar_backend)} bytes)')

# Copiar a MercAPP_Deploy
shutil.copy2(target_rar_backend, target_rar_deploy)
print(f'-> Sincronizado en Deploy: {target_rar_deploy} ({os.path.getsize(target_rar_deploy)} bytes)')

# Limpieza
shutil.rmtree(staging_parent)
print('8. Limpieza de staging completada.')
