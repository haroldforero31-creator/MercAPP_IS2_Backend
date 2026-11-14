import pytest
from app import app, db
from models.user import Store, User, StoreSettings
from models.supplier import Supplier, SupplierDelivery
from models.sale import Order, CashSession
from werkzeug.security import generate_password_hash
from datetime import datetime

@pytest.fixture
def test_setup():
    with app.app_context():
        store = Store.query.get(1)
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

        # Supplier
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


def test_supplier_order_creation_and_admin_confirmation(test_setup):
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
