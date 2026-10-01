from datetime import datetime
from models.database import db

class Category(db.Model):
    __tablename__ = 'categoria'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200), default='default_category.png')
    description = db.Column(db.String(200))
    display_order = db.Column(db.Integer, default=0)
    visible_in_pos = db.Column(db.Boolean, default=True)
    
    subcategories = db.relationship('Subcategory', backref='category', lazy=True, cascade='all, delete-orphan')
    products = db.relationship('Product', backref='category', lazy=True)


class Subcategory(db.Model):
    __tablename__ = 'subcategoria'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    image = db.Column(db.String(200), default='default_subcategory.png')
    display_order = db.Column(db.Integer, default=0)
    
    products = db.relationship('Product', backref='subcategory', lazy=True)


class Product(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    barcode = db.Column(db.String(60), nullable=True)
    price = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategoria.id'), nullable=True)
    image = db.Column(db.String(200), default='default_product.png')
    has_barcode = db.Column(db.Boolean, default=False)
    stock = db.Column(db.Integer, nullable=True)
    sell_by_weight = db.Column(db.Boolean, default=False)
    weight_unit = db.Column(db.String(5), default='kg')  # 'kg' or 'lb'
    plu_code = db.Column(db.String(60), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
