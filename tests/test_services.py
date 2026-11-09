# -*- coding: utf-8 -*-
"""
Pruebas Unitarias para Capa de Servicios, DTOs, Utilidades y JWT
================================================================
Asegura cobertura >= 70% para el backend según Criterio G de Sustentación.
"""
import pytest
from datetime import datetime
from app import app, db
from models import Store, User, Category, Product, CashSession, Sale
from dtos.user_dto import UserCreateDTO, UserUpdateDTO, UserLoginDTO
from dtos.product_dto import ProductCreateDTO, ProductUpdateDTO
from services.user_service import UserService
from services.product_service import ProductService
from services.sale_service import SaleService
from utilities.security import hash_password, verify_password
from utilities.response_helper import success_response, error_response
from utilities.report_generator import generate_sales_report_excel, generate_inventory_report_excel



@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as c:
        yield c

@pytest.fixture
def test_app_ctx():
    with app.app_context():
        store = Store.query.filter_by(name="Tienda Test Services").first()
        if not store:
            store = Store(name="Tienda Test Services")
            db.session.add(store)
            db.session.commit()

        cat = Category.query.filter_by(store_id=store.id, slug="serv-cat").first()
        if not cat:
            cat = Category(store_id=store.id, name="Servicios Categoria", slug="serv-cat")
            db.session.add(cat)
            db.session.commit()

        yield {"store": store, "category": cat}


def test_security_helpers():
    pwd = "MiSuperPassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_pwd", hashed) is False


def test_response_helpers():
    with app.test_request_context():
        resp, code = success_response(data={"item": 1}, message="OK", status_code=200)
        assert code == 200
        json_data = resp.get_json()
        assert json_data["success"] is True
        assert json_data["data"]["item"] == 1

        err_resp, err_code = error_response(message="Error grave", errors=["Campo invalido"], status_code=400)
        assert err_code == 400
        err_json = err_resp.get_json()
        assert err_json["success"] is False
        assert "Campo invalido" in err_json["details"]


def test_user_service_full_lifecycle(test_app_ctx):
    store = test_app_ctx["store"]
    email = f"service_user_{int(datetime.now().timestamp())}@test.com"

    # 1. Validation error
    invalid_dto = UserCreateDTO(name="", email="notanemail", password="123")
    user_res, err = UserService.create_user(invalid_dto)
    assert user_res is None
    assert err is not None

    # 2. Valid creation
    dto = UserCreateDTO(name="Usuario Servicio", email=email, password="Password123!", is_admin=False, store_id=store.id)
    user_res, err = UserService.create_user(dto)
    assert err is None
    assert user_res["email"] == email
    user_id = user_res["id"]

    # 3. Duplicate email error
    dup_res, dup_err = UserService.create_user(dto)
    assert dup_res is None
    assert "ya se encuentra registrado" in dup_err

    # 4. Get by ID and Get All
    found_user, err = UserService.get_user_by_id(user_id)
    assert err is None
    assert found_user["name"] == "Usuario Servicio"

    not_found, err = UserService.get_user_by_id(999999)
    assert not_found is None
    assert err is not None

    all_users = UserService.get_all_users(store.id)
    assert len(all_users) >= 1

    # 5. Authentication
    login_dto = UserLoginDTO(email=email, password="Password123!")
    auth_user, err = UserService.authenticate(login_dto)
    assert err is None
    assert auth_user["id"] == user_id

    # Wrong password
    bad_login = UserLoginDTO(email=email, password="WrongPassword")
    bad_auth, err = UserService.authenticate(bad_login)
    assert bad_auth is None
    assert "incorrectas" in err

    # 6. Update user
    update_dto = UserUpdateDTO(name="Usuario Renombrado")
    updated, err = UserService.update_user(user_id, update_dto)
    assert err is None
    assert updated["name"] == "Usuario Renombrado"

    # 7. Delete user
    deleted, err = UserService.delete_user(user_id)
    assert deleted is True
    assert err is None


def test_product_service_full_lifecycle(test_app_ctx):
    store = test_app_ctx["store"]
    cat = test_app_ctx["category"]
    barcode = f"BAR_{int(datetime.now().timestamp())}"

    # 1. Validation error
    bad_dto = ProductCreateDTO(name="", price=-50, category_id=cat.id)
    res, err = ProductService.create_product(bad_dto)
    assert res is None
    assert err is not None

    # 2. Valid creation
    dto = ProductCreateDTO(
        name="Arroz Test Service",
        price=4500,
        category_id=cat.id,
        store_id=store.id,
        barcode=barcode,
        stock=100
    )
    prod_res, err = ProductService.create_product(dto)
    assert err is None
    assert prod_res["name"] == "Arroz Test Service"
    prod_id = prod_res["id"]

    # 3. Get by ID
    found, err = ProductService.get_product_by_id(prod_id)
    assert err is None
    assert found["price"] == 4500

    # 4. Search products
    results = ProductService.search_products("Arroz Test", store_id=store.id)
    assert len(results) >= 1
    assert any(p["id"] == prod_id for p in results)

    # Search by barcode
    bar_results = ProductService.search_products(barcode, store_id=store.id)
    assert len(bar_results) >= 1

    # 5. Get all products and categories
    all_prods = ProductService.get_all_products(store_id=store.id)
    assert len(all_prods) >= 1

    cats = ProductService.get_categories(store_id=store.id)
    assert len(cats) >= 1

    # 6. Update product
    update_dto = ProductUpdateDTO(name="Arroz Test Actualizado", price=4800, stock=80)
    updated, err = ProductService.update_product(prod_id, update_dto, store_id=store.id)
    assert err is None
    assert updated["price"] == 4800

    # 7. Delete product (soft delete)
    deleted, err = ProductService.delete_product(prod_id)
    assert deleted is True
    assert err is None


def test_sale_service_lifecycle():
    with app.app_context():
        ts = int(datetime.now().timestamp())
        fresh_store = Store(name=f"Store Sale Test {ts}")
        db.session.add(fresh_store)
        db.session.flush()

        fresh_user = User(
            store_id=fresh_store.id,
            name="Cashier Sale Test",
            email=f"cashier_sale_{ts}@test.com",
            password_hash=hash_password("123"),
            status="ACTIVO"
        )
        db.session.add(fresh_user)
        db.session.commit()

        # Open session
        session, err = SaleService.open_session(store_id=fresh_store.id, user_id=fresh_user.id, base_amount=100000)
        assert err is None
        assert session is not None
        assert session.status == "abierta"
        session_id = session.id

        # Check today session
        active = SaleService.get_today_session(store_id=fresh_store.id)
        assert active is not None
        assert active.id == session_id

        # Close session
        closed, err = SaleService.close_session(session_id=session_id, actual_cash=100000)
        assert err is None
        assert closed.status == "cerrada"


def test_report_generators():
    sales = [
        {"receipt_number": "R-001", "date": "09/11/2026 10:00", "cashier": "Ana", "payment_method": "efectivo", "subtotal": 15000, "total": 15000, "status": "completada"},
        {"receipt_number": "R-002", "date": "09/11/2026 10:30", "cashier": "Ana", "payment_method": "tarjeta", "subtotal": 30000, "total": 30000, "status": "completada"}
    ]
    excel_sales = generate_sales_report_excel(sales, "Tienda Prueba", "Hoy")
    assert excel_sales is not None
    assert len(excel_sales.getvalue()) > 1000

    products = [
        {"name": "Leche Entera", "barcode": "77012345", "category": "Lácteos", "price": 4200, "stock": 25},
        {"name": "Pan Tajado", "barcode": "77054321", "category": "Panadería", "price": 5000, "stock": 3}
    ]
    excel_inv = generate_inventory_report_excel(products, "Tienda Prueba")
    assert excel_inv is not None
    assert len(excel_inv.getvalue()) > 1000


def test_jwt_token_generation_and_auth(client, test_app_ctx):
    store = test_app_ctx["store"]
    email = f"jwt_user_{int(datetime.now().timestamp())}@test.com"
    pwd = "JwtPassword123!"

    user = User(name="Usuario JWT", email=email, is_admin=True, store_id=store.id, status="ACTIVO")
    user.set_password(pwd)
    db.session.add(user)
    db.session.commit()

    # 1. Missing fields
    res = client.post('/api/auth/token', json={})
    assert res.status_code == 400

    # 2. Bad credentials
    res = client.post('/api/auth/token', json={"email": email, "password": "wrong"})
    assert res.status_code == 401

    # 3. Valid credentials
    res = client.post('/api/auth/token', json={"email": email, "password": pwd})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["email"] == email

    token = data["token"]

    # 4. Use token in Authorization header
    headers = {"Authorization": f"Bearer {token}"}
    users_res = client.get('/api/users', headers=headers)
    assert users_res.status_code == 200
    assert users_res.is_json
