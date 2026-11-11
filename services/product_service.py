from repositories.product_repository import ProductRepository
from dtos.product_dto import ProductCreateDTO, ProductUpdateDTO, ProductResponseDTO, CategoryDTO

class ProductService:
    """
    Capa de Servicio para Catálogo de Productos y Categorías:
    Aplica reglas de negocio (ej. unicidad de código de barras, stock).
    """

    @staticmethod
    def get_all_products(store_id: int = 1):
        products = ProductRepository.get_all(store_id)
        return ProductResponseDTO.from_model_list(products)

    @staticmethod
    def get_product_by_id(product_id: int):
        product = ProductRepository.get_by_id(product_id)
        if not product or not product.is_active:
            return None, "Producto no encontrado."
        return ProductResponseDTO.from_model(product), None

    @staticmethod
    def search_products(term: str, store_id: int = 1):
        if not term:
            return ProductService.get_all_products(store_id)
        results = ProductRepository.search(term, store_id)
        return ProductResponseDTO.from_model_list(results)

    @staticmethod
    def create_product(dto: ProductCreateDTO):
        validation_errors = dto.validate()
        if validation_errors:
            return None, validation_errors

        # Regla: Si tiene código de barras, verificar que no esté repetido en la tienda
        if dto.barcode:
            existing = ProductRepository.get_by_barcode(dto.barcode, dto.store_id)
            if existing:
                return None, f"El código de barras '{dto.barcode}' ya está asignado al producto '{existing.name}'."

        category = ProductRepository.get_category_by_id(dto.category_id)
        if not category:
            return None, "La categoría especificada no existe."

        nuevo = ProductRepository.create(
            name=dto.name,
            price=dto.price,
            category_id=dto.category_id,
            store_id=dto.store_id,
            barcode=dto.barcode,
            subcategory_id=dto.subcategory_id,
            stock=dto.stock,
            sell_by_weight=dto.sell_by_weight,
            weight_unit=dto.weight_unit,
            plu_code=dto.plu_code,
            image=dto.image
        )
        return ProductResponseDTO.from_model(nuevo), None

    @staticmethod
    def update_product(product_id: int, dto: ProductUpdateDTO, store_id: int = 1):
        product = ProductRepository.get_by_id(product_id)
        if not product or not product.is_active:
            return None, "Producto no encontrado."

        validation_errors = dto.validate()
        if validation_errors:
            return None, validation_errors

        if dto.barcode and dto.barcode != product.barcode:
            existing = ProductRepository.get_by_barcode(dto.barcode, store_id)
            if existing and existing.id != product.id:
                return None, f"El código de barras '{dto.barcode}' ya está en uso."

        update_fields = {}
        for attr in ['name', 'price', 'category_id', 'subcategory_id', 'barcode',
                     'stock', 'sell_by_weight', 'weight_unit', 'plu_code', 'is_active']:
            val = getattr(dto, attr)
            if val is not None:
                update_fields[attr] = val

        updated = ProductRepository.update(product, **update_fields)
        return ProductResponseDTO.from_model(updated), None

    @staticmethod
    def delete_product(product_id: int):
        product = ProductRepository.get_by_id(product_id)
        if not product or not product.is_active:
            return False, "Producto no encontrado."

        ProductRepository.delete(product, soft_delete=True)
        return True, None

    @staticmethod
    def get_categories(store_id: int = 1):
        categories = ProductRepository.get_categories(store_id)
        return CategoryDTO.from_model_list(categories)
