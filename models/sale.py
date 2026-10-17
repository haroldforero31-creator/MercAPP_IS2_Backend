from datetime import datetime
from models.database import db

class CashSession(db.Model):
    __tablename__ = 'sesion_caja'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.now)
    closed_at = db.Column(db.DateTime, nullable=True)
    base_amount = db.Column(db.Integer, nullable=False, default=0)
    cash_sales = db.Column(db.Integer, default=0)
    card_sales = db.Column(db.Integer, default=0)
    transfer_sales = db.Column(db.Integer, default=0)
    expected_cash = db.Column(db.Integer, default=0)
    actual_cash = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='abierta')  # abierta, cerrada
    sales = db.relationship('Sale', backref='session', lazy=True)


class Sale(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    cash_session_id = db.Column(db.Integer, db.ForeignKey('sesion_caja.id'), nullable=True)
    credit_client_id = db.Column(db.Integer, db.ForeignKey('cliente_credito.id'), nullable=True)
    receipt_number = db.Column(db.String(30), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.now)
    subtotal = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # efectivo, tarjeta, transferencia, fiado, mixto
    amount_received = db.Column(db.Integer, default=0)
    change_given = db.Column(db.Integer, default=0)
    payment_ref = db.Column(db.String(100), nullable=True)
    amount_cash = db.Column(db.Integer, default=0, nullable=True)
    amount_card = db.Column(db.Integer, default=0, nullable=True)
    amount_transfer = db.Column(db.Integer, default=0, nullable=True)
    status = db.Column(db.String(20), default='completada')  # completada, anulada
    cashier = db.relationship('User', backref='sales', foreign_keys=[user_id], lazy=True)
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items)


class SaleItem(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)
    weight_grams = db.Column(db.Integer, nullable=True)
    weight_unit = db.Column(db.String(5), nullable=True)
    product = db.relationship('Product', backref='sale_items')


class CreditClient(db.Model):
    """Clientes que compran a crédito (fiado)."""
    __tablename__ = 'cliente_credito'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    credit_sales = db.relationship('CreditSale', backref='client', lazy=True)
    payments = db.relationship('CreditPayment', backref='client', lazy=True)
    store = db.relationship('Store', backref='credit_clients')

    @property
    def total_debt(self):
        return sum(cs.balance for cs in self.credit_sales if cs.status == 'pendiente')

    @property
    def total_purchased(self):
        return sum(cs.amount for cs in self.credit_sales)

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments)

    @property
    def debt_status(self):
        return 'pagado' if self.total_debt <= 0 else 'pendiente'


class CreditSale(db.Model):
    """Venta fiada ligada a un cliente."""
    __tablename__ = 'venta_credito'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('cliente_credito.id'), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pendiente')  # pendiente, pagado
    created_at = db.Column(db.DateTime, default=datetime.now)
    sale = db.relationship('Sale', backref='credit_sale_record')


class CreditPayment(db.Model):
    """Abono a la deuda de fiado."""
    __tablename__ = 'pago_credito'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('cliente_credito.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(20), default='efectivo')
    payment_date = db.Column(db.DateTime, default=datetime.now)
    notes = db.Column(db.String(200), nullable=True)
