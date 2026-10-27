"""
Merki Query Engine — Consultas a la Base de Datos
==================================================
Todas las funciones son de SOLO LECTURA (SELECT).
Cada consulta filtra por store_id para seguridad multi-tenant.
"""
from datetime import datetime, timedelta
from sqlalchemy import func, desc, case, and_, or_
from models.database import db
from models.product import Product, Category, Subcategory
from models.sale import Sale, SaleItem, CreditClient, CreditSale, CashSession


class MerkiQueries:
    """Capa de consultas optimizadas para el asistente Merki."""

    SYNONYMS = {
        'kilo': ['kilo', 'kg', '1kg', '1 kg'],
        'kilos': ['kilo', 'kg'],
        'litro': ['litro', 'lt', 'l', '1l', '1lt'],
        'litros': ['litro', 'lt', 'l'],
        'gramos': ['gramo', 'gr', 'g'],
        'gramo': ['gramo', 'gr', 'g'],
        'frutino': ['frutiño', 'frutino'],
        'frutinos': ['frutiño', 'frutino'],
        'shampoo': ['shampoo', 'champu', 'champoo'],
        'sobre': ['sobre', 'sob', 'sobres']
    }

    # ============================================================
    # PRODUCTOS
    # ============================================================

    @classmethod
    def _build_product_filter(cls, store_id, search_term=None):
        """Genera query base de productos con coincidencia exacta o multi-término inteligente."""
        query = Product.query.filter(
            Product.store_id == store_id,
            Product.is_active == True
        )
        if not search_term or not search_term.strip():
            return query

        clean = search_term.strip().lower()
        # 1. Probar coincidencia directa de subcadena
        direct = query.filter(Product.name.ilike(f"%{clean}%"))
        if direct.count() > 0:
            return direct

        # 2. Dividir en palabras y aplicar sinónimos
        words = [w for w in clean.split() if len(w) > 2]
        if not words:
            return direct

        conds = []
        for w in words:
            variants = cls.SYNONYMS.get(w, [w])
            conds.append(or_(*[Product.name.ilike(f"%{v}%") for v in variants]))

        return query.filter(and_(*conds))

    @classmethod
    def search_product(cls, store_id, search_term):
        """Busca productos por nombre (coincidencia inteligente)."""
        return cls._build_product_filter(store_id, search_term).all()

    @classmethod
    def product_exists(cls, store_id, search_term):
        """Verifica si un producto existe y retorna info básica."""
        products = cls.search_product(store_id, search_term)
        if not products:
            return None
        return {
            'found': True,
            'count': len(products),
            'products': [
                {
                    'name': p.name,
                    'price': p.price,
                    'stock': p.stock,
                    'category': p.category.name if p.category else 'Sin categoría'
                }
                for p in products
            ]
        }

    @classmethod
    def product_price(cls, store_id, search_term):
        """Obtiene el precio de un producto."""
        products = cls.search_product(store_id, search_term)
        if not products:
            return None
        return [
            {'name': p.name, 'price': p.price, 'stock': p.stock}
            for p in products
        ]

    @classmethod
    def cheapest_product(cls, store_id, search_term=None):
        """Encuentra el producto más barato (opcionalmente filtrando por término)."""
        query = cls._build_product_filter(store_id, search_term)
        product = query.filter(Product.price > 0).order_by(Product.price.asc()).first()
        if not product:
            return None
        return {'name': product.name, 'price': product.price, 'stock': product.stock}

    @classmethod
    def most_expensive_product(cls, store_id, search_term=None):
        """Encuentra el producto más caro (opcionalmente filtrando por término)."""
        query = cls._build_product_filter(store_id, search_term)
        product = query.order_by(Product.price.desc()).first()
        if not product:
            return None
        return {'name': product.name, 'price': product.price, 'stock': product.stock}

    @staticmethod
    def product_stock(store_id, search_term):
        """Consulta el stock de un producto específico."""
        products = MerkiQueries.search_product(store_id, search_term)
        if not products:
            return None
        return [
            {'name': p.name, 'stock': p.stock, 'price': p.price}
            for p in products
        ]

    @staticmethod
    def count_product_types(store_id, search_term):
        """Cuenta cuántos tipos/variantes de un producto hay."""
        products = MerkiQueries.search_product(store_id, search_term)
        return {
            'term': search_term,
            'count': len(products),
            'products': [{'name': p.name, 'price': p.price} for p in products]
        }

    @staticmethod
    def products_in_category(store_id, category_name):
        """Lista productos de una categoría específica."""
        category = Category.query.filter(
            Category.store_id == store_id,
            Category.name.ilike(f"%{category_name}%")
        ).first()
        if not category:
            return None
        products = Product.query.filter(
            Product.store_id == store_id,
            Product.category_id == category.id,
            Product.is_active == True
        ).all()
        return {
            'category': category.name,
            'count': len(products),
            'products': [{'name': p.name, 'price': p.price} for p in products]
        }

    @staticmethod
    def total_products(store_id):
        """Cuenta el total de productos activos en la tienda."""
        count = Product.query.filter(
            Product.store_id == store_id,
            Product.is_active == True
        ).count()
        return {'total': count}

    @staticmethod
    def list_categories(store_id):
        """Lista todas las categorías de la tienda."""
        categories = Category.query.filter_by(store_id=store_id).order_by(
            Category.display_order.asc()
        ).all()
        result = []
        for cat in categories:
            prod_count = Product.query.filter(
                Product.store_id == store_id,
                Product.category_id == cat.id,
                Product.is_active == True
            ).count()
            result.append({'name': cat.name, 'product_count': prod_count})
        return {'categories': result, 'total': len(result)}

    @classmethod
    def search_by_code(cls, store_id, code):
        """Busca producto por código de barras o código PLU exacto."""
        if not code:
            return None
        clean = str(code).strip()
        return Product.query.filter(
            Product.store_id == store_id,
            Product.is_active == True,
            or_(Product.barcode == clean, Product.plu_code == clean)
        ).first()

    @classmethod
    def product_full_info(cls, store_id, search_term):
        """Obtiene toda la información detallada disponible de un producto."""
        if not search_term or not search_term.strip():
            return None
        code_match = cls.search_by_code(store_id, search_term)
        if code_match:
            prod = code_match
            total_matches = 1
        else:
            prods = cls.search_product(store_id, search_term)
            if not prods:
                return None
            prod = prods[0]
            total_matches = len(prods)

        return {
            'found': True,
            'id': prod.id,
            'name': prod.name,
            'price': prod.price,
            'stock': prod.stock,
            'sell_by_weight': bool(prod.sell_by_weight),
            'weight_unit': prod.weight_unit or 'kg',
            'barcode': prod.barcode,
            'plu_code': prod.plu_code,
            'has_barcode': bool(prod.has_barcode),
            'category': prod.category.name if prod.category else 'Sin categoría',
            'subcategory': prod.subcategory.name if prod.subcategory else None,
            'total_matches': total_matches
        }

    @classmethod
    def compare_products(cls, store_id, term_a, term_b):
        """Compara dos productos en precio, existencias y categoría."""
        prods_a = cls.search_product(store_id, term_a)
        prods_b = cls.search_product(store_id, term_b)

        if not prods_a or not prods_b:
            return {
                'found': False,
                'missing_a': not bool(prods_a),
                'missing_b': not bool(prods_b),
                'term_a': term_a,
                'term_b': term_b
            }

        pa = prods_a[0]
        pb = prods_b[0]

        price_diff = abs(pa.price - pb.price)
        stock_a = pa.stock if pa.stock is not None else 0
        stock_b = pb.stock if pb.stock is not None else 0
        stock_diff = abs(stock_a - stock_b)

        return {
            'found': True,
            'prod_a': {
                'name': pa.name,
                'price': pa.price,
                'stock': pa.stock,
                'sell_by_weight': bool(pa.sell_by_weight),
                'weight_unit': pa.weight_unit or 'kg',
                'category': pa.category.name if pa.category else 'Sin categoría'
            },
            'prod_b': {
                'name': pb.name,
                'price': pb.price,
                'stock': pb.stock,
                'sell_by_weight': bool(pb.sell_by_weight),
                'weight_unit': pb.weight_unit or 'kg',
                'category': pb.category.name if pb.category else 'Sin categoría'
            },
            'price_diff': price_diff,
            'cheaper': 'a' if pa.price < pb.price else ('b' if pb.price < pa.price else 'equal'),
            'stock_diff': stock_diff,
            'more_stock': 'a' if stock_a > stock_b else ('b' if stock_b > stock_a else 'equal')
        }

    # ============================================================
    # VENTAS
    # ============================================================

    @staticmethod
    def sales_today(store_id):
        """Resumen de ventas del día."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        sales = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.sale_date >= today_start,
            Sale.status == 'completada'
        ).all()
        total = sum(s.total for s in sales)
        return {
            'count': len(sales),
            'total': total,
            'period': 'hoy'
        }

    @staticmethod
    def sales_week(store_id):
        """Resumen de ventas de la semana."""
        today = datetime.now()
        week_start = (today - timedelta(days=today.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        sales = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.sale_date >= week_start,
            Sale.status == 'completada'
        ).all()
        total = sum(s.total for s in sales)
        return {
            'count': len(sales),
            'total': total,
            'period': 'esta semana'
        }

    @staticmethod
    def sales_month(store_id):
        """Resumen de ventas del mes."""
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        sales = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.sale_date >= month_start,
            Sale.status == 'completada'
        ).all()
        total = sum(s.total for s in sales)
        return {
            'count': len(sales),
            'total': total,
            'period': 'este mes'
        }

    @staticmethod
    def sales_on_date(store_id, target_date):
        """Consulta de ventas para una fecha específica (date object o string YYYY-MM-DD)."""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())

        sales = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.sale_date >= day_start,
            Sale.sale_date <= day_end,
            Sale.status == 'completada'
        ).all()

        total = sum(s.total for s in sales)
        return {
            'date': target_date.strftime('%d/%m/%Y'),
            'date_obj': target_date,
            'count': len(sales),
            'total': total
        }

    @staticmethod
    def sales_in_date_range(store_id, start_date, end_date, label=None):
        """Consulta de ventas en un rango de fechas."""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        dt_start = datetime.combine(start_date, datetime.min.time())
        dt_end = datetime.combine(end_date, datetime.max.time())

        sales = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.sale_date >= dt_start,
            Sale.sale_date <= dt_end,
            Sale.status == 'completada'
        ).all()

        total = sum(s.total for s in sales)
        return {
            'label': label or f"{start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}",
            'start_date': start_date.strftime('%d/%m/%Y'),
            'end_date': end_date.strftime('%d/%m/%Y'),
            'count': len(sales),
            'total': total
        }

    @staticmethod
    def last_sale(store_id):
        """Obtiene información de la última venta."""
        sale = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.status == 'completada'
        ).order_by(Sale.sale_date.desc()).first()
        if not sale:
            return None
        items = SaleItem.query.filter_by(sale_id=sale.id).all()
        return {
            'receipt': sale.receipt_number,
            'total': sale.total,
            'items_count': len(items),
            'payment_method': sale.payment_method,
            'date': sale.sale_date.strftime('%d/%m/%Y %I:%M %p'),
            'items': [
                {'name': item.product.name if item.product else 'Producto', 'qty': item.quantity, 'subtotal': item.subtotal}
                for item in items[:5]  # máximo 5 items para no saturar la respuesta
            ]
        }

    @staticmethod
    def best_seller(store_id):
        """Producto más vendido (por cantidad)."""
        result = db.session.query(
            Product.name,
            Product.price,
            func.sum(SaleItem.quantity).label('total_sold')
        ).join(
            SaleItem, SaleItem.product_id == Product.id
        ).join(
            Sale, Sale.id == SaleItem.sale_id
        ).filter(
            Product.store_id == store_id,
            Sale.status == 'completada'
        ).group_by(
            Product.id
        ).order_by(
            desc('total_sold')
        ).first()

        if not result:
            return None
        return {
            'name': result[0],
            'price': result[1],
            'total_sold': int(result[2])
        }

    @staticmethod
    def sales_count_today(store_id):
        """Solo el conteo de ventas de hoy."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.sale_date >= today_start,
            Sale.status == 'completada'
        ).count()
        return {'count': count}

    # ============================================================
    # DEUDAS / CRÉDITO
    # ============================================================

    @staticmethod
    def total_debt(store_id):
        """Total de deuda pendiente de todos los clientes de crédito."""
        clients = CreditClient.query.filter(
            CreditClient.store_id == store_id,
            CreditClient.is_active == True
        ).all()
        total = sum(c.total_debt for c in clients)
        clients_with_debt = [c for c in clients if c.total_debt > 0]
        return {
            'total': total,
            'clients_with_debt': len(clients_with_debt),
            'total_clients': len(clients)
        }

    @staticmethod
    def who_owes_most(store_id):
        """Cliente que más debe."""
        clients = CreditClient.query.filter(
            CreditClient.store_id == store_id,
            CreditClient.is_active == True
        ).all()
        if not clients:
            return None
        clients_with_debt = [c for c in clients if c.total_debt > 0]
        if not clients_with_debt:
            return {'no_debt': True}
        top = max(clients_with_debt, key=lambda c: c.total_debt)
        return {
            'name': top.name,
            'debt': top.total_debt,
            'days': top.days_without_payment
        }

    @staticmethod
    def debt_client_count(store_id):
        """Cuántos clientes tienen deuda pendiente."""
        clients = CreditClient.query.filter(
            CreditClient.store_id == store_id,
            CreditClient.is_active == True
        ).all()
        with_debt = [c for c in clients if c.total_debt > 0]
        return {
            'with_debt': len(with_debt),
            'total': len(clients)
        }

    @classmethod
    def client_debt_detail(cls, store_id, client_name):
        """Consulta detallada de la deuda, abonos y compras de un cliente específico."""
        if not client_name or not client_name.strip():
            return None

        clean = client_name.strip().lower()

        # 1. Búsqueda directa por subcadena
        clients = CreditClient.query.filter(
            CreditClient.store_id == store_id,
            CreditClient.is_active == True,
            CreditClient.name.ilike(f"%{clean}%")
        ).all()

        # 2. Búsqueda por palabras si no hubo coincidencia directa
        if not clients:
            words = [w for w in clean.split() if len(w) > 2]
            if words:
                conds = [CreditClient.name.ilike(f"%{w}%") for w in words]
                clients = CreditClient.query.filter(
                    CreditClient.store_id == store_id,
                    CreditClient.is_active == True,
                    or_(*conds)
                ).all()

        if not clients:
            return {'found': False, 'name': client_name}

        client = clients[0]
        return {
            'found': True,
            'id': client.id,
            'name': client.name,
            'phone': client.phone,
            'total_debt': client.total_debt,
            'total_purchased': client.total_purchased,
            'total_paid': client.total_paid,
            'days_without_payment': client.days_without_payment,
            'is_blocked': client.is_blocked,
            'total_matches': len(clients)
        }

    # ============================================================
    # STOCK
    # ============================================================

    @staticmethod
    def out_of_stock(store_id):
        """Productos agotados (stock = 0)."""
        products = Product.query.filter(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.stock == 0,
            Product.sell_by_weight == False
        ).all()
        return {
            'count': len(products),
            'products': [{'name': p.name, 'price': p.price} for p in products[:10]]
        }

    @staticmethod
    def low_stock(store_id, threshold=5):
        """Productos con stock bajo (menos de threshold unidades)."""
        products = Product.query.filter(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.stock <= threshold,
            Product.stock > 0,
            Product.sell_by_weight == False
        ).order_by(Product.stock.asc()).all()
        return {
            'count': len(products),
            'products': [
                {'name': p.name, 'stock': p.stock, 'price': p.price}
                for p in products[:10]
            ]
        }

    # ============================================================
    # SESIÓN DE CAJA
    # ============================================================

    @staticmethod
    def active_session(store_id):
        """Info de la sesión de caja activa y ventas en tiempo real."""
        session = CashSession.query.filter(
            CashSession.store_id == store_id,
            CashSession.status == 'abierta'
        ).order_by(CashSession.opened_at.desc()).first()

        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if not session:
            # Fallback si no hay sesión abierta: ventas del día
            day_sales = Sale.query.filter(
                Sale.store_id == store_id,
                Sale.sale_date >= today_start,
                Sale.status == 'completada'
            ).all()
            total_day = sum(s.total for s in day_sales)
            return {
                'active': False,
                'sales_count': len(day_sales),
                'total_sales': total_day,
                'cash_sales': sum((s.amount_cash if s.amount_cash else (s.total if s.payment_method == 'efectivo' else 0)) for s in day_sales),
                'card_sales': sum((s.amount_card if s.amount_card else (s.total if s.payment_method == 'tarjeta' else 0)) for s in day_sales),
                'transfer_sales': sum((s.amount_transfer if s.amount_transfer else (s.total if s.payment_method == 'transferencia' else 0)) for s in day_sales)
            }

        sales = Sale.query.filter_by(cash_session_id=session.id, status='completada').all()
        total_sales = sum(s.total for s in sales)
        cash_sales = sum(
            (s.amount_cash if (s.amount_cash is not None and s.amount_cash > 0)
             else (s.total if s.payment_method == 'efectivo' else 0))
            for s in sales
        )
        card_sales = sum(
            (s.amount_card if (s.amount_card is not None and s.amount_card > 0)
             else (s.total if s.payment_method == 'tarjeta' else 0))
            for s in sales
        )
        transfer_sales = sum(
            (s.amount_transfer if (s.amount_transfer is not None and s.amount_transfer > 0)
             else (s.total if s.payment_method == 'transferencia' else 0))
            for s in sales
        )

        return {
            'active': True,
            'session_id': session.id,
            'base': session.base_amount or 0,
            'cash_sales': cash_sales,
            'card_sales': card_sales,
            'transfer_sales': transfer_sales,
            'total_sales': total_sales,
            'sales_count': len(sales),
            'opened_at': session.opened_at.strftime('%I:%M %p')
        }

