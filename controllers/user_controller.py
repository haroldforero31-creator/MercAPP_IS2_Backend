from flask import Blueprint, request
from flask_login import login_required, current_user
from dtos.user_dto import UserCreateDTO, UserUpdateDTO, UserLoginDTO
from services.user_service import UserService
from utilities.response_helper import success_response, error_response
from utilities.rate_limiter import limiter

user_controller = Blueprint('user_controller', __name__, url_prefix='/api/users')

@user_controller.route('', methods=['GET'])
@login_required
def get_all():
    """GET /api/users - Listar usuarios (solo admin)"""
    if not current_user.is_admin:
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)
    users = UserService.get_all_users()
    return success_response(data=users, message="Usuarios recuperados exitosamente.")


@user_controller.route('/<int:user_id>', methods=['GET'])
@login_required
def get_by_id(user_id):
    """GET /api/users/<id> - Detalle de usuario (solo admin)"""
    if not current_user.is_admin:
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)
    user, error = UserService.get_user_by_id(user_id)
    if error:
        return error_response(message=error, status_code=404)
    return success_response(data=user)


@user_controller.route('', methods=['POST'])
@login_required
def create():
    """POST /api/users - Registrar usuario (solo admin, is_admin=False por defecto)"""
    if not current_user.is_admin:
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)
    data = request.get_json() or {}
    dto = UserCreateDTO(
        name=data.get('name'),
        email=data.get('email'),
        password=data.get('password'),
        is_admin=data.get('is_admin', False),
        store_id=data.get('store_id', current_user.store_id if hasattr(current_user, 'store_id') else 1)
    )
    user, error = UserService.create_user(dto)
    if error:
        if isinstance(error, list):
            return error_response(message="Errores de validación", errors=error, status_code=400)
        return error_response(message=error, status_code=400)

    return success_response(data=user, message="Usuario creado exitosamente.", status_code=201)


@user_controller.route('/<int:user_id>', methods=['PUT'])
@login_required
def update(user_id):
    """PUT /api/users/<id> - Actualizar usuario (solo admin)"""
    if not current_user.is_admin:
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)
    data = request.get_json() or {}
    dto = UserUpdateDTO(
        name=data.get('name'),
        email=data.get('email'),
        password=data.get('password'),
        is_admin=data.get('is_admin'),
        status=data.get('status')
    )
    user, error = UserService.update_user(user_id, dto)
    if error:
        if isinstance(error, list):
            return error_response(message="Errores de validación", errors=error, status_code=400)
        return error_response(message=error, status_code=400)

    return success_response(data=user, message="Usuario actualizado exitosamente.")


@user_controller.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete(user_id):
    """DELETE /api/users/<id> - Eliminar usuario (solo admin, no puede eliminarse a si mismo)"""
    if not current_user.is_admin:
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)
    if current_user.id == user_id:
        return error_response(message="No puedes eliminar tu propia cuenta.", status_code=400)
    success, error = UserService.delete_user(user_id)
    if error:
        return error_response(message=error, status_code=404)
    return success_response(message="Usuario eliminado exitosamente.")


@user_controller.route('/login', methods=['POST'])
@limiter.limit(max_requests=5, window_seconds=60, key='api_users_login')
def login():
    """POST /api/users/login - Autenticar credenciales (ruta publica)"""
    data = request.get_json() or {}
    dto = UserLoginDTO(
        email=data.get('email'),
        password=data.get('password')
    )
    user, error = UserService.authenticate(dto)
    if error:
        if isinstance(error, list):
            return error_response(message="Credenciales requeridas", errors=error, status_code=400)
        return error_response(message=error, status_code=401)

    return success_response(data=user, message="Autenticación exitosa.")
