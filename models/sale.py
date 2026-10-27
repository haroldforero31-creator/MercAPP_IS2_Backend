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
    email = db.Column(db.String(120), nullable=True)
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

    @property
    def last_activity_date(self):
        """Fecha del último abono o, si no hay abonos, de la deuda más antigua pendiente."""
        if self.payments:
            return max(p.payment_date for p in self.payments)
        pending = [cs for cs in self.credit_sales if cs.status == 'pendiente']
        if pending:
            return min(cs.created_at for cs in pending)
        return self.created_at

    @property
    def days_without_payment(self):
        """Días transcurridos sin hacer al menos un abono a la deuda pendiente."""
        if self.total_debt <= 0:
            return 0
        now = datetime.now()
        last_date = self.last_activity_date
        if last_date:
            return max(0, (now - last_date).days)
        return 0

    @property
    def is_blocked(self):
        """Bloqueado si tiene deuda y lleva 60 días (2 meses) o más sin abonar."""
        if self.total_debt <= 0:
            return False
        return self.days_without_payment >= 60


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


class Order(db.Model):
    """Storefront Delivery/Pickup Orders."""
    __tablename__ = 'pedido'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.String(200), nullable=True)
    order_type = db.Column(db.String(20), default='domicilio')    # 'domicilio' o 'recoger'
    payment_method = db.Column(db.String(20), default='efectivo')
    delivery_cost = db.Column(db.Integer, default=0)
    subtotal = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), default='pendiente')        # 'pendiente', 'confirmado', 'completado', 'cancelado'
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('OrderNotification', backref='order', lazy=True, cascade='all, delete-orphan')
    sale = db.relationship('Sale', backref='linked_order', lazy=True)
    store = db.relationship('Store', backref='orders', lazy=True)
    customer = db.relationship('Customer', backref='orders', lazy=True)


class OrderItem(db.Model):
    """Items inside a customer Order."""
    __tablename__ = 'detalle_pedido'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)
    weight_grams = db.Column(db.Integer, nullable=True)
    weight_unit = db.Column(db.String(5), nullable=True)
    product = db.relationship('Product', backref='order_items_rel')


class OrderNotification(db.Model):
    """Internal notifications sent by Admin to Customer regarding an order."""
    __tablename__ = 'notificacion_pedido'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class EmailQueue(db.Model):
    """Cola de correos salientes con soporte de reintento automático offline/online."""
    __tablename__ = 'cola_correos'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, nullable=True)
    recipient = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_body = db.Column(db.Text, nullable=False)
    email_type = db.Column(db.String(50), default='cierre_caja')
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    attempts = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    sent_at = db.Column(db.DateTime, nullable=True)


