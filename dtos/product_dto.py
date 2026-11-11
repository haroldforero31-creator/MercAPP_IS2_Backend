class ProductCreateDTO:
    """DTO para crear un producto en el catálogo."""
    def __init__(self, name, price, category_id, store_id=1, barcode=None, subcategory_id=None,
                 stock=0, sell_by_weight=False, weight_unit='kg', plu_code=None, image='default_product.png'):
        self.name = name.strip() if name else ""
        self.price = int(price) if price is not None else 0
        self.category_id = int(category_id) if category_id else None
        self.store_id = int(store_id) if store_id else 1
        self.barcode = barcode.strip() if barcode else None
        self.subcategory_id = int(subcategory_id) if subcategory_id else None
        self.stock = int(stock) if stock is not None else 0
        self.sell_by_weight = bool(sell_by_weight)
        self.weight_unit = weight_unit if weight_unit in ('kg', 'lb') else 'kg'
        self.plu_code = plu_code.strip() if plu_code else None
        self.image = image or 'default_product.png'

    def validate(self):
        errors = []
        if not self.name or len(self.name) < 2:
            errors.append("El nombre del producto es obligatorio y debe tener al menos 2 caracteres.")
        if self.price < 0:
            errors.append("El precio no puede ser negativo.")
        if not self.category_id:
            errors.append("Debe asociar el producto a una categoría válida.")
        return errors


class ProductUpdateDTO:
    """DTO para actualizar un producto."""
    def __init__(self, name=None, price=None, category_id=None, subcategory_id=None,
                 barcode=None, stock=None, sell_by_weight=None, weight_unit=None, plu_code=None, is_active=None):
        self.name = name.strip() if name is not None else None
        self.price = int(price) if price is not None else None
        self.category_id = int(category_id) if category_id is not None else None
        self.subcategory_id = int(subcategory_id) if subcategory_id is not None else None
        self.barcode = barcode.strip() if barcode is not None else None
        self.stock = int(stock) if stock is not None else None
        self.sell_by_weight = bool(sell_by_weight) if sell_by_weight is not None else None
        self.weight_unit = weight_unit if weight_unit is not None else None
        self.plu_code = plu_code.strip() if plu_code is not None else None
        self.is_active = bool(is_active) if is_active is not None else None

    def validate(self):
        errors = []
        if self.name is not None and len(self.name) < 2:
            errors.append("El nombre del producto debe tener al menos 2 caracteres.")
        if self.price is not None and self.price < 0:
            errors.append("El precio no puede ser negativo.")
        return errors


class ProductResponseDTO:
    """DTO de salida para productos."""
    @staticmethod
    def from_model(p):
        if not p:
            return None
        return {
            "id": p.id,
            "name": p.name,
            "barcode": p.barcode,
            "price": p.price,
            "stock": p.stock,
            "category_id": p.category_id,
            "category_name": p.category.name if p.category else None,
            "subcategory_id": p.subcategory_id,
            "subcategory_name": p.subcategory.name if p.subcategory else None,
            "image": p.image,
            "sell_by_weight": p.sell_by_weight,
            "weight_unit": p.weight_unit,
            "plu_code": p.plu_code,
            "is_active": p.is_active,
            "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None
        }

    @staticmethod
    def from_model_list(products):
        return [ProductResponseDTO.from_model(p) for p in products]


class CategoryDTO:
    """DTO para categorías."""
    @staticmethod
    def from_model(c):
        if not c:
            return None
        return {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "image": c.image,
            "description": c.description,
            "display_order": c.display_order,
            "visible_in_pos": c.visible_in_pos,
            "subcategories_count": len(c.subcategories) if c.subcategories else 0,
            "products_count": len(c.products) if c.products else 0
        }

    @staticmethod
    def from_model_list(categories):
        return [CategoryDTO.from_model(c) for c in categories]
