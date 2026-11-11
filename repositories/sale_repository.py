from datetime import datetime, timedelta
from models.database import db
from models.sale import CashSession, Sale, SaleItem, CreditClient, CreditSale, CreditPayment

class SaleRepository:
    """
    Capa de Repositorio para Ventas, Sesiones de Caja y Fiados.
    """

    @staticmethod
    def get_today_session(store_id: int, user_id: int = None):
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        today_end = today_start + timedelta(days=1)
        
        query = CashSession.query.filter(
            CashSession.store_id == store_id,
            CashSession.opened_at >= today_start,
            CashSession.opened_at < today_end
        )
        if user_id:
            query = query.filter(CashSession.user_id == user_id)
        return query.first()

    @staticmethod
    def get_any_open_session(store_id: int):
        return CashSession.query.filter_by(
            store_id=store_id, status='abierta'
        ).order_by(CashSession.opened_at.desc()).first()

    @staticmethod
    def create_session(store_id: int, user_id: int, base_amount: int):
        session = CashSession(
            store_id=store_id,
            user_id=user_id,
            base_amount=base_amount,
            expected_cash=base_amount,
            status='abierta'
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def get_session_by_id(session_id: int):
        return db.session.get(CashSession, session_id)

    @staticmethod
    def get_sessions_by_store(store_id: int):
        return CashSession.query.filter_by(store_id=store_id).order_by(CashSession.opened_at.desc()).all()

    @staticmethod
    def create_sale(store_id: int, user_id: int, receipt_number: str,
                    subtotal: int, total: int, payment_method: str,
                    cash_session_id: int = None, amount_received: int = 0,
                    change_given: int = 0, payment_ref: str = None,
                    amount_cash: int = 0, amount_card: int = 0, amount_transfer: int = 0):
        sale = Sale(
            store_id=store_id,
            cash_session_id=cash_session_id,
            receipt_number=receipt_number,
            user_id=user_id,
            subtotal=subtotal,
            total=total,
            payment_method=payment_method,
            amount_received=amount_received,
            change_given=change_given,
            payment_ref=payment_ref,
            amount_cash=amount_cash,
            amount_card=amount_card,
            amount_transfer=amount_transfer,
            status='completada'
        )
        db.session.add(sale)
        db.session.flush()
        return sale

    @staticmethod
    def add_sale_item(sale_id: int, product_id: int, quantity: int, unit_price: int,
                      subtotal: int, weight_grams: int = None, weight_unit: str = None):
        item = SaleItem(
            sale_id=sale_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            weight_grams=weight_grams,
            weight_unit=weight_unit
        )
        db.session.add(item)
        return item

    @staticmethod
    def get_sale_by_id(sale_id: int):
        return db.session.get(Sale, sale_id)

    @staticmethod
    def get_sales_by_store(store_id: int, limit: int = 100):
        return Sale.query.filter_by(store_id=store_id).order_by(Sale.sale_date.desc()).limit(limit).all()

    @staticmethod
    def generate_receipt_number(store_id: int):
        today = datetime.now().strftime('%Y%m%d')
        prefix = f"MRC-{today}-"
        last_sale = Sale.query.filter(
            Sale.store_id == store_id,
            Sale.receipt_number.like(f"{prefix}%")
        ).order_by(Sale.id.desc()).first()
        
        if last_sale:
            try:
                last_num = int(last_sale.receipt_number.split('-')[-1])
                return f"{prefix}{last_num + 1:04d}"
            except (ValueError, IndexError):
                pass
        return f"{prefix}0001"
