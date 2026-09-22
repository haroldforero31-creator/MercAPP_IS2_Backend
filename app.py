from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, re

# Configuramos las rutas para que Flask busque el HTML en la carpeta FRONTEND
base_dir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.abspath(os.path.join(base_dir, '..', 'MercAPP_IS2_Frontend'))
UPLOAD_DIR = os.path.join(base_dir, 'uploads')
os.makedirs(os.path.join(UPLOAD_DIR, 'products'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, 'categories'), exist_ok=True)

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

# ============================================================
# MODELS — Sprint 2: Roles, Estados, Auditoría, Productos, Categorías
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
    # Necesitamos diferenciar Customer de User en el user_loader
    is_admin = False  # Property para compatibilidad con base.html

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
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('tienda.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    barcode = db.Column(db.String(50), nullable=True)
    price = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    image = db.Column(db.String(200), default='default_product.png')
    stock = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class AuditLog(db.Model):
    """Tabla de auditoría APPEND-ONLY: registra quién hizo qué y cuándo."""
    __tablename__ = 'auditoria'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # LOGIN, LOGOUT, REGISTER, LOGIN_FAILED, PRODUCT_CREATE, etc.
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    severity = db.Column(db.String(20), default='INFO')  # INFO, WARNING, CRITICAL
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

@app.context_processor
def inject_csrf():
    return dict(csrf_token=lambda: "")

@app.context_processor
def inject_globals():
    """Inyectar variables globales que base.html espera."""
    return dict(
        cashier_mode=False,
        active_cashier_name='',
        pending_orders_count=0
    )

def log_audit(action, description, user_id=None, severity='INFO'):
    """Función auxiliar para registrar un evento de auditoría."""
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


# ============================================================
# ROUTES — AUTHENTICATION (Sprint 1 - ya funcional)
# ============================================================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
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
            return redirect(url_for('dashboard'))
        else:
            # Registrar intento fallido
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
        
        # Crear tienda y usuario administrador
        new_store = Store(name=store_name)
        db.session.add(new_store)
        db.session.flush()  # Obtener el ID de la tienda
            
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
    return redirect(url_for('products'))

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
# ROUTES — PRODUCT MANAGEMENT (Sprint 2 - PB4 y PB6)
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
        price = request.form.get('price', '0')
        category_id = request.form.get('category_id')
        stock = request.form.get('stock', '')
        
        if not name or not category_id:
            flash('Nombre y categoría son obligatorios.', 'error')
            return render_template('formulario_producto.html', categories=categories, editing=False)
        
        try:
            price_int = int(price)
        except ValueError:
            price_int = 0
        
        product = Product(
            store_id=current_user.store_id,
            name=name,
            barcode=barcode,
            price=price_int,
            category_id=int(category_id),
            stock=int(stock) if stock else None
        )
        
        # Handle image upload
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            safe_name = re.sub(r'[^a-z0-9]', '_', name.lower()) + '_' + str(int(datetime.now().timestamp()))
            ext = image_file.filename.rsplit('.', 1)[-1].lower() if '.' in image_file.filename else 'jpg'
            img_name = f"{safe_name}.{ext}"
            image_file.save(os.path.join(UPLOAD_DIR, 'products', img_name))
            product.image = img_name
        
        db.session.add(product)
        db.session.commit()
        
        log_audit('PRODUCT_CREATE', f'Producto creado: "{name}" (ID:{product.id}) - Precio: ${price_int:,} COP', current_user.id)
        flash(f'Producto "{name}" agregado exitosamente.', 'success')
        return redirect(url_for('products'))
        
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
        
        product.name = request.form.get('name', product.name).strip()
        product.barcode = request.form.get('barcode', '').strip() or None
        product.category_id = int(request.form.get('category_id', product.category_id))
        
        try:
            product.price = int(request.form.get('price', product.price))
        except ValueError:
            pass
        
        stock_val = request.form.get('stock', '')
        product.stock = int(stock_val) if stock_val else None
        
        # Handle image upload
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            safe_name = re.sub(r'[^a-z0-9]', '_', product.name.lower()) + '_' + str(int(datetime.now().timestamp()))
            ext = image_file.filename.rsplit('.', 1)[-1].lower() if '.' in image_file.filename else 'jpg'
            img_name = f"{safe_name}.{ext}"
            image_file.save(os.path.join(UPLOAD_DIR, 'products', img_name))
            product.image = img_name
        
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
        
    return render_template('formulario_producto.html', categories=categories, editing=True, product=product)


@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    product = db.session.get(Product, product_id)
    if not product or product.store_id != current_user.store_id:
        flash('Producto no encontrado.', 'error')
        return redirect(url_for('products'))
    
    product_name = product.name
    db.session.delete(product)
    db.session.commit()
    
    log_audit('PRODUCT_DELETE', f'Producto eliminado: "{product_name}" (ID:{product_id})', current_user.id, 'WARNING')
    flash(f'Producto "{product_name}" eliminado.', 'success')
    return redirect(url_for('products'))


# ============================================================
# ROUTES — CATEGORY MANAGEMENT (Sprint 2 - PB5)
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
        
        cat = Category(
            store_id=current_user.store_id,
            name=name,
            slug=slug,
            description=description,
            display_order=max_order + 1,
            image='default_category.png'
        )
        
        # Handle image
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            safe_name = re.sub(r'[^a-z0-9]', '_', name.lower()) + '_' + str(int(datetime.now().timestamp()))
            ext = image_file.filename.rsplit('.', 1)[-1].lower() if '.' in image_file.filename else 'jpg'
            img_name = f"{safe_name}.{ext}"
            image_file.save(os.path.join(UPLOAD_DIR, 'categories', img_name))
            cat.image = img_name
                
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
        
        # Handle image
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            safe_name = re.sub(r'[^a-z0-9]', '_', cat.name.lower()) + '_' + str(int(datetime.now().timestamp()))
            ext = image_file.filename.rsplit('.', 1)[-1].lower() if '.' in image_file.filename else 'jpg'
            img_name = f"{safe_name}.{ext}"
            image_file.save(os.path.join(UPLOAD_DIR, 'categories', img_name))
            cat.image = img_name
        
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


# ============================================================
# ROUTES — AUDIT LOG (Sprint 2 - Requerimiento del Profesor)
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
# ROUTES — SERVE UPLOADED IMAGES
# ============================================================

@app.route('/uploads/<path:filename>')
def user_images(filename):
    """Servir imágenes subidas desde el directorio de uploads."""
    return send_from_directory(UPLOAD_DIR, filename)


# ============================================================
# ROUTES — STUBS for base.html navbar links that don't exist yet
# ============================================================

@app.route('/pos')
@login_required
def pos():
    return redirect(url_for('products'))

@app.route('/settings')
@login_required
def settings():
    return redirect(url_for('products'))

@app.route('/orders')
@login_required
def orders():
    return redirect(url_for('products'))

@app.route('/sales-history')
@login_required
def sales_history():
    return redirect(url_for('products'))

@app.route('/sessions')
@login_required
def session_history():
    return redirect(url_for('products'))

@app.route('/debts')
@login_required
def debts():
    return redirect(url_for('products'))

@app.route('/cashiers')
@login_required
def cashiers():
    return redirect(url_for('products'))

@app.route('/settings/hardware')
@login_required
def settings_hardware():
    return redirect(url_for('products'))

@app.route('/products/export')
@login_required
def products_export():
    flash('Exportación de productos estará disponible en el próximo sprint.', 'info')
    return redirect(url_for('products'))

@app.route('/products/import', methods=['POST'])
@login_required
def products_import():
    flash('Importación de productos estará disponible en el próximo sprint.', 'info')
    return redirect(url_for('products'))

@app.route('/api/subcategories/<int:category_id>')
@login_required
def api_subcategories(category_id):
    return {'subcategories': []}

@app.route('/api/categories/toggle-visibility', methods=['POST'])
@login_required
def api_toggle_visibility():
    return {'success': True}

@app.route('/api/categories/reorder', methods=['POST'])
@login_required
def api_reorder_categories():
    return {'success': True}


# ============================================================
# STARTUP
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
