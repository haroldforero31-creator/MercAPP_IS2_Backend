from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db

class Supplier(UserMixin, db.Model):
    """Proveedor / Distribuidor mayorista vinculado a una tienda en MercAPP."""
    __tablename__ = 'proveedor'
    
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(100), nullable=True)
    nit = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    category_type = db.Column(db.String(100), default='General')
    payment_terms_days = db.Column(db.Integer, default=30)
    credit_limit = db.Column(db.Integer, default=10000000)
    total_debt = db.Column(db.Integer, default=0)
    password_hash = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='ACTIVO')
    created_at = db.Column(db.DateTime, default=datetime.now)

    store = db.relationship('Store', backref=db.backref('suppliers', lazy=True))
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True, cascade='all, delete-orphan')
    invoices = db.relationship('SupplierInvoice', backref='supplier', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"supplier_{self.id}"

    @property
    def is_admin(self):
        return False


class PurchaseOrder(db.Model):
    """Orden de Compra / Pedido de reabastecimiento que el negocio hace a su proveedor."""
    __tablename__ = 'orden_compra'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    order_number = db.Column(db.String(50), nullable=False, unique=True)
    status = db.Column(db.String(30), default='PENDIENTE')  # PENDIENTE, CONFIRMADA, EN_CAMINO, ENTREGADA, CANCELADA
    total_estimated = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, nullable=True)
    expected_delivery = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    store = db.relationship('Store', backref=db.backref('purchase_orders', lazy=True))
    items = db.relationship('PurchaseOrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class PurchaseOrderItem(db.Model):
    """Detalle de productos solicitados en una Orden de Compra."""
    __tablename__ = 'orden_compra_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orden_compra.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False, default=1)
    quantity_received = db.Column(db.Integer, default=0)
    unit_cost = db.Column(db.Integer, default=0)
    subtotal = db.Column(db.Integer, default=0)

    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))


class SupplierInvoice(db.Model):
    """Factura / Remisión de Proveedor — Control de Cuentas por Pagar del Supermercado."""
    __tablename__ = 'factura_proveedor'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    invoice_number = db.Column(db.String(50), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.now)
    due_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Integer, nullable=False)
    paid_amount = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='PENDIENTE')  # PENDIENTE, PAGADA_PARCIAL, PAGADA, VENCIDA
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    store = db.relationship('Store', backref=db.backref('supplier_invoices', lazy=True))

    @property
    def balance(self):
        return max(0, (self.total_amount or 0) - (self.paid_amount or 0))
