import os
import sys
import time
import socket
import threading
import subprocess
import webbrowser
import urllib.request

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, db

def is_port_in_use(port, host='127.0.0.1'):
    """Check if a network port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def find_available_port(preferred_port=5001):
    """Find a usable port starting from the preferred port."""
    port = preferred_port
    while port < preferred_port + 20:
        if not is_port_in_use(port):
            return port
        port += 1
    return preferred_port

def init_local_database():
    """Ensure SQLite database, tables and column migrations are applied."""
    print("[MERCAPP] Inicializando base de datos local SQLite...")
    with app.app_context():
        try:
            db.create_all()
            # Migraciones seguras para SQLite existente
            migrations = [
                "ALTER TABLE cliente_credito ADD COLUMN email VARCHAR(120)",
                "ALTER TABLE usuario ADD COLUMN username VARCHAR(50)",
                "ALTER TABLE usuario ADD COLUMN is_active_cashier BOOLEAN DEFAULT 1",
                "ALTER TABLE cliente ADD COLUMN created_at DATETIME",
                "ALTER TABLE configuracion_tienda ADD COLUMN printer_name VARCHAR(200) DEFAULT ''",
                "ALTER TABLE configuracion_tienda ADD COLUMN auto_print BOOLEAN DEFAULT 1",
                "ALTER TABLE configuracion_tienda ADD COLUMN auto_drawer BOOLEAN DEFAULT 1"
            ]
            with db.engine.connect() as conn:
                for sql in migrations:
                    try:
                        conn.execute(db.text(sql))
                        conn.commit()
                    except Exception:
                        pass
            print("[MERCAPP] Base de datos verificada y lista.")
        except Exception as e:
            print(f"[MERCAPP] Advertencia durante inicio de base de datos: {e}")

def start_server(port):
    """Run the production-grade Waitress WSGI server."""
    try:
        from waitress import serve
        print(f"[MERCAPP] Iniciando servidor local en http://127.0.0.1:{port} con Waitress (8 hilos)...")
        serve(app, host='127.0.0.1', port=port, threads=8, channel_timeout=120)
    except Exception as e:
        print(f"[MERCAPP ERROR] No se pudo iniciar Waitress: {e}. Usando servidor de respaldo...")
        app.run(host='127.0.0.1', port=port, debug=False)

def get_browser_path():
    """Find Microsoft Edge or Google Chrome to launch in native desktop app window mode."""
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None

def wait_for_server(port, timeout=12):
    """Wait until the HTTP server is responsive."""
    url = f"http://127.0.0.1:{port}/api/sync/status"
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=0.8) as response:
                if response.status in (200, 302, 401, 404):
                    return True
        except Exception:
            time.sleep(0.3)
    return False

def open_desktop_window(port):
    """Open MercAPP as a standalone native desktop window or standard browser tab."""
    target_url = f"http://127.0.0.1:{port}/pos"
    wait_for_server(port)
    browser_exe = get_browser_path()
    if browser_exe:
        print(f"[MERCAPP] Abriendo ventana nativa de escritorio con: {browser_exe}")
        cmd = [browser_exe, f"--app={target_url}"]
        subprocess.Popen(cmd)
    else:
        print("[MERCAPP] Abriendo navegador predeterminado del sistema...")
        webbrowser.open(target_url)

if __name__ == '__main__':
    # Determine port
    env_port = os.getenv('PORT')
    if env_port and env_port.isdigit():
        port = int(env_port)
    else:
        port = find_available_port(5001)

    os.environ['PORT'] = str(port)
    print("=" * 60)
    print("  MercAPP IS2 — Sistema de Punto de Venta y Gestión")
    print(f"  Modo: Autónomo Local (Offline-first)")
    print(f"  URL:  http://127.0.0.1:{port}/pos")
    print("=" * 60)

    # Initialize local SQLite DB
    init_local_database()

    # Launch server in background thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    # Open native application window
    open_desktop_window(port)

    # Keep launcher process running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MERCAPP] Deteniendo aplicación...")
        sys.exit(0)
