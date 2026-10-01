from flask import Blueprint, request
from dtos.product_dto import ProductCreateDTO, ProductUpdateDTO
from services.product_service import ProductService
from utilities.response_helper import success_response, error_response

product_controller = Blueprint('product_controller', __name__, url_prefix='/api')

@product_controller.route('/products', methods=['GET'])
def get_products():
    """
    GET /api/products?q=termino_busqueda
    Lista productos o busca por término.
    """
    query = request.args.get('q', '').strip()
    if query:
        products = ProductService.search_products(query)
    else:
        products = ProductService.get_all_products()
    return success_response(data=products, message="Productos recuperados exitosamente.")


@product_controller.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """GET /api/products/<id>"""
    product, error = ProductService.get_product_by_id(product_id)
    if error:
        return error_response(message=error, status_code=404)
    return success_response(data=product)


@product_controller.route('/products', methods=['POST'])
def create_product():
    """POST /api/products - Crear un nuevo producto"""
    data = request.get_json() or {}
    dto = ProductCreateDTO(
        name=data.get('name'),
        price=data.get('price'),
        category_id=data.get('category_id'),
        store_id=data.get('store_id', 1),
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
def update_product(product_id):
    """PUT /api/products/<id> - Actualizar producto"""
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
    product, error = ProductService.update_product(product_id, dto)
    if error:
        if isinstance(error, list):
            return error_response(message="Errores de validación", errors=error, status_code=400)
        return error_response(message=error, status_code=400)

    return success_response(data=product, message="Producto actualizado exitosamente.")


@product_controller.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """DELETE /api/products/<id> - Desactivar o eliminar producto"""
    success, error = ProductService.delete_product(product_id)
    if error:
        return error_response(message=error, status_code=404)
    return success_response(message="Producto eliminado exitosamente.")


@product_controller.route('/categories', methods=['GET'])
def get_categories():
    """GET /api/categories - Listar categorías"""
    categories = ProductService.get_categories()
    return success_response(data=categories, message="Categorías recuperadas exitosamente.")
