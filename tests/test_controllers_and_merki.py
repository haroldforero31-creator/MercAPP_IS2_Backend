# -*- coding: utf-8 -*-
"""
Pruebas para Controladores, Merki IA, Reportes y Helpers
=========================================================
Eleva la cobertura global del backend a más del 70%.
"""
import pytest
from datetime import datetime
from app import app, db
from models import Store, User, Category, Product, CashSession, Sale
from utilities.helpers import round_to_50, format_weight, generate_verification_code, validate_payment
from services.merki_queries import MerkiQueries
from services.merki_service import MerkiService


def test_helpers_round_and_format():
    assert round_to_50(123) == 100
    assert round_to_50(135) == 150
    assert round_to_50(175) == 200

    assert format_weight(1500, 'kg') == "1.500 kg"
    assert "kg" in format_weight(500, 'kg')
    assert format_weight(None) == "0 kg"

    code = generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()


def test_helpers_validate_payment():
    # Efectivo valido
    errors, details = validate_payment('efectivo', 10000, amount_received=15000)
    assert len(errors) == 0
    assert details['change_given'] == 5000

    # Efectivo insuficiente
    errors, details = validate_payment('efectivo', 10000, amount_received=5000)
    assert len(errors) > 0

    # Tarjeta valida
    errors, details = validate_payment('tarjeta', 10000, card_last4='1234')
    assert len(errors) == 0

    # Metodo invalido
    errors, details = validate_payment('cripto', 10000)
    assert len(errors) > 0


def test_merki_queries_functions():
    with app.app_context():
        store = Store.query.first()
        sid = store.id if store else 1

        s_today = MerkiQueries.sales_today(sid)
        assert s_today is not None

        s_wk = MerkiQueries.sales_week(sid)
        assert s_wk is not None

        s_m = MerkiQueries.sales_month(sid)
        assert s_m is not None

        debt = MerkiQueries.total_debt(sid)
        assert debt is not None

        low = MerkiQueries.low_stock(sid)
        assert low is not None

        out = MerkiQueries.out_of_stock(sid)
        assert out is not None

        act = MerkiQueries.active_session(sid)
        assert act is not None

        tot_p = MerkiQueries.total_products(sid)
        assert tot_p is not None

        cats = MerkiQueries.list_categories(sid)
        assert cats is not None

        MerkiQueries.cheapest_product(sid)
        MerkiQueries.most_expensive_product(sid)
        MerkiQueries.best_seller(sid)
        MerkiQueries.who_owes_most(sid)
        MerkiQueries.sales_count_today(sid)
        MerkiQueries.debt_client_count(sid)
        MerkiQueries.search_by_code(sid, "123456")
        MerkiQueries.last_sale(sid)


def test_merki_service_nlp():
    with app.app_context():
        store = Store.query.first()
        sid = store.id if store else 1

        resp1 = MerkiService.process_question(sid, "cuanto vendi hoy")
        assert resp1 is not None

        resp2 = MerkiService.process_question(sid, "como esta la caja")
        assert resp2 is not None

        resp3 = MerkiService.process_question(sid, "productos por agotarse")
        assert resp3 is not None

        resp4 = MerkiService.process_question(sid, "quien me debe dinero")
        assert resp4 is not None

        resp5 = MerkiService.process_question(sid, "hola buenos dias")
        assert resp5 is not None

        resp6 = MerkiService.process_question(sid, "cuanto vendi esta semana")
        assert resp6 is not None

        resp7 = MerkiService.process_question(sid, "cuanto vendi este mes")
        assert resp7 is not None

        resp8 = MerkiService.process_question(sid, "que metodos de pago usaron")
        assert resp8 is not None

        resp9 = MerkiService.process_question(sid, "cual es el valor del inventario")
        assert resp9 is not None

        resp10 = MerkiService.process_question(sid, "cuales son los productos mas vendidos")
        assert resp10 is not None

        sugg = MerkiService.get_dynamic_suggestions(sid)
        assert isinstance(sugg, list)


def test_controllers_and_reports_with_admin():
    orig_csrf = app.config.get('WTF_CSRF_ENABLED', True)
    app.config['WTF_CSRF_ENABLED'] = False
    try:
        with app.app_context():
            import jwt as pyjwt
            admin = User.query.filter_by(is_admin=True, status="ACTIVO").first()
            if not admin:
                store = Store.query.first()
                if not store:
                    store = Store(name="Test Store")
                    db.session.add(store)
                    db.session.flush()
                admin = User(name="Admin Ctrl", email="admin_ctrl@test.com", is_admin=True, status="ACTIVO", store_id=store.id)
                admin.set_password("AdminPass123*")
                db.session.add(admin)
                db.session.commit()
            token = pyjwt.encode({'user_id': admin.id, 'email': admin.email}, app.config['SECRET_KEY'], algorithm='HS256')
            headers = {'Authorization': f'Bearer {token}'}

            # Ensure category exists for admin's store
            cat = Category.query.filter_by(store_id=admin.store_id).first()
            if not cat:
                cat = Category(name="General", slug="general", store_id=admin.store_id)
                db.session.add(cat)
                db.session.commit()

            with app.test_client() as c:
                # 1. Product controller endpoints
                prods_res = c.get(f'/api/products?store_id={admin.store_id}', headers=headers)
                assert prods_res.status_code == 200

                # Create product via controller
                new_prod = c.post('/api/products', json={
                    "name": f"Prod Controller {int(datetime.now().timestamp())}",
                    "price": 2500,
                    "category_id": cat.id,
                    "stock": 10
                }, headers=headers)
                assert new_prod.status_code in [201, 200]
                prod_id = new_prod.get_json()["data"]["id"]

                # Detail product
                detail = c.get(f'/api/products/{prod_id}', headers=headers)
                assert detail.status_code == 200

                # Update product
                upd = c.put(f'/api/products/{prod_id}', json={"price": 3000}, headers=headers)
                assert upd.status_code == 200

                # Delete product
                del_res = c.delete(f'/api/products/{prod_id}', headers=headers)
                assert del_res.status_code == 200

                # 2. User controller endpoints
                new_u = c.post('/api/users', json={
                    "name": "User Controller Test",
                    "email": f"u_ctrl_{int(datetime.now().timestamp())}@test.com",
                    "password": "Password123!",
                    "is_admin": False
                }, headers=headers)
                assert new_u.status_code == 201
                u_id = new_u.get_json()["data"]["id"]

                u_detail = c.get(f'/api/users/{u_id}', headers=headers)
                assert u_detail.status_code == 200

                u_del = c.delete(f'/api/users/{u_id}', headers=headers)
                assert u_del.status_code == 200

                # 3. Merki controller suggestions
                sugg_res = c.get(f'/api/merki/suggestions?store_id={admin.store_id}', headers=headers)
                assert sugg_res.status_code == 200

                # 4. Sale controller session check
                open_res = c.post('/api/sessions/open', json={'base_amount': 50000}, headers=headers)
                assert open_res.status_code in [201, 400]

                sess_res = c.get('/api/sessions/today', headers=headers)
                assert sess_res.status_code in [200, 404]

                close_res = c.post('/api/sessions/99999/close', json={'actual_cash': 50000}, headers=headers)
                assert close_res.status_code in [200, 400, 404]

                # 5. Backup service JSON export
                from utilities.backup_service import BackupService
                exp = BackupService.export_store_data_json(admin.store_id)
                assert "metadata" in exp

                # 6. Excel Reports routes (Criterio F)
                rep_sales = c.get('/api/reports/sales', headers=headers)
                assert rep_sales.status_code == 200
                assert rep_sales.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

                rep_inv = c.get('/api/reports/inventory', headers=headers)
                assert rep_inv.status_code == 200
                assert rep_inv.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    finally:
        app.config['WTF_CSRF_ENABLED'] = orig_csrf
