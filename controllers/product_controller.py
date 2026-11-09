from flask import Blueprint, request
from flask_login import login_required, current_user
from dtos.product_dto import ProductCreateDTO, ProductUpdateDTO
from services.product_service import ProductService
from repositories.product_repository import ProductRepository
from utilities.response_helper import success_response, error_response

product_controller = Blueprint('product_controller', __name__, url_prefix='/api')


@product_controller.route('/products', methods=['GET'])
def get_products():
    """
    GET /api/products?q=termino_busqueda&store_id=X
    Lista productos o busca por término.
    """
    store_id = None
    if current_user and current_user.is_authenticated and hasattr(current_user, 'store_id'):
        store_id = current_user.store_id
    if not store_id:
        store_id = request.args.get('store_id', 1, type=int)

    query = request.args.get('q', '').strip()
    if query:
        products = ProductService.search_products(query, store_id=store_id)
    else:
        products = ProductService.get_all_products(store_id=store_id)
    return success_response(data=products, message="Productos recuperados exitosamente.")


@product_controller.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """GET /api/products/<id>"""
    product, error = ProductService.get_product_by_id(product_id)
    if error:
        return error_response(message=error, status_code=404)
    return success_response(data=product)


@product_controller.route('/products', methods=['POST'])
@login_required
def create_product():
    """POST /api/products - Crear un nuevo producto (solo administrador)"""
    if not getattr(current_user, 'is_admin', False):
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)

    user_store_id = getattr(current_user, 'store_id', None)
    if not user_store_id:
        return error_response(message="El usuario no tiene una tienda asociada.", status_code=400)

    data = request.get_json() or {}
    dto = ProductCreateDTO(
        name=data.get('name'),
        price=data.get('price'),
        category_id=data.get('category_id'),
        store_id=user_store_id,  # P0-3 FIX: Forzar siempre la tienda de la sesión autenticada
        barcode=data.get('barcode'),
        subcategory_id=data.get('subcategory_id'),
        stock=data.get('stock', 0),
        sell_by_weight=data.get('sell_by_weight', False),
        weight_unit=data.get('weight_unit', 'kg'),
        plu_code=data.get('plu_code'),
        image=data.get('image', 'default_product.png')
    )
    product, error = ProductService.create_product(dto)
    if error:
        if isinstance(error, list):
            return error_response(message="Errores de validación", errors=error, status_code=400)
        return error_response(message=error, status_code=400)

    return success_response(data=product, message="Producto creado exitosamente.", status_code=201)


@product_controller.route('/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """PUT /api/products/<id> - Actualizar producto (solo administrador de la tienda)"""
    if not getattr(current_user, 'is_admin', False):
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)

    user_store_id = getattr(current_user, 'store_id', None)
    existing_product = ProductRepository.get_by_id(product_id)
    if not existing_product or not existing_product.is_active:
        return error_response(message="Producto no encontrado.", status_code=404)

    # P0-3 FIX: Validar que el producto pertenezca a la tienda del usuario
    if user_store_id and existing_product.store_id != user_store_id:
        return error_response(message="No tienes permiso para modificar productos de otra tienda.", status_code=403)

    data = request.get_json() or {}
    dto = ProductUpdateDTO(
        name=data.get('name'),
        price=data.get('price'),
        category_id=data.get('category_id'),
        subcategory_id=data.get('subcategory_id'),
        barcode=data.get('barcode'),
        stock=data.get('stock'),
        sell_by_weight=data.get('sell_by_weight'),
        weight_unit=data.get('weight_unit'),
        plu_code=data.get('plu_code'),
        is_active=data.get('is_active')
    )
    product, error = ProductService.update_product(product_id, dto, store_id=user_store_id or 1)
    if error:
        if isinstance(error, list):
            return error_response(message="Errores de validación", errors=error, status_code=400)
        return error_response(message=error, status_code=400)

    return success_response(data=product, message="Producto actualizado exitosamente.")


@product_controller.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """DELETE /api/products/<id> - Desactivar o eliminar producto (solo administrador)"""
    if not getattr(current_user, 'is_admin', False):
        return error_response(message="Acceso denegado. Se requieren permisos de administrador.", status_code=403)

    user_store_id = getattr(current_user, 'store_id', None)
    existing_product = ProductRepository.get_by_id(product_id)
    if not existing_product or not existing_product.is_active:
        return error_response(message="Producto no encontrado.", status_code=404)

    # P0-3 FIX: Validar que el producto pertenezca a la tienda del usuario
    if user_store_id and existing_product.store_id != user_store_id:
        return error_response(message="No tienes permiso para eliminar productos de otra tienda.", status_code=403)

    success, error = ProductService.delete_product(product_id)
    if error:
        return error_response(message=error, status_code=404)
    return success_response(message="Producto eliminado exitosamente.")


@product_controller.route('/categories', methods=['GET'])
def get_categories():
    """GET /api/categories - Listar categorías"""
    store_id = None
    if current_user and current_user.is_authenticated and hasattr(current_user, 'store_id'):
        store_id = current_user.store_id
    if not store_id:
        store_id = request.args.get('store_id', 1, type=int)

    categories = ProductService.get_categories(store_id=store_id)
    return success_response(data=categories, message="Categorías recuperadas exitosamente.")
