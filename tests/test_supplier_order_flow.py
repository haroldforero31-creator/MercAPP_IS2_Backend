import pytest
from app import app, db
from models.user import Store, User, StoreSettings
from models.supplier import Supplier, SupplierDelivery, SupplierEmailVerification
from models.sale import Order, CashSession
from werkzeug.security import generate_password_hash
from datetime import datetime

@pytest.fixture
def test_setup():
    with app.app_context():
        store = db.session.get(Store, 1)
        if not store:
            store = Store(id=1, name="MercAPP Supermercado Central", is_active=True)
            db.session.add(store)
            db.session.commit()

        st_set = StoreSettings.query.filter_by(store_id=1).first()
        if not st_set:
            st_set = StoreSettings(store_id=1, store_name="MercAPP Central")
            db.session.add(st_set)
            db.session.commit()

        admin = User.query.filter_by(email="admin_flujo@test.com").first()
        if not admin:
            admin = User(
                name="Admin Flujo",
                email="admin_flujo@test.com",
                password_hash=generate_password_hash("Admin1234!"),
                is_admin=True,
                status="ACTIVO",
                store_id=1
            )
            db.session.add(admin)
            db.session.commit()

        # Open Cash Session
        session_obj = CashSession.query.filter_by(store_id=1, status='abierta').first()
        if not session_obj:
            session_obj = CashSession(
                store_id=1,
                user_id=admin.id,
                base_amount=100000,
                status='abierta',
                opened_at=datetime.now()
            )
            db.session.add(session_obj)
            db.session.commit()

        # Supplier for direct order test
        supplier_email = "proveedor_flujo@lacteos.com"
        supplier = Supplier.query.filter_by(email=supplier_email).first()
        if not supplier:
            supplier = Supplier(
                company_name="Lácteos del Valle SAS",
                contact_name="Andrés Gómez",
                email=supplier_email,
                phone="3109876543",
                password_hash=generate_password_hash("ClaveProv123!"),
                status='ACTIVO'
            )
            db.session.add(supplier)
            db.session.commit()

        return {
            'store_id': 1,
            'admin_id': admin.id,
            'supplier_id': supplier.id,
            'supplier_get_id': supplier.get_id()
        }


def test_supplier_registration_and_email_verification():
    """Test full supplier registration, 6-digit code generation and email verification."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    test_email = "nuevo_proveedor_test@distribuidor.com"
    with app.test_client() as client:
        # Clean previous if exists
        with app.app_context():
            Supplier.query.filter_by(email=test_email).delete()
            SupplierEmailVerification.query.filter_by(email=test_email).delete()
            db.session.commit()

        # 1. Register supplier
        reg_data = {
            'company_name': 'Distribuidora Mayorista ABC',
            'contact_name': 'Mauricio Rojas',
            'phone': '3151234567',
            'email': test_email,
            'password': 'Password123!'
        }
        res_reg = client.post('/proveedor/registro', data=reg_data, follow_redirects=True)
        assert res_reg.status_code == 200

        # Verify in DB that verification record was created with 6-digit code
        with app.app_context():
            verif = SupplierEmailVerification.query.filter_by(email=test_email, verified=False).first()
            assert verif is not None
            assert len(verif.code) == 6
            assert verif.code.isdigit()
            saved_code = verif.code

        # 2. Submit verification code
        res_code = client.post('/proveedor/verificar-email', data={'code': saved_code}, follow_redirects=True)
        assert res_code.status_code == 200
        assert b"Distribuidora Mayorista ABC" in res_code.data or b"Tiendas Disponibles" in res_code.data

        # 3. Verify in DB that Supplier is now ACTIVO
        with app.app_context():
            new_sup = Supplier.query.filter_by(email=test_email).first()
            assert new_sup is not None
            assert new_sup.status == 'ACTIVO'
            assert new_sup.check_password('Password123!') is True


def test_supplier_login_and_logout():
    """Test supplier manual login with credentials and session persistence."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    supplier_email = "proveedor_login_test@carnicos.com"
    with app.app_context():
        sup = Supplier.query.filter_by(email=supplier_email).first()
        if not sup:
            sup = Supplier(
                company_name="Cárnicos la Granja",
                contact_name="Pedro Martínez",
                phone="3209871234",
                email=supplier_email,
                password_hash=generate_password_hash("Carnes2026!"),
                status='ACTIVO'
            )
            db.session.add(sup)
            db.session.commit()

    with app.test_client() as client:
        # Invalid password
        bad_login = client.post('/proveedor/login', data={'email': supplier_email, 'password': 'WrongPassword'}, follow_redirects=True)
        assert bad_login.status_code == 200
        assert b"incorrectas" in bad_login.data

        # Valid login
        good_login = client.post('/proveedor/login', data={'email': supplier_email, 'password': 'Carnes2026!'}, follow_redirects=True)
        assert good_login.status_code == 200
        assert b"C\xc3\xa1rnicos la Granja" in good_login.data or b"Tiendas" in good_login.data

        # Logout
        logout_resp = client.get('/proveedor/logout', follow_redirects=True)
        assert logout_resp.status_code == 200


def test_supplier_order_creation_and_admin_confirmation(test_setup):
    """Test supplier submitting order and admin confirming with mixed cash/transfer."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    store_id = test_setup['store_id']
    admin_id = test_setup['admin_id']
    supplier_get_id = test_setup['supplier_get_id']

    # 1. Supplier places order
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = supplier_get_id
            sess['_fresh'] = True

        order_data = {
            'delivery_date': '2026-11-14',
            'total_amount': '150000',
            'notes': 'Despacho de 30 paquetes de yogurt. 2 unidades averiadas.'
        }
        resp = client.post(f'/proveedor/tienda/{store_id}/entrega', data=order_data, follow_redirects=True)
        assert resp.status_code == 200

    # 2. Verify in DB
    with app.app_context():
        order = Order.query.filter_by(store_id=store_id, order_type='proveedor', status='pendiente').first()
        assert order is not None
        assert order.customer_name == "Lácteos del Valle SAS"
        assert order.total == 150000
        assert "averiadas" in order.notes
        order_id = order.id

        deliv = SupplierDelivery.query.filter_by(order_number=f"ORD-{order_id}").first()
        assert deliv is not None
        assert deliv.is_confirmed is False

    # 3. Admin confirms and pays supplier (Mixto: 100,000 cash, 50,000 transfer)
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_id)
            sess['_fresh'] = True

        orders_page = client.get('/orders')
        assert orders_page.status_code == 200
        assert b"PEDIDO PROVEEDOR" in orders_page.data

        pay_resp = client.post(f'/api/order/{order_id}/confirm_supplier_payment', json={
            'payment_method': 'mixto',
            'total_paid': 150000,
            'amount_cash': 100000,
            'amount_transfer': 50000
        })
        assert pay_resp.status_code == 200
        assert pay_resp.get_json()['success'] is True

    # 4. Check DB updates
    with app.app_context():
        updated_order = db.session.get(Order, order_id)
        assert updated_order.status == 'completado'
        assert updated_order.payment_method == 'mixto'

        updated_delivery = SupplierDelivery.query.filter_by(order_number=f"ORD-{order_id}").first()
        assert updated_delivery.is_confirmed is True
        assert updated_delivery.amount_cash == 100000
        assert updated_delivery.amount_transfer == 50000
        assert updated_delivery.cash_session_id is not None


def test_supplier_ui_isolation_and_no_admin_navbar(test_setup):
    """Test supplier UI has NO admin navbar (no Caja, Ventas, Deudas) and NO demo bypass."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    supplier_get_id = test_setup['supplier_get_id']

    with app.test_client() as client:
        # 1. Login page: ensure no demo bypass
        login_res = client.get('/proveedor/login')
        assert login_res.status_code == 200
        assert b"Acceso R\xc3\xa1pido Demo" not in login_res.data
        assert b"Rellenar Datos de Prueba" not in login_res.data
        assert b"autoFillDemoSupplier" not in login_res.data

        # 2. Authenticated supplier visits stores list
        with client.session_transaction() as sess:
            sess['_user_id'] = supplier_get_id
            sess['_fresh'] = True

        tiendas_res = client.get('/proveedor/tiendas')
        assert tiendas_res.status_code == 200
        # Assert NO admin navigation items
        assert b'class="navbar"' not in tiendas_res.data
        assert b'<a href="/pos"' not in tiendas_res.data
        assert b'<span class="nav-text">Caja</span>' not in tiendas_res.data
        assert b'<span class="nav-text">Ventas</span>' not in tiendas_res.data
        assert b'<span class="nav-text">Deudas</span>' not in tiendas_res.data
        assert b'<span class="nav-text">Historial</span>' not in tiendas_res.data
        # Assert supplier header is present
        assert b"Tiendas Disponibles" in tiendas_res.data
        assert b"Proveedor:" in tiendas_res.data

        # 3. Authenticated supplier visits delivery page
        entrega_res = client.get('/proveedor/tienda/1/entrega')
        assert entrega_res.status_code == 200
        assert b'class="navbar"' not in entrega_res.data
        assert b'<span class="nav-text">Caja</span>' not in entrega_res.data
        assert b"Solicitud de Pedido / Despacho" in entrega_res.data
        assert b"Fecha de Pedido" in entrega_res.data
        assert b"Costo del Pedido" in entrega_res.data

        # 4. Supplier logout via standard /logout or /proveedor/logout doesn't throw 500
        logout_std = client.get('/logout', follow_redirects=True)
        assert logout_std.status_code == 200
