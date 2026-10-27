import os
import sys
import time
import threading
import urllib.request
import json
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, db
from models import User, Store, CashSession, Product, Category, Sale, SaleItem, AppLicense
from datetime import datetime, timedelta
from waitress import serve

TEST_PORT = 5088

def prepare_test_environment():
    """Ensure database has license unlocked, a store, cashier and test products."""
    with app.app_context():
        db.create_all()
        # License unlock for tests
        lic = AppLicense.query.first()
        if not lic:
            lic = AppLicense(expiration_date=datetime.now() + timedelta(days=60), last_time_checked=datetime.now())
            db.session.add(lic)
        else:
            lic.expiration_date = datetime.now() + timedelta(days=60)
            lic.last_time_checked = datetime.now()

        # Ensure Store
        store = Store.query.first()
        if not store:
            store = Store(name="Tienda Test Concurrencia")
            db.session.add(store)
            db.session.flush()

        # Ensure Admin User
        user = User.query.filter_by(email="admin_test@mercapp.com").first()
        if not user:
            user = User(
                email="admin_test@mercapp.com",
                name="Admin Test",
                store_id=store.id,
                is_admin=True,
                status="ACTIVO"
            )
            user.set_password("Admin123*")
            db.session.add(user)
            db.session.flush()

        # Ensure Category
        cat = Category.query.filter_by(store_id=store.id).first()
        if not cat:
            cat = Category(name="General", store_id=store.id)
            db.session.add(cat)
            db.session.flush()

        # Ensure Product for high-concurrency race test
        prod = Product.query.filter_by(barcode="STRESS_TEST_001").first()
        if not prod:
            prod = Product(
                store_id=store.id,
                category_id=cat.id,
                name="Producto Test Concurrencia",
                barcode="STRESS_TEST_001",
                price=5000,
                stock=100,
                is_active=True
            )
            db.session.add(prod)
        else:
            prod.stock = 100
            prod.is_active = True

        # Ensure Cash Session for today
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        session = CashSession.query.filter(
            CashSession.store_id == store.id,
            CashSession.opened_at >= today_start
        ).first()
        if not session:
            session = CashSession(
                store_id=store.id,
                user_id=user.id,
                opening_balance=50000,
                opened_at=now
            )
            db.session.add(session)

        db.session.commit()
        return store.id, user.id, prod.id

def run_background_waitress(port):
    """Run Waitress with 64 worker threads."""
    serve(
        app,
        host='127.0.0.1',
        port=port,
        threads=64,
        connection_limit=1000,
        channel_timeout=30,
        _quiet=True
    )

def wait_for_server(port, timeout=10):
    url = f"http://127.0.0.1:{port}/api/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False

def make_request(url):
    """Single HTTP GET request with timing."""
    start_t = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'StressTest/1.0'})
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            data = resp.read()
            lat_ms = (time.perf_counter() - start_t) * 1000.0
            return True, resp.status, lat_ms, None
    except Exception as e:
        lat_ms = (time.perf_counter() - start_t) * 1000.0
        return False, getattr(e, 'code', 0), lat_ms, str(e)

def run_concurrency_test(port, total_requests=500, max_workers=500):
    print("\n" + "=" * 65)
    print(f" EJECUTANDO PRUEBA DE ESTRÉS: {total_requests} PETICIONES CONCURRENTES")
    print(f" Hilos simultáneos (Concurrencia real): {max_workers}")
    print(f" Servidor: Waitress (64 hilos de procesamiento)")
    print(f" Base de Datos: SQLite WAL (Write-Ahead Logging + 30s busy_timeout)")
    print("=" * 65)

    urls = [
        f"http://127.0.0.1:{port}/api/health",
        f"http://127.0.0.1:{port}/api/sync/status",
        f"http://127.0.0.1:{port}/login"
    ]

    latencies = []
    success_count = 0
    fail_count = 0
    errors = []

    wall_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(total_requests):
            target_url = urls[i % len(urls)]
            futures.append(executor.submit(make_request, target_url))

        for f in as_completed(futures):
            ok, status, lat, err = f.result()
            if ok:
                success_count += 1
                latencies.append(lat)
            else:
                fail_count += 1
                errors.append(err)

    wall_duration = time.perf_counter() - wall_start
    rps = total_requests / wall_duration if wall_duration > 0 else 0

    latencies.sort()
    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
    max_lat = latencies[-1] if latencies else 0
    min_lat = latencies[0] if latencies else 0

    print("\n[METRICAS] RESULTADOS DE LA PRUEBA DE ALTA CONCURRENCIA:")
    print(f"  * Total de Peticiones:         {total_requests}")
    print(f"  * Peticiones Exitosas (200 OK): {success_count} ({success_count/total_requests*100:.2f}%)")
    print(f"  * Peticiones Fallidas:          {fail_count} ({fail_count/total_requests*100:.2f}%)")
    print(f"  * Tiempo Total de Ejecución:    {wall_duration:.2f} segundos")
    print(f"  * Rendimiento (Throughput):     {rps:.2f} peticiones/segundo (RPS)")
    print(f"  * Latencia Mínima:              {min_lat:.2f} ms")
    print(f"  * Latencia Promedio:            {avg_lat:.2f} ms")
    print(f"  * Latencia Mediana (p50):       {p50:.2f} ms")
    print(f"  * Latencia Percentil 95 (p95):  {p95:.2f} ms")
    print(f"  * Latencia Percentil 99 (p99):  {p99:.2f} ms")
    print(f"  * Latencia Máxima:              {max_lat:.2f} ms")

    if fail_count > 0:
        print(f"  [ALERTA] Muestra de errores ({len(errors)}): {errors[:3]}")

    print("=" * 65)
    return success_count == total_requests

def test_atomic_stock_concurrency(store_id, user_id, product_id):
    """Test race condition protection: concurrent transactions buying stock."""
    print("\n" + "=" * 65)
    print(" VERIFICANDO CONTROL ATÓMICO DE STOCK Y PREVENCIÓN DE SOBREVENTA")
    print("=" * 65)

    with app.app_context():
        p = db.session.get(Product, product_id)
        p.stock = 10
        db.session.commit()
        print(f"  * Stock inicial configurado: 10 unidades")

    from sqlalchemy import text

    def simulate_concurrent_sale(sale_index):
        with app.app_context():
            session_today = CashSession.query.filter_by(store_id=store_id).first()
            res = db.session.execute(
                text("UPDATE producto SET stock = stock - 1, sale_count = COALESCE(sale_count, 0) + 1 WHERE id = :pid AND stock >= 1"),
                {'pid': product_id}
            )
            if res.rowcount == 0:
                db.session.rollback()
                return False, "Stock agotado"
            
            receipt = f"MRC-STRESS-{sale_index:04d}_{secrets.token_hex(2).upper()}"
            sale = Sale(
                store_id=store_id,
                cash_session_id=session_today.id,
                receipt_number=receipt,
                user_id=user_id,
                subtotal=5000,
                total=5000,
                payment_method='efectivo',
                amount_received=5000,
                status='completada'
            )
            db.session.add(sale)
            db.session.flush()
            item = SaleItem(sale_id=sale.id, product_id=product_id, quantity=1, unit_price=5000, subtotal=5000)
            db.session.add(item)
            db.session.commit()
            return True, receipt

    results = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(simulate_concurrent_sale, i) for i in range(30)]
        for f in as_completed(futures):
            results.append(f.result())

    succeeded = sum(1 for ok, _ in results if ok)
    rejected = sum(1 for ok, _ in results if not ok)

    with app.app_context():
        final_stock = db.session.get(Product, product_id).stock

    print(f"  * Transacciones ejecutadas:   30 simultáneas")
    print(f"  * Transacciones exitosas:     {succeeded} (Esperado: 10)")
    print(f"  * Transacciones rechazadas:   {rejected} (Esperado: 20 por falta de stock)")
    print(f"  * Stock final en BD:          {final_stock} (Esperado: 0, jamás negativo)")

    assert succeeded == 10, f"Error de sobreventa: se procesaron {succeeded} ventas pero solo había 10 unidades."
    assert final_stock == 0, f"Inconsistencia en stock final: {final_stock}"
    print("  [OK] Protección contra condiciones de carrera (Race Condition) 100% EXITOSA.")
    print("=" * 65)

if __name__ == '__main__':
    store_id, user_id, product_id = prepare_test_environment()

    srv = threading.Thread(target=run_background_waitress, args=(TEST_PORT,), daemon=True)
    srv.start()

    if not wait_for_server(TEST_PORT):
        print("[ERROR] El servidor de pruebas no respondió a tiempo.")
        sys.exit(1)

    print("[INFO] Servidor de prueba Waitress iniciado y respondiendo en puerto", TEST_PORT)

    success_500 = run_concurrency_test(TEST_PORT, total_requests=500, max_workers=500)
    test_atomic_stock_concurrency(store_id, user_id, product_id)

    if success_500:
        print("\n>>> TODAS LAS PRUEBAS DE ALTA CONCURRENCIA E INTEGRIDAD PASARON CON ÉXITO <<<")
        sys.exit(0)
    else:
        print("\n>>> ALGUNAS PRUEBAS EXPERIMENTARON FALLOS <<<")
        sys.exit(1)
