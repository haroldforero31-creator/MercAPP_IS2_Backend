from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
from datetime import datetime
import os, re, io, csv

# Configuramos las rutas para que Flask busque el HTML en la carpeta FRONTEND
base_dir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.abspath(os.path.join(base_dir, '..', 'MercAPP_IS2_Frontend'))
UPLOAD_DIR = os.path.join(base_dir, 'uploads')
os.makedirs(os.path.join(UPLOAD_DIR, 'products'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'categories'), exist_ok=True)

# Also ensure frontend static/images exist
STATIC_IMG_DIR = os.path.join(frontend_dir, 'static', 'images')
os.makedirs(os.path.join(STATIC_IMG_DIR, 'products'), exist_ok=True)
os.makedirs(os.path.join(STATIC_IMG_DIR, 'categories'), exist_ok=True)

app = Flask(__name__, 
            template_folder=os.path.join(frontend_dir, 'templates'),
            static_folder=os.path.join(frontend_dir, 'static'))

app.config['SECRET_KEY'] = 'sprint2-nueva-clave-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'mercapp.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.template_filter('cop')
def cop_filter(value):
    try:
        return f"${int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "$0"

def format_cop(value):
    if value is None:
        return '$0'
    return f"${int(value):,}".replace(',', '.')

def mix_color(color1, color2, weight=0.85):
    """Mix two hex colors."""
    if not color1 or not color1.startswith('#') or len(color1) != 7:
        return color1
    try:
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        if color2 == 'white':
            r2, g2, b2 = 255, 255, 255
        elif color2 == 'black':
            r2, g2, b2 = 0, 0, 0
        else:
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 * weight + r2 * (1 - weight))
        g = int(g1 * weight + g2 * (1 - weight))
        b = int(b1 * weight + b2 * (1 - weight))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return color1

def color_alpha(color, alpha=0.3):
    """Return rgba string from hex."""
    if not color or not color.startswith('#') or len(color) != 7:
        return color
    try:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    except Exception:
        return color

# ============================================================
# MODELS — Sprint 2 + Sprint 3: Tienda, Configuración, Categorías, Subcategorías, Productos, Auditoría
# ============================================================

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
    scale_mode = db.Column(db.String(10), default='manual')  # 'manual' or 'auto'
    printer_name = db.Column(db.String(200), default='')
    auto_print = db.Column(db.Boolean, default=True)
    auto_drawer = db.Column(db.Boolean, default=True)
    
    # Theme visual personalization
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
    status = db.Column(db.String(20), default='ACTIVO')  # ACTIVO, INACTIVO, BLOQUEADO
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

class AuditLog(db.Model):
    """Tabla de auditoría APPEND-ONLY: registra quién hizo qué y cuándo."""
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    severity = db.Column(db.String(20), default='INFO')
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='audit_logs', lazy=True)


# ============================================================
# USER LOADER & HELPERS
# ============================================================

@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    if user:
        return user
    return db.session.get(Customer, int(user_id))

def get_store_settings():
    """Obtener o crear la configuración de la tienda del usuario actual."""
    if not current_user.is_authenticated or not hasattr(current_user, 'store_id'):
        return None
    settings = StoreSettings.query.filter_by(store_id=current_user.store_id).first()
    if not settings:
        settings = StoreSettings(store_id=current_user.store_id, store_name=current_user.store.name if current_user.store else 'MercAPP')
        db.session.add(settings)
        db.session.commit()
    return settings

@app.context_processor
def inject_csrf():
    return dict(csrf_token=lambda: "")

@app.context_processor
def inject_globals():
    """Inyectar variables globales y tema dinámico que base.html espera."""
    global_settings = get_store_settings() if current_user.is_authenticated else None
    theme_vars = {}
    if global_settings:
        p = global_settings.theme_color_primary
        if p and p != 'default':
            theme_vars['primary'] = p
            theme_vars['primary_light'] = mix_color(p, 'white', 0.85)
            theme_vars['primary_dark'] = mix_color(p, 'black', 0.85)
            theme_vars['primary_glow'] = color_alpha(p, 0.3)
            
        a = global_settings.theme_color_accent
        if a and a != 'default':
            theme_vars['accent'] = a
            theme_vars['accent_light'] = mix_color(a, 'white', 0.85)
            theme_vars['accent_dark'] = mix_color(a, 'black', 0.85)
            
        bg = global_settings.theme_color_background
        if bg and bg != 'default':
            theme_vars['bg'] = bg
            theme_vars['bg_card'] = mix_color(bg, 'white', 0.92)
            theme_vars['bg_card_hover'] = mix_color(bg, 'white', 0.87)
            theme_vars['bg_input'] = mix_color(bg, 'white', 0.96)
            theme_vars['border'] = mix_color(bg, 'white', 0.80)
            
        btn_clear = global_settings.theme_btn_clear_color
        if btn_clear and btn_clear != 'default':
            theme_vars['btn_clear_color'] = btn_clear
            theme_vars['btn_clear_bg'] = color_alpha(btn_clear, 0.12)
            theme_vars['btn_clear_border'] = color_alpha(btn_clear, 0.30)
            theme_vars['btn_clear_hover_bg'] = btn_clear
            
        btn_charge = global_settings.theme_btn_charge_color
        if btn_charge and btn_charge != 'default':
            theme_vars['btn_charge_color'] = btn_charge
            theme_vars['btn_charge_bg_start'] = mix_color(btn_charge, 'black', 0.80)
            theme_vars['btn_charge_bg_end'] = btn_charge
            theme_vars['btn_charge_glow'] = color_alpha(btn_charge, 0.30)
            theme_vars['btn_charge_hover_bg_start'] = btn_charge
            theme_vars['btn_charge_hover_bg_end'] = mix_color(btn_charge, 'white', 0.80)
            theme_vars['btn_charge_hover_glow'] = color_alpha(btn_charge, 0.50)

    return dict(
        cashier_mode=False,
        active_cashier_name='',
        pending_orders_count=0,
        global_settings=global_settings,
        theme_vars=theme_vars
    )

def log_audit(action, description, user_id=None, severity='INFO'):
    """Registrar un evento de auditoría inmutable."""
    ip = request.remote_addr or '127.0.0.1'
    entry = AuditLog(
        user_id=user_id,
        action=action,
        description=description,
        ip_address=ip,
        severity=severity
    )
    db.session.add(entry)
    db.session.commit()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'avif', 'jfif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(file, product_name):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', product_name.lower())
        filename = f"{safe_name}_{int(datetime.now().timestamp())}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, 'products', filename)
        img = Image.open(file)
        img.thumbnail((400, 400))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(filepath, quality=85, optimize=True)
        return filename
    return None

def save_category_image(file, category_name):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', category_name.lower())
        filename = f"cat_{safe_name}_{int(datetime.now().timestamp())}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, 'categories', filename)
        img = Image.open(file)
        img.thumbnail((600, 400))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(filepath, quality=85, optimize=True)
        return filename
    return None

def validate_price(price_str):
    if not price_str:
        return None, 'El precio es obligatorio.'
    price_str = str(price_str).strip()
    if '.' in price_str or ',' in price_str:
        return None, 'El precio debe ser un número entero sin puntos ni comas (ej: 3500).'
    if not price_str.isdigit():
        return None, 'El precio solo puede contener números.'
    if len(price_str) > 9:
        return None, 'El precio no puede exceder los 9 dígitos (máximo $100.000.000 COP).'
    try:
        price = int(price_str)
    except (ValueError, OverflowError):
        return None, 'El precio ingresado es demasiado grande.'
    if price < 50:
        return None, 'El precio mínimo es $50 COP.'
    if price > 100000000:
        return None, 'El precio máximo es $100.000.000 COP.'
    return price, None


# ============================================================
# ROUTES — AUTHENTICATION
# ============================================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('settings'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('settings'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.status == 'BLOQUEADO':
                flash('Tu cuenta está bloqueada. Contacta al administrador.', 'error')
                log_audit('LOGIN_BLOCKED', f'Intento de login con cuenta bloqueada: {email}', user.id, 'WARNING')
                return render_template('inicio_sesion.html')
            
            user.failed_attempts = 0
            user.last_login = datetime.now()
            db.session.commit()
            login_user(user)
            log_audit('LOGIN', f'Inicio de sesión exitoso para {user.name} ({user.email})', user.id)
            return redirect(url_for('settings'))
        else:
            if user:
                user.failed_attempts += 1
                if user.failed_attempts >= 5:
                    user.status = 'BLOQUEADO'
                    log_audit('ACCOUNT_LOCKED', f'Cuenta bloqueada por {user.failed_attempts} intentos fallidos: {email}', user.id, 'CRITICAL')
                db.session.commit()
            log_audit('LOGIN_FAILED', f'Intento de login fallido para: {email}', user.id if user else None, 'WARNING')
            flash('Email o contraseña incorrectos.', 'error')
            
    return render_template('inicio_sesion.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        store_name = request.form.get('store_name', 'Mi Tienda')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Las contraseñas no coinciden.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('El correo ya está registrado.', 'error')
            return redirect(url_for('register'))
        
        new_store = Store(name=store_name)
        db.session.add(new_store)
        db.session.flush()
        
        # Crear configuración inicial de la tienda
        store_settings = StoreSettings(store_id=new_store.id, store_name=store_name)
        db.session.add(store_settings)
            
        new_user = User(store_id=new_store.id, name=name, email=email, is_admin=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        log_audit('REGISTER', f'Nuevo usuario registrado: {name} ({email}) - Tienda: {store_name}', new_user.id)
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
        
    return render_template('registro.html')

@app.route('/customer/login', endpoint='customer_login', methods=['GET', 'POST'])
def customer_login_view():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        customer = Customer.query.filter_by(email=email).first()
        
        if customer and customer.check_password(password):
            login_user(customer)
            return redirect(url_for('dashboard'))
        else:
            flash('Email o contraseña incorrectos.', 'error')
            
    return render_template('customer_login.html')

@app.route('/customer/register', endpoint='customer_register', methods=['GET', 'POST'])
def customer_register_view():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        password = request.form.get('password')
        
        if Customer.query.filter_by(email=email).first():
            flash('El correo ya está registrado.', 'error')
            return redirect(url_for('customer_register'))
            
        new_customer = Customer(name=name, email=email, phone=phone, address=address)
        new_customer.set_password(password)
        db.session.add(new_customer)
        db.session.commit()
        
        flash('Registro exitoso. Ahora puedes iniciar sesión como cliente.', 'success')
        return redirect(url_for('customer_login'))
        
    return render_template('customer_register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return redirect(url_for('settings'))

@app.route('/logout')
@login_required
def logout():
    user_name = current_user.name
    user_id = current_user.id if isinstance(current_user, User) else None
    if user_id:
        log_audit('LOGOUT', f'Cierre de sesión de {user_name}', user_id)
    logout_user()
    return redirect(url_for('login'))


# ============================================================
# ROUTES — SETTINGS / CENTRO DE CONTROL
# ============================================================

@app.route('/settings')
@login_required
def settings():
    """Centro de Control (Configuración General)."""
    return render_template('config_hub.html')

@app.route('/settings/store', methods=['GET', 'POST'])
@login_required
def settings_store():
    """Datos del Supermercado y Personalización Visual."""
    store = get_store_settings()
    
    if request.method == 'POST':
        store.store_name = request.form.get('store_name', 'MercAPP').strip()
        store.razon_social = request.form.get('razon_social', '').strip()
        store.nit = request.form.get('nit', '').strip()
        store.rut = request.form.get('rut', '').strip()
        store.regimen_tributario = request.form.get('regimen_tributario', '').strip()
        store.gran_contribuyente = request.form.get('gran_contribuyente', '').strip()
        store.agente_retencion = request.form.get('agente_retencion', '').strip()
        store.direccion = request.form.get('direccion', '').strip()
        store.telefono = request.form.get('telefono', '').strip()
        store.ciudad = request.form.get('ciudad', '').strip()
        store.resolucion_dian = request.form.get('resolucion_dian', '').strip()
        store.resolucion_fecha = request.form.get('resolucion_fecha', '').strip()
        store.rango_desde = request.form.get('rango_desde', '').strip()
        store.rango_hasta = request.form.get('rango_hasta', '').strip()
        store.mensaje_ticket = request.form.get('mensaje_ticket', '').strip()
        
        user_name = request.form.get('user_name', '').strip()
        if user_name and len(user_name) >= 2:
            current_user.name = user_name
        
        # Logo upload
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename and allowed_file(logo_file.filename):
            ext = logo_file.filename.rsplit('.', 1)[1].lower()
            logo_name = f"logo_store.{ext}"
            logo_path = os.path.join(STATIC_IMG_DIR, logo_name)
            img = Image.open(logo_file)
            img.thumbnail((300, 300))
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(logo_path, quality=90, optimize=True)
            store.logo = logo_name

        # QR upload
        qr_file = request.files.get('qr_transferencia')
        if qr_file and qr_file.filename and allowed_file(qr_file.filename):
            ext = qr_file.filename.rsplit('.', 1)[1].lower()
            qr_name = f"qr_transferencia_{int(datetime.now().timestamp())}.{ext}"
            qr_path = os.path.join(STATIC_IMG_DIR, qr_name)
            img = Image.open(qr_file)
            img.thumbnail((400, 400))
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(qr_path, quality=90, optimize=True)
            store.qr_transferencia = qr_name
        
        # Theme visual settings
        store.theme_color_primary = request.form.get('theme_color_primary', 'default').strip()
        store.theme_color_accent = request.form.get('theme_color_accent', 'default').strip()
        store.theme_color_background = request.form.get('theme_color_background', 'default').strip()
        store.theme_font_family = request.form.get('theme_font_family', 'default').strip()
        store.theme_font_size = request.form.get('theme_font_size', 'default').strip()
        store.theme_btn_clear_color = request.form.get('theme_btn_clear_color', 'default').strip()
        store.theme_btn_charge_color = request.form.get('theme_btn_charge_color', 'default').strip()
        
        db.session.commit()
        log_audit('STORE_SETTINGS_UPDATE', f'Configuración del supermercado actualizada: {store.store_name}', current_user.id)
        flash('Configuración guardada exitosamente.', 'success')
        return redirect(url_for('settings_store'))
    
    return render_template('configuracion.html', store=store)


# ============================================================
# ROUTES — PRODUCT MANAGEMENT (Sprint 2 & 3 Completo)
# ============================================================

@app.route('/products')
@login_required
def products():
    if not isinstance(current_user, User):
        flash('Acceso restringido.', 'error')
        return redirect(url_for('dashboard'))
    
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')
    
    query = Product.query.filter_by(store_id=current_user.store_id)
    
    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.barcode.ilike(f'%{search}%')
            )
        )
    
    if category_filter:
        query = query.filter_by(category_id=int(category_filter))
    
    products_list = query.order_by(Product.category_id, Product.name).all()
    categories = Category.query.filter_by(store_id=current_user.store_id).order_by(Category.display_order).all()
    
    return render_template('productos.html', products=products_list, categories=categories,
                           search=search, category_filter=category_filter)


@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def product_add():
    categories = Category.query.filter_by(store_id=current_user.store_id).order_by(Category.display_order).all()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        barcode = request.form.get('barcode', '').strip() or None
        plu_code = request.form.get('plu_code', '').strip() or None
        price = request.form.get('price', '0')
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id', '') or None
        stock = request.form.get('stock', '').strip()
        sell_by_weight = request.form.get('sell_by_weight') == 'on'
        weight_unit = request.form.get('weight_unit', 'kg')
        
        if not name or not category_id:
            flash('Nombre y categoría son obligatorios.', 'error')
            return render_template('formulario_producto.html', categories=categories, editing=False)
        
        # Validar precio para evitar números gigantescos / OverflowError
        price_int, price_err = validate_price(price)
        if price_err:
            flash(price_err, 'error')
            return render_template('formulario_producto.html', categories=categories, editing=False)
            
        # Validar código de barras
        if barcode:
            if len(barcode) > 50:
                flash('El código de barras no puede tener más de 50 caracteres.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=False)
            existing = Product.query.filter_by(store_id=current_user.store_id, barcode=barcode).first()
            if existing:
                flash(f'Ya existe un producto con el código de barras "{barcode}": {existing.name}', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=False)
                
        # Validar código PLU
        if plu_code:
            if len(plu_code) > 50:
                flash('El código PLU no puede tener más de 50 caracteres.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=False)
                
        # Validar stock
        stock_val = None
        if stock:
            if not stock.isdigit():
                flash('El stock debe ser un número entero.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=False)
            if len(stock) > 6 or int(stock) > 999999:
                flash('El stock no puede superar las 999.999 unidades.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=False)
            stock_val = int(stock)
            
        image_name = 'default_product.png'
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            saved = save_product_image(image_file, name)
            if saved:
                image_name = saved
        
        product = Product(
            store_id=current_user.store_id,
            name=name,
            barcode=barcode,
            plu_code=plu_code,
            price=price_int,
            category_id=int(category_id),
            subcategory_id=int(subcategory_id) if subcategory_id else None,
            image=image_name,
            has_barcode=True if barcode else False,
            sell_by_weight=sell_by_weight,
            weight_unit=weight_unit if sell_by_weight else 'kg',
            stock=stock_val
        )
        
        try:
            db.session.add(product)
            db.session.commit()
            log_audit('PRODUCT_CREATE', f'Producto creado: "{name}" (ID:{product.id}) - Precio: ${price_int:,} COP', current_user.id)
            flash(f'Producto "{name}" agregado exitosamente.', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el producto: valores fuera de rango permitido.', 'error')
            return render_template('formulario_producto.html', categories=categories, editing=False)
        
    return render_template('formulario_producto.html', categories=categories, editing=False)


@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    product = db.session.get(Product, product_id)
    if not product or product.store_id != current_user.store_id:
        flash('Producto no encontrado.', 'error')
        return redirect(url_for('products'))
    
    categories = Category.query.filter_by(store_id=current_user.store_id).order_by(Category.display_order).all()
    
    if request.method == 'POST':
        old_name = product.name
        old_price = product.price
        
        name = request.form.get('name', product.name).strip()
        barcode = request.form.get('barcode', '').strip() or None
        plu_code = request.form.get('plu_code', '').strip() or None
        price = request.form.get('price', str(product.price))
        category_id = int(request.form.get('category_id', product.category_id))
        sub_id = request.form.get('subcategory_id', '')
        stock_str = request.form.get('stock', '').strip()
        sell_by_weight = request.form.get('sell_by_weight') == 'on'
        weight_unit = request.form.get('weight_unit', 'kg')
        
        if not name:
            flash('El nombre del producto es obligatorio.', 'error')
            return render_template('formulario_producto.html', categories=categories, editing=True, product=product)

        # Validar precio
        price_int, price_err = validate_price(price)
        if price_err:
            flash(price_err, 'error')
            return render_template('formulario_producto.html', categories=categories, editing=True, product=product)

        # Validar código de barras
        if barcode:
            if len(barcode) > 50:
                flash('El código de barras no puede tener más de 50 caracteres.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=True, product=product)
            existing = Product.query.filter_by(store_id=current_user.store_id, barcode=barcode).first()
            if existing and existing.id != product.id:
                flash(f'Ya existe otro producto con el código de barras "{barcode}": {existing.name}', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=True, product=product)

        # Validar código PLU
        if plu_code:
            if len(plu_code) > 50:
                flash('El código PLU no puede tener más de 50 caracteres.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=True, product=product)

        # Validar stock
        stock_val = None
        if stock_str:
            if not stock_str.isdigit():
                flash('El stock debe ser un número entero.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=True, product=product)
            if len(stock_str) > 6 or int(stock_str) > 999999:
                flash('El stock no puede superar las 999.999 unidades.', 'error')
                return render_template('formulario_producto.html', categories=categories, editing=True, product=product)
            stock_val = int(stock_str)
        
        product.name = name
        product.barcode = barcode
        product.plu_code = plu_code
        product.has_barcode = True if barcode else False
        product.category_id = category_id
        product.subcategory_id = int(sub_id) if sub_id else None
        product.price = price_int
        product.sell_by_weight = sell_by_weight
        product.weight_unit = weight_unit if sell_by_weight else 'kg'
        product.stock = stock_val
        
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            saved = save_product_image(image_file, product.name)
            if saved:
                product.image = saved
        
        try:
            db.session.commit()
            changes = []
            if old_name != product.name:
                changes.append(f'nombre: "{old_name}" → "{product.name}"')
            if old_price != product.price:
                changes.append(f'precio: ${old_price:,} → ${product.price:,}')
            change_str = ', '.join(changes) if changes else 'datos actualizados'
            
            log_audit('PRODUCT_UPDATE', f'Producto editado (ID:{product.id}): {change_str}', current_user.id)
            flash(f'Producto "{product.name}" actualizado.', 'success')
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el producto: valores fuera de rango.', 'error')
            return render_template('formulario_producto.html', categories=categories, editing=True, product=product)
        
    return render_template('formulario_producto.html', categories=categories, editing=True, product=product)


@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    """Toggle activar/desactivar producto (Soft Delete conforme al botón de la interfaz)."""
    product = db.session.get(Product, product_id)
    if not product or product.store_id != current_user.store_id:
        flash('Producto no encontrado.', 'error')
        return redirect(url_for('products'))
    
    product.is_active = not product.is_active
    action_text = 'desactivado' if not product.is_active else 'reactivado'
    db.session.commit()
    
    log_audit('PRODUCT_TOGGLE', f'Producto {action_text}: "{product.name}" (ID:{product_id})', current_user.id, 'INFO')
    flash(f'Producto "{product.name}" {action_text} exitosamente.', 'success')
    return redirect(url_for('products'))


@app.route('/products/export')
@login_required
def products_export():
    """Exportar catálogo de productos a archivo CSV compatible con Excel."""
    categories_param = request.args.get('categories', '')
    query = Product.query.filter_by(store_id=current_user.store_id)
    
    if categories_param:
        try:
            cat_ids = [int(c.strip()) for c in categories_param.split(',') if c.strip()]
            if cat_ids:
                query = query.filter(Product.category_id.in_(cat_ids))
        except ValueError:
            pass
        
    products_list = query.order_by(Product.name).all()
    output = io.StringIO()
    output.write('\ufeff')  # BOM UTF-8 para Excel
    writer = csv.writer(output, delimiter=';')
    
    writer.writerow([
        'Nombre', 'CodigoBarras', 'CodigoPLU', 'Precio', 'Categoria', 
        'VentaPorPeso', 'UnidadPeso', 'Stock'
    ])
    
    for p in products_list:
        writer.writerow([
            p.name,
            p.barcode if p.barcode else '',
            p.plu_code if p.plu_code else '',
            p.price,
            p.category.name if p.category else '',
            'si' if p.sell_by_weight else 'no',
            p.weight_unit or 'kg',
            p.stock if p.stock is not None else ''
        ])
    
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=productos_mercapp_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8"
    return response


@app.route('/products/import', methods=['POST'])
@login_required
def products_import():
    """Importar inventario masivo desde archivo CSV."""
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo.', 'error')
        return redirect(url_for('products'))
    
    file = request.files['file']
    if not file or file.filename == '':
        flash('El archivo está vacío.', 'error')
        return redirect(url_for('products'))
    
    if not file.filename.lower().endswith('.csv'):
        flash('Solo se permiten archivos con extensión .CSV', 'error')
        return redirect(url_for('products'))
    
    try:
        content = file.stream.read().decode("utf-8-sig")
        stream = io.StringIO(content)
        dialect = csv.Sniffer().sniff(content[:2048], delimiters=';,')
        reader = csv.DictReader(stream, dialect=dialect)
        
        required_headers = ['Nombre', 'Precio', 'Categoria']
        for h in required_headers:
            if h not in reader.fieldnames:
                flash(f'Formato inválido. El CSV debe tener la columna "{h}".', 'error')
                return redirect(url_for('products'))
        
        created_count = 0
        updated_count = 0
        
        for row in reader:
            name = (row.get('Nombre') or '').strip()
            if not name:
                continue
            
            barcode = (row.get('CodigoBarras') or '').strip() or None
            plu_code = (row.get('CodigoPLU') or '').strip() or None
            price_str = (row.get('Precio') or '').strip()
            cat_name = (row.get('Categoria') or '').strip()
            
            # Categoría
            cat_id = None
            if cat_name:
                cat = Category.query.filter_by(store_id=current_user.store_id, name=cat_name).first()
                if not cat:
                    slug = re.sub(r'[^a-z0-9]', '_', cat_name.lower())
                    max_order = db.session.query(db.func.max(Category.display_order)).filter_by(store_id=current_user.store_id).scalar() or 0
                    cat = Category(store_id=current_user.store_id, name=cat_name, slug=slug, display_order=max_order + 1)
                    db.session.add(cat)
                    db.session.flush()
                cat_id = cat.id
            
            try:
                price = int(float(price_str))
            except:
                price = 0
                
            stock_str = (row.get('Stock') or '').strip()
            stock_val = int(float(stock_str)) if stock_str else None
            sell_by_weight = (row.get('VentaPorPeso') or '').lower() == 'si'
            weight_unit = (row.get('UnidadPeso') or 'kg').lower()
            if weight_unit not in ('kg', 'lb'):
                weight_unit = 'kg'
                
            product = None
            if barcode:
                product = Product.query.filter_by(store_id=current_user.store_id, barcode=barcode).first()
            
            if product:
                product.name = name
                product.price = price
                product.plu_code = plu_code
                if cat_id:
                    product.category_id = cat_id
                product.stock = stock_val
                product.sell_by_weight = sell_by_weight
                product.weight_unit = weight_unit
                updated_count += 1
            else:
                new_p = Product(
                    store_id=current_user.store_id,
                    name=name,
                    barcode=barcode,
                    plu_code=plu_code,
                    price=price,
                    category_id=cat_id or 1,
                    stock=stock_val,
                    sell_by_weight=sell_by_weight,
                    weight_unit=weight_unit,
                    has_barcode=True if barcode else False,
                    is_active=True
                )
                db.session.add(new_p)
                created_count += 1
                
        db.session.commit()
        log_audit('PRODUCTS_IMPORT', f'Importación masiva: {created_count} creados, {updated_count} actualizados', current_user.id)
        flash(f'¡Importación completada! Creados: {created_count}, Actualizados: {updated_count}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar el archivo CSV: {str(e)}', 'error')
        
    return redirect(url_for('products'))


@app.route('/api/products/bulk-price', methods=['POST'])
@login_required
def api_bulk_price():
    """Actualización masiva de precios seleccionados."""
    try:
        data = request.get_json() or {}
        product_ids = data.get('product_ids', [])
        new_price_str = str(data.get('new_price', ''))
        
        if not product_ids:
            return jsonify({'success': False, 'message': 'Debes seleccionar al menos un producto.'}), 400
            
        price, price_err = validate_price(new_price_str)
        if price_err:
            return jsonify({'success': False, 'message': price_err}), 400
            
        updated = 0
        for pid in product_ids:
            try:
                pid = int(pid)
            except (ValueError, TypeError):
                continue
            product = db.session.get(Product, pid)
            if product and product.store_id == current_user.store_id:
                product.price = price
                updated += 1
                
        db.session.commit()
        log_audit('BULK_PRICE_UPDATE', f'Actualización masiva de precio a {format_cop(price)} para {updated} productos', current_user.id)
        
        return jsonify({
            'success': True,
            'message': f'Precio actualizado a {format_cop(price)} en {updated} producto(s).',
            'updated_count': updated,
            'new_price': price,
            'new_price_formatted': format_cop(price)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ============================================================
# ROUTES — CATEGORY MANAGEMENT
# ============================================================

@app.route('/categories')
@login_required
def categories():
    cats = Category.query.filter_by(store_id=current_user.store_id).order_by(Category.display_order).all()
    return render_template('categorias.html', categories=cats)


@app.route('/categories/add', methods=['GET', 'POST'])
@login_required
def category_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        slug = re.sub(r'[^a-z0-9]', '_', name.lower())
        
        if not name:
            flash('El nombre es obligatorio.', 'error')
            return render_template('formulario_categoria.html', editing=False)
            
        max_order = db.session.query(db.func.max(Category.display_order)).filter_by(store_id=current_user.store_id).scalar() or 0
        
        image_name = 'default_category.png'
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            saved = save_category_image(image_file, name)
            if saved:
                image_name = saved
                
        cat = Category(
            store_id=current_user.store_id,
            name=name,
            slug=slug,
            description=description,
            display_order=max_order + 1,
            image=image_name
        )
                
        db.session.add(cat)
        db.session.commit()
        
        log_audit('CATEGORY_CREATE', f'Categoría creada: "{name}" (ID:{cat.id})', current_user.id)
        flash(f'Categoría "{name}" agregada exitosamente.', 'success')
        return redirect(url_for('categories'))
        
    return render_template('formulario_categoria.html', editing=False)


@app.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def category_edit(category_id):
    cat = db.session.get(Category, category_id)
    if not cat or cat.store_id != current_user.store_id:
        flash('Categoría no encontrada.', 'error')
        return redirect(url_for('categories'))
    
    if request.method == 'POST':
        old_name = cat.name
        cat.name = request.form.get('name', cat.name).strip()
        cat.description = request.form.get('description', '').strip()
        cat.slug = re.sub(r'[^a-z0-9]', '_', cat.name.lower())
        
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            saved = save_category_image(image_file, cat.name)
            if saved:
                cat.image = saved
        
        db.session.commit()
        
        log_audit('CATEGORY_UPDATE', f'Categoría editada (ID:{cat.id}): "{old_name}" → "{cat.name}"', current_user.id)
        flash(f'Categoría "{cat.name}" actualizada.', 'success')
        return redirect(url_for('categories'))
        
    return render_template('formulario_categoria.html', editing=True, category=cat)


@app.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def category_delete(category_id):
    cat = db.session.get(Category, category_id)
    if not cat or cat.store_id != current_user.store_id:
        flash('Categoría no encontrada.', 'error')
        return redirect(url_for('categories'))
    
    product_count = Product.query.filter_by(category_id=cat.id).count()
    if product_count > 0:
        flash(f'No se puede eliminar "{cat.name}" porque tiene {product_count} productos. Mueve o elimina los productos primero.', 'error')
        return redirect(url_for('categories'))
    
    cat_name = cat.name
    db.session.delete(cat)
    db.session.commit()
    
    log_audit('CATEGORY_DELETE', f'Categoría eliminada: "{cat_name}" (ID:{category_id})', current_user.id, 'WARNING')
    flash(f'Categoría "{cat_name}" eliminada.', 'success')
    return redirect(url_for('categories'))


@app.route('/api/categories/toggle-visibility', methods=['POST'])
@login_required
def api_toggle_category_visibility():
    """Mostrar/Ocultar categoría en la caja (POS)."""
    data = request.get_json() or {}
    cat_id = data.get('category_id')
    cat = db.session.get(Category, cat_id)
    if not cat or cat.store_id != current_user.store_id:
        return jsonify({'success': False, 'message': 'Categoría no encontrada.'}), 404
    cat.visible_in_pos = not cat.visible_in_pos
    db.session.commit()
    log_audit('CATEGORY_VISIBILITY', f'Visibilidad de categoría "{cat.name}" cambiada a {"Visible" if cat.visible_in_pos else "Oculta"}', current_user.id)
    return jsonify({'success': True, 'visible': cat.visible_in_pos})


@app.route('/api/categories/reorder', methods=['POST'])
@login_required
def api_reorder_categories():
    """Reordenar categorías subiendo o bajando."""
    data = request.get_json() or {}
    cat_id = data.get('category_id')
    direction = data.get('direction')
    
    cats = Category.query.filter_by(store_id=current_user.store_id).order_by(Category.display_order).all()
    idx = next((i for i, c in enumerate(cats) if c.id == cat_id), None)
    if idx is None:
        return jsonify({'success': False, 'message': 'Categoría no encontrada.'}), 404
        
    if direction == 'up' and idx > 0:
        cats[idx].display_order, cats[idx-1].display_order = cats[idx-1].display_order, cats[idx].display_order
    elif direction == 'down' and idx < len(cats) - 1:
        cats[idx].display_order, cats[idx+1].display_order = cats[idx+1].display_order, cats[idx].display_order
    else:
        return jsonify({'success': False, 'message': 'No se puede mover más.'}), 400
        
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/subcategories/<int:category_id>')
@login_required
def api_subcategories(category_id):
    subs = Subcategory.query.filter_by(store_id=current_user.store_id, category_id=category_id).order_by(Subcategory.display_order).all()
    return jsonify({
        'subcategories': [{'id': s.id, 'name': s.name} for s in subs]
    })


# ============================================================
# ROUTES — AUDIT LOG
# ============================================================

@app.route('/audit')
@login_required
def audit():
    if not isinstance(current_user, User) or not current_user.is_admin:
        flash('Acceso restringido a administradores.', 'error')
        return redirect(url_for('products'))
    
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).all()
    
    session_actions = ['LOGIN', 'LOGOUT', 'REGISTER', 'LOGIN_FAILED', 'LOGIN_BLOCKED', 'ACCOUNT_LOCKED']
    session_count = sum(1 for l in logs if l.action in session_actions)
    inventory_count = sum(1 for l in logs if l.action not in session_actions)
    
    return render_template('auditoria.html', logs=logs, session_count=session_count, inventory_count=inventory_count)


# ============================================================
# ROUTES — SERVE UPLOADED & STATIC IMAGES
# ============================================================

@app.route('/user_images/<path:filename>')
def user_images(filename):
    """Servir imágenes subidas o por defecto con fallback."""
    # 1. Probar en uploads
    upload_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(upload_path):
        return send_from_directory(UPLOAD_DIR, filename)
    
    # 2. Probar en static/images
    static_img_path = os.path.join(STATIC_IMG_DIR, filename)
    if os.path.exists(static_img_path):
        return send_from_directory(STATIC_IMG_DIR, filename)
        
    # 3. Fallback en raíz de uploads
    return send_from_directory(UPLOAD_DIR, filename)


# ============================================================
# ROUTES — STUBS for features to come in subsequent sprints
# ============================================================

@app.route('/pos')
@login_required
def pos():
    return redirect(url_for('settings'))

@app.route('/orders')
@login_required
def orders():
    return redirect(url_for('settings'))

@app.route('/sales-history')
@login_required
def sales_history():
    return redirect(url_for('settings'))

@app.route('/sessions')
@login_required
def session_history():
    return redirect(url_for('settings'))

@app.route('/debts')
@login_required
def debts():
    return redirect(url_for('settings'))

@app.route('/cashiers')
@login_required
def cashiers():
    return redirect(url_for('settings'))

@app.route('/settings/hardware')
@login_required
def settings_hardware():
    flash('El módulo de Hardware estará disponible en el siguiente sprint.', 'info')
    return redirect(url_for('settings'))


# ============================================================
# STARTUP
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
