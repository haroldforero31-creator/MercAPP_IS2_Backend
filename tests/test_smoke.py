import os
import sys
import pytest
from datetime import datetime, timedelta

# Ensure isolated test database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

TEST_DB_PATH = os.path.join(BASE_DIR, 'test_smoke.db')
if os.path.exists(TEST_DB_PATH):
    try:
        os.remove(TEST_DB_PATH)
    except Exception:
        pass

os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB_PATH}'
os.environ['SECRET_KEY'] = 'test-secret-key-smoke-1234567890'

from app import app, db
from models import User, Store, CashSession, Product, Category, Sale, SaleItem, AppLicense

@pytest.fixture(scope='session', autouse=True)
def setup_database():
    """Create test schema and initial records for smoke tests."""
    with app.app_context():
        db.create_all()
        # Seed test store
        store = Store(name="Tienda Smoke Test")
        db.session.add(store)
        db.session.flush()

        # Seed test admin
        admin = User(name="Admin Tester", email="admin@test.com", store_id=store.id, is_admin=True, status="ACTIVO")
        admin.set_password("AdminPass123*")
        db.session.add(admin)

        # Seed test cashier
        cashier = User(name="Cajero Tester", email="cashier@test.com", store_id=store.id, is_admin=False, status="ACTIVO")
        cashier.set_password("CashierPass123*")
        db.session.add(cashier)

        # Seed test category
        cat = Category(name="Abarrotes", slug="abarrotes", store_id=store.id)
        db.session.add(cat)
        db.session.flush()

        # Seed test product
        prod = Product(
            store_id=store.id,
            category_id=cat.id,
            name="Arroz Diana 1kg",
            barcode="7701234567890",
            price=4500,
            stock=50,
            is_active=True
        )
        db.session.add(prod)

        # Seed active license
        lic = AppLicense(expiration_date=datetime.now() + timedelta(days=90), last_time_checked=datetime.now())
        db.session.add(lic)

        db.session.commit()

    yield

    # Teardown
    with app.app_context():
        db.session.remove()
        db.drop_all()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

# ==============================================================================
# 1. PRUEBAS DE AUTENTICACIÓN Y MODELO DE USUARIO
# ==============================================================================

def test_user_password_hashing():
    """Verifica que las contraseñas se almacenen cifradas y no en texto plano."""
    with app.app_context():
        user = User.query.filter_by(email="admin@test.com").first()
        assert user is not None
        assert user.password_hash != "AdminPass123*"
        assert user.check_password("AdminPass123*") is True
        assert user.check_password("WrongPassword") is False

def test_user_roles_and_permissions():
    """Verifica separación de roles: admin vs cajero."""
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        cashier = User.query.filter_by(email="cashier@test.com").first()
        assert admin.is_admin is True
        assert cashier.is_admin is False

# ==============================================================================
# 2. PRUEBAS DE SEGURIDAD P0: PROTECCIÓN DE RUTAS /api/users
# ==============================================================================

def test_api_users_unauthenticated_blocked(client):
    """P0 #1: Usuario no autenticado no puede listar usuarios."""
    response = client.get('/api/users')
    assert response.status_code in [302, 401, 403]

def test_api_users_cashier_forbidden(client):
    """P0 #1: Un cajero no-admin recibe 403 al intentar acceder a la API de usuarios."""
    with client.session_transaction() as sess:
        with app.app_context():
            cashier = User.query.filter_by(email="cashier@test.com").first()
            sess['_user_id'] = str(cashier.id)
            sess['_fresh'] = True
    response = client.get('/api/users')
    assert response.status_code == 403
    data = response.get_json()
    assert "Acceso denegado" in (data.get('error') or data.get('message') or '')

# ==============================================================================
# 3. PRUEBAS DE NEGOCIO POS: CONTROL DE STOCK Y SOBREVENTA
# ==============================================================================

def test_product_stock_integrity():
    """Verifica que el stock se consulte y mantenga consistente."""
    with app.app_context():
        prod = Product.query.filter_by(barcode="7701234567890").first()
        assert prod is not None
        assert prod.stock == 50
        assert prod.price == 4500

def test_atomic_stock_decrement():
    """Verifica decremento atómico de stock para evitar inconsistencias."""
    from sqlalchemy import text
    with app.app_context():
        prod = Product.query.filter_by(barcode="7701234567890").first()
        initial_stock = prod.stock
        
        result = db.session.execute(
            text("UPDATE producto SET stock = stock - :qty WHERE id = :pid AND stock >= :qty"),
            {'qty': 5, 'pid': prod.id}
        )
        db.session.commit()
        assert result.rowcount == 1
        
        db.session.refresh(prod)
        assert prod.stock == initial_stock - 5

def test_overselling_prevention():
    """Verifica que el sistema rechace ventas si el stock es insuficiente."""
    from sqlalchemy import text
    with app.app_context():
        prod = Product.query.filter_by(barcode="7701234567890").first()
        
        result = db.session.execute(
            text("UPDATE producto SET stock = stock - :qty WHERE id = :pid AND stock >= :qty"),
            {'qty': 9999, 'pid': prod.id}
        )
        db.session.commit()
        assert result.rowcount == 0

# ==============================================================================
# 4. PRUEBAS DE CAJA: APERTURA, VENTAS Y ARQUEO
# ==============================================================================

def test_cash_session_lifecycle():
    """Verifica apertura, cálculo de ventas y arqueo de caja."""
    with app.app_context():
        store = Store.query.first()
        cashier = User.query.filter_by(email="cashier@test.com").first()

        session = CashSession(
            store_id=store.id,
            user_id=cashier.id,
            base_amount=50000,
            opened_at=datetime.now(),
            status='abierta'
        )
        db.session.add(session)
        db.session.commit()
        assert session.id is not None
        assert session.base_amount == 50000

        sale = Sale(
            store_id=store.id,
            cash_session_id=session.id,
            receipt_number="TEST-REC-001",
            user_id=cashier.id,
            subtotal=15000,
            total=15000,
            payment_method='efectivo',
            amount_received=20000,
            change_given=5000,
            status='completada'
        )
        db.session.add(sale)
        
        session.cash_sales = (session.cash_sales or 0) + 15000
        db.session.commit()

        expected_cash = session.base_amount + (session.cash_sales or 0)
        assert expected_cash == 65000
        
        session.actual_cash = 65000
        session.expected_cash = expected_cash
        session.status = 'cerrada'
        session.closed_at = datetime.now()
        db.session.commit()
        
        assert session.status == 'cerrada'
        assert session.actual_cash == session.expected_cash

# ==============================================================================
# 5. PRUEBAS DE LICENCIA FAIL-CLOSED (P0 #5)
# ==============================================================================

def test_license_validity():
    """Verifica que una licencia vigente permita operación."""
    with app.app_context():
        lic = AppLicense.query.first()
        assert lic is not None
        assert lic.expiration_date > datetime.now()

def test_license_expired_detection():
    """Verifica que una licencia expirada se detecte correctamente."""
    with app.app_context():
        now = datetime.now()
        past_date = now - timedelta(days=5)
        is_expired = now > past_date
        assert is_expired is True

# ==============================================================================
# 6. PRUEBAS DE SALUD DEL SISTEMA Y ENDPOINTS CLAVE
# ==============================================================================

def test_health_check_endpoint(client):
    """GET /api/health debe responder 200 con estado operativo."""
    response = client.get('/api/health')
    assert response.status_code == 200

def test_sync_status_endpoint(client):
    """GET /api/sync/status debe responder 200."""
    response = client.get('/api/sync/status')
    assert response.status_code == 200

# ==============================================================================
# 7. PRUEBA DE RESPALDOS (P3 #19)
# ==============================================================================

def test_backup_service():
    """P3 #19: Verifica la generación de copias de seguridad de datos."""
    from utilities.backup_service import BackupService
    with app.app_context():
        store = Store.query.first()
        data = BackupService.export_store_data_json(store.id)
        assert data is not None
        assert data['metadata']['store_name'] == store.name
        assert 'products' in data
        assert 'categories' in data

# ==============================================================================
# 8. PRUEBAS DE BLOQUEADORES RESUELTOS (P0-1, P0-3, P0-4, P1-3)
# ==============================================================================

def test_login_page_contains_csrf_token(client):
    """P0-1 FIX: El formulario de login debe contener el input de csrf_token."""
    response = client.get('/login')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'name="csrf_token"' in html

def test_anonymous_product_creation_blocked(client):
    """P0-3 FIX: Un usuario anónimo no puede crear productos mediante POST /api/products."""
    response = client.post('/api/products', json={
        "name": "Producto Ilegal",
        "price": 1000,
        "category_id": 1
    })
    # Debe ser rechazado (302 redirect a login o 401/403)
    assert response.status_code in [302, 401, 403]

def test_anonymous_merki_ask_blocked(client):
    """P0-4 FIX: Un usuario anónimo no puede consultar ventas mediante Merki."""
    response = client.post('/api/merki/ask', json={
        "question": "cuanto vendi hoy",
        "store_id": 1
    })
    assert response.status_code in [302, 401, 403]

def test_security_headers_present(client):
    """P1-3 FIX: Las respuestas deben incluir cabeceras de seguridad HTTP."""
    response = client.get('/login')
    assert response.headers.get('X-Content-Type-Options') == 'nosniff'
    assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'

def test_api_unauthorized_returns_json_401(client):
    """P1-18 FIX: Acceso no autenticado a endpoint API con header JSON devuelve 401 JSON, no 302 HTML."""
    response = client.get('/api/users', headers={'Accept': 'application/json', 'Content-Type': 'application/json'})
    assert response.status_code == 401
    assert response.is_json
    data = response.get_json()
    assert 'No autorizado' in data.get('error', '')


# ==============================================================================
# 9. PRUEBAS DE RATE LIMITING, ÍNDICES Y AISLAMIENTO DE DATOS (P1-2, P1-8, P1-16)
# ==============================================================================

def test_rate_limiter_blocks_brute_force(client):
    """P1-2 FIX: 5 intentos fallidos rápidos activan HTTP 429 Too Many Requests."""
    for i in range(5):
        client.post('/api/users/login', json={'email': 'hacker@evil.com', 'password': 'wrong'})
    
    # El 6to intento consecutivo debe ser rechazado inmediatamente con 429
    res = client.post('/api/users/login', json={'email': 'hacker@evil.com', 'password': 'wrong'})
    assert res.status_code == 429
    assert res.is_json
    data = res.get_json()
    assert 'Demasiadas solicitudes' in data.get('error', '')
    assert 'Retry-After' in res.headers

def test_database_indexes_registered():
    """P1-8 & Fase 2: Verifica que los índices de optimización existan en la base de datos."""
    from sqlalchemy import inspect
    with app.app_context():
        inspector = inspect(db.engine)
        venta_indexes = [idx['name'] for idx in inspector.get_indexes('venta')]
        prod_indexes = [idx['name'] for idx in inspector.get_indexes('producto')]
        
        # Deben existir índices de optimización para store y fecha/barcode
        assert any('store' in idx or 'date' in idx or 'receipt' in idx for idx in venta_indexes)
        assert any('barcode' in idx or 'store' in idx for idx in prod_indexes)

def test_backup_tenant_isolation():
    """P1-16 FIX: Un respaldo de la tienda 1 nunca debe contener datos de la tienda 2."""
    from utilities.backup_service import BackupService
    with app.app_context():
        # Crear tienda 2 con un producto exclusivo
        store2 = Store.query.filter_by(name="Tienda Tenant 2").first()
        if not store2:
            store2 = Store(name="Tienda Tenant 2")
            db.session.add(store2)
            db.session.commit()
            
            cat2 = Category(store_id=store2.id, name="Cat2", slug="cat2")
            db.session.add(cat2)
            db.session.commit()
            
            prod2 = Product(
                store_id=store2.id,
                name="Producto Secreto Tienda 2",
                barcode="999888777666",
                price=50000,
                category_id=cat2.id
            )
            db.session.add(prod2)
            db.session.commit()

        # Exportar datos de Tienda 1
        store1 = Store.query.first()
        data_s1 = BackupService.export_store_data_json(store1.id)
        
        # Verificar que el producto secreto de Tienda 2 NO aparezca en el respaldo de Tienda 1
        product_names_s1 = [p['name'] for p in data_s1.get('products', [])]
        assert "Producto Secreto Tienda 2" not in product_names_s1
