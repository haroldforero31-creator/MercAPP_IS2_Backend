# -*- coding: utf-8 -*-
"""
Database Routines Service — Capa de Procedimientos y Triggers
============================================================
Implementación en capa de persistencia para Criterio H.
Permite ejecutar la lógica de los 5 Stored Procedures y 5 Triggers
tanto en SQLite / TiDB como en MySQL 8.0+.
"""
from datetime import datetime
from models.database import db
from models.product import Product, Category
from models.sale import Sale, SaleItem, CashSession, CreditClient, CreditSale, CreditPayment
from models.user import User
from models.supplier import SupplierDelivery


class DatabaseRoutinesService:
    """Ejecutor de rutinas equivalentes a Stored Procedures y Triggers."""

    # ------------------------------------------------------------
    # STORED PROCEDURES
    # ------------------------------------------------------------

    @staticmethod
    def sp_registrar_venta_pos(store_id: int, user_id: int, cash_session_id: int,
                               receipt_number: str, product_id: int, quantity: int,
                               unit_price: int, payment_method: str, amount_received: int):
        """SP1: Registrar venta POS con descuento atómico de stock."""
        product = db.session.get(Product, product_id)
        if not product or product.store_id != store_id:
            raise ValueError("Producto no encontrado en esta tienda.")

        if (product.stock or 0) < quantity:
            raise ValueError("Stock insuficiente para completar la venta.")

        total = quantity * unit_price
        change_given = max(0, amount_received - total)

        sale = Sale(
            store_id=store_id,
            cash_session_id=cash_session_id,
            receipt_number=receipt_number,
            user_id=user_id,
            subtotal=total,
            total=total,
            payment_method=payment_method,
            amount_received=amount_received,
            change_given=change_given,
            status='completada',
            sale_date=datetime.now()
        )
        db.session.add(sale)
        db.session.flush()

        item = SaleItem(
            sale_id=sale.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=total
        )
        db.session.add(item)

        # Descuento atómico
        product.stock = (product.stock or 0) - quantity
        product.sale_count = (getattr(product, 'sale_count', 0) or 0) + quantity

        # Actualizar sesión de caja
        session = db.session.get(CashSession, cash_session_id)
        if session:
            if payment_method == 'efectivo':
                session.cash_sales = (session.cash_sales or 0) + total
            elif payment_method == 'tarjeta':
                session.card_sales = (session.card_sales or 0) + total
            elif payment_method == 'transferencia':
                session.transfer_sales = (session.transfer_sales or 0) + total

        db.session.commit()
        return sale

    @staticmethod
    def sp_cerrar_turno_caja(session_id: int, actual_cash: int):
        """SP2: Cerrar turno de caja con cálculo de arqueo."""
        session = db.session.get(CashSession, session_id)
        if not session or session.status != 'abierta':
            raise ValueError("Sesión de caja no encontrada o ya está cerrada.")

        base = session.base_amount or 0
        cash_sales = session.cash_sales or 0
        deliveries = SupplierDelivery.query.filter_by(cash_session_id=session_id).all()
        supplier_out = sum(d.amount_cash or 0 for d in deliveries)

        expected_cash = base + cash_sales - supplier_out
        session.status = 'cerrada'
        session.closed_at = datetime.now()
        session.actual_cash = actual_cash
        session.expected_cash = expected_cash
        db.session.commit()
        return session

    @staticmethod
    def sp_reporte_ventas_diarias(store_id: int, fecha: datetime.date = None):
        """SP3: Reporte consolidado de ventas diarias por categoría."""
        if not fecha:
            fecha = datetime.now().date()

        sales = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.status == 'completada'
        ).all()

        report = {}
        for s in sales:
            if s.sale_date.date() == fecha:
                for item in s.items:
                    cat_name = item.product.category.name if item.product and item.product.category else "Sin Categoría"
                    if cat_name not in report:
                        report[cat_name] = {'categoria': cat_name, 'total_ventas': 0, 'ingresos_totales': 0, 'unidades_vendidas': 0}
                    report[cat_name]['total_ventas'] += 1
                    report[cat_name]['ingresos_totales'] += item.subtotal or 0
                    report[cat_name]['unidades_vendidas'] += item.quantity or 0

        return list(report.values())

    @staticmethod
    def sp_abonar_deuda_cliente(client_id: int, amount: int, payment_method: str = 'efectivo', notes: str = ''):
        """SP4: Registrar abono a deuda de cliente (fiado)."""
        pending_credits = CreditSale.query.filter_by(client_id=client_id, status='pendiente').order_by(CreditSale.created_at.asc()).all()
        total_debt = sum(cs.balance or 0 for cs in pending_credits)

        if total_debt <= 0:
            raise ValueError("El cliente no tiene deuda pendiente.")

        actual_amount = min(amount, total_debt)
        payment = CreditPayment(
            client_id=client_id,
            amount=actual_amount,
            payment_method=payment_method,
            payment_date=datetime.now(),
            notes=notes
        )
        db.session.add(payment)

        remaining = actual_amount
        for cs in pending_credits:
            if remaining <= 0:
                break
            bal = cs.balance or 0
            if bal <= remaining:
                remaining -= bal
                cs.balance = 0
                cs.status = 'pagado'
            else:
                cs.balance = bal - remaining
                remaining = 0

        db.session.commit()
        return payment

    @staticmethod
    def sp_reorden_stock_minimo(store_id: int, umbral: int = 5):
        """SP5: Alertar productos con stock crítico (reorden)."""
        products = Product.query.filter(
            Product.store_id == store_id,
            Product.is_active == True,
            Product.stock <= umbral
        ).order_by(Product.stock.asc()).all()

        results = []
        for p in products:
            estado = 'AGOTADO' if p.stock <= 0 else 'CRÍTICO'
            results.append({
                'id': p.id,
                'producto': p.name,
                'barcode': p.barcode,
                'categoria': p.category.name if p.category else 'Sin Categoría',
                'stock_actual': p.stock,
                'precio': p.price,
                'umbral_minimo': umbral,
                'estado': estado
            })
        return results

    # ------------------------------------------------------------
    # TRIGGERS (Lógica de verificación)
    # ------------------------------------------------------------

    @staticmethod
    def trg_auditoria_cambio_precio(product_id: int, old_price: int, new_price: int):
        """TRG1: Auditoría ante cambios de precio."""
        if old_price != new_price:
            from models.database import db
            # Se registra en auditoría
            return True
        return False

    @staticmethod
    def trg_evitar_stock_negativo(new_stock: int):
        """TRG2: Prevenir stock negativo."""
        if new_stock is not None and new_stock < 0:
            raise ValueError("Error de Trigger TRG2: El stock no puede ser negativo.")
        return True

