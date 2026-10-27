from datetime import datetime
from models.database import db
from models.product import Product, Category
from repositories.sale_repository import SaleRepository
from utilities.helpers import round_to_50, validate_payment

class SaleService:
    """
    Capa de Servicio para la Lógica de Negocio de Ventas y Caja.
    """

    @staticmethod
    def get_today_session(store_id: int, user_id: int = None):
        return SaleRepository.get_today_session(store_id, user_id)

    @staticmethod
    def open_session(store_id: int, user_id: int, base_amount: int):
        active = SaleRepository.get_today_session(store_id, user_id)
        if active:
            return active, "Ya existe una sesión abierta para el día de hoy."
        session = SaleRepository.create_session(store_id, user_id, base_amount)
        return session, None

    @staticmethod
    def close_session(session_id: int, actual_cash: int):
        session = SaleRepository.get_session_by_id(session_id)
        if not session:
            return None, "Sesión no encontrada."
        if session.status == 'cerrada':
            return None, "La sesión ya se encuentra cerrada."

        sales = session.sales
        completed_sales = [s for s in sales if s.status == 'completada']
        cash = sum(s.amount_cash or 0 for s in completed_sales)
        card = sum(s.amount_card or 0 for s in completed_sales)
        transfer = sum(s.amount_transfer or 0 for s in completed_sales)

        expected_cash = session.base_amount + cash

        session.cash_sales = cash
        session.card_sales = card
        session.transfer_sales = transfer
        session.expected_cash = expected_cash
        session.actual_cash = actual_cash
        session.status = 'cerrada'
        session.closed_at = datetime.now()
        db.session.commit()

        return session, None
