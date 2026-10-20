from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from services.sale_service import SaleService
from repositories.sale_repository import SaleRepository
from utilities.response_helper import success_response, error_response

sale_controller = Blueprint('sale_controller', __name__, url_prefix='/api')

@sale_controller.route('/sessions/today', methods=['GET'])
@login_required
def get_today_session():
    """GET /api/sessions/today - Obtener la sesión activa de hoy"""
    session = SaleService.get_today_session(current_user.store_id)
    if not session:
        return error_response(message="No hay una sesión activa de caja para hoy.", status_code=404)
    return success_response(data={
        'id': session.id,
        'base_amount': session.base_amount,
        'status': session.status,
        'opened_at': session.opened_at.isoformat()
    })

@sale_controller.route('/sessions/open', methods=['POST'])
@login_required
def open_session():
    """POST /api/sessions/open - Abrir sesión de caja"""
    data = request.get_json() or {}
    base_amount = data.get('base_amount', 0)
    try:
        base = int(base_amount)
    except ValueError:
        return error_response(message="El monto base debe ser un número entero.", status_code=400)

    session, error = SaleService.open_session(current_user.store_id, current_user.id, base)
    if error:
        return error_response(message=error, status_code=400)
    return success_response(data={'id': session.id, 'base_amount': session.base_amount}, message="Caja abierta exitosamente.", status_code=201)

@sale_controller.route('/sessions/<int:session_id>/close', methods=['POST'])
@login_required
def close_session(session_id):
    """POST /api/sessions/<id>/close - Cerrar sesión de caja"""
    data = request.get_json() or {}
    actual_cash = data.get('actual_cash')
    if actual_cash is None:
        return error_response(message="Debes especificar el monto de recuento de efectivo.", status_code=400)
    try:
        actual = int(actual_cash)
    except ValueError:
        return error_response(message="El monto de recuento debe ser numérico.", status_code=400)

    session, error = SaleService.close_session(session_id, actual)
    if error:
        return error_response(message=error, status_code=400)
    return success_response(data={'id': session.id, 'difference': session.actual_cash - session.expected_cash}, message="Caja cerrada exitosamente.")
