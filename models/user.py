from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db

class Store(db.Model):
    __tablename__ = 'tienda'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    
    users = db.relationship('User', backref='store', lazy=True)
    categories = db.relationship('Category', backref='store', lazy=True)
    products = db.relationship('Product', backref='store', lazy=True)
    settings = db.relationship('StoreSettings', backref='store', lazy=True)


class StoreSettings(db.Model):
    __tablename__ = 'configuracion_tienda'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    store_name = db.Column(db.String(100), default='MercAPP')
    logo = db.Column(db.String(200), default='logo.png')
    qr_transferencia = db.Column(db.String(200), default='')
    razon_social = db.Column(db.String(200), default='MercAPP S.A.S')
    nit = db.Column(db.String(20), default='000.000.000-0')
    rut = db.Column(db.String(30), default='')
    regimen_tributario = db.Column(db.String(100), default='No responsable de IVA')
    gran_contribuyente = db.Column(db.String(100), default='')
    agente_retencion = db.Column(db.String(100), default='')
    direccion = db.Column(db.String(200), default='')
    telefono = db.Column(db.String(20), default='')
    ciudad = db.Column(db.String(100), default='')
    resolucion_dian = db.Column(db.String(100), default='')
    resolucion_fecha = db.Column(db.String(50), default='')
    rango_desde = db.Column(db.String(30), default='MRC-0001')
    rango_hasta = db.Column(db.String(30), default='MRC-9999')
    mensaje_ticket = db.Column(db.String(200), default='¡Gracias por su compra!')
    scale_mode = db.Column(db.String(10), default='manual')
    printer_name = db.Column(db.String(200), default='')
    auto_print = db.Column(db.Boolean, default=True)
    auto_drawer = db.Column(db.Boolean, default=True)
    theme_color_primary = db.Column(db.String(20), default='default')
    theme_color_accent = db.Column(db.String(20), default='default')
    theme_color_background = db.Column(db.String(20), default='default')
    theme_font_family = db.Column(db.String(50), default='default')
    theme_font_size = db.Column(db.String(15), default='default')
    theme_btn_clear_color = db.Column(db.String(20), default='default')
    theme_btn_charge_color = db.Column(db.String(20), default='default')


class User(UserMixin, db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(20), default='ACTIVO')
    failed_attempts = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Customer(UserMixin, db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    password_hash = db.Column(db.String(255))
    is_admin = False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class AuditLog(db.Model):
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    severity = db.Column(db.String(20), default='INFO')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='audit_logs', lazy=True)
