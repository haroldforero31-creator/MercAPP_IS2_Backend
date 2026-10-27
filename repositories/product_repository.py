from models.database import db
from models.product import Product, Category, Subcategory

class ProductRepository:
    """
    Capa de Repositorio de Productos y Categorías:
    Maneja el acceso a base de datos para el catálogo.
    """

    @staticmethod
    def get_all(store_id: int = 1):
        return Product.query.filter_by(store_id=store_id, is_active=True).all()

    @staticmethod
    def get_by_id(product_id: int):
        return Product.query.get(product_id)

    @staticmethod
    def get_by_barcode(barcode: str, store_id: int = 1):
        if not barcode:
            return None
        return Product.query.filter_by(store_id=store_id, barcode=barcode.strip(), is_active=True).first()

    @staticmethod
    def search(search_term: str, store_id: int = 1):
        term = f"%{search_term.strip()}%"
        return Product.query.filter(
            Product.store_id == store_id,
            Product.is_active == True,
            (Product.name.ilike(term) | Product.barcode.ilike(term) | Product.plu_code.ilike(term))
        ).all()

    @staticmethod
    def create(name, price, category_id, store_id=1, barcode=None, subcategory_id=None,
               stock=0, sell_by_weight=False, weight_unit='kg', plu_code=None, image='default_product.png'):
        has_barcode = bool(barcode)
        product = Product(
            name=name,
            price=price,
            category_id=category_id,
            store_id=store_id,
            barcode=barcode,
            subcategory_id=subcategory_id,
            stock=stock,
            sell_by_weight=sell_by_weight,
            weight_unit=weight_unit,
            plu_code=plu_code,
            image=image,
            has_barcode=has_barcode,
            is_active=True
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update(product: Product, **kwargs):
        for field, value in kwargs.items():
            if hasattr(product, field) and value is not None:
                setattr(product, field, value)
        db.session.commit()
        return product

    @staticmethod
    def delete(product: Product, soft_delete: bool = True):
        if soft_delete:
            product.is_active = False
        else:
            db.session.delete(product)
        db.session.commit()

    # --- Categorías ---
    @staticmethod
    def get_categories(store_id: int = 1):
        return Category.query.filter_by(store_id=store_id).order_by(Category.display_order.asc()).all()

    @staticmethod
    def get_category_by_id(category_id: int):
        return Category.query.get(category_id)
