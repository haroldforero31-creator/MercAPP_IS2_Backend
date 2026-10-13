from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, make_response, session, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from PIL import Image
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os, re, io, csv, secrets, difflib

# Configuramos las rutas para que Flask busque el HTML en la carpeta FRONTEND
base_dir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path)

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

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sprint4-nueva-clave-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'mercapp.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'mercapp.services@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'mykrejpwsnpdpbom')
app.config['MAIL_DEFAULT_SENDER'] = ('MercAPP', os.getenv('MAIL_USERNAME', 'mercapp.services@gmail.com'))

mail = Mail(app)

from models import (
    db, Store, StoreSettings, User, Customer, AuditLog,
    EmailVerification, PasswordReset, Category, Subcategory, Product,
    CashSession, Sale, SaleItem, CreditClient, CreditSale, CreditPayment
)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder.'
login_manager.login_message_category = 'error'

from utilities.helpers import (
    round_to_50, format_weight, generate_verification_code, validate_payment
)

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

def clamp_color_darkness(hex_color, max_brightness=140):
    """Garantiza que un color hexadecimal no sea demasiado claro para mantener contraste con texto blanco."""
    if not hex_color or hex_color == 'default' or not hex_color.startswith('#') or len(hex_color) != 7:
        return hex_color
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        if brightness > max_brightness and brightness > 0:
            factor = max_brightness / brightness
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            return f"#{r:02x}{g:02x}{b:02x}"
        return hex_color
    except Exception:
        return hex_color

# ============================================================
# MODELS — Sprint 2 + Sprint 3: Tienda, Configuración, Categorías, Subcategorías, Productos, Auditoría
# ============================================================

# ============================================================
# CASHIER & SESSION HELPERS
# ============================================================

def is_cashier_mode():
    """Check if the current session is in cashier mode."""
    return session.get('cashier_mode', False)

def get_active_cashier():
    """Get the active cashier User object, or None."""
    cashier_id = session.get('active_cashier_id')
    if cashier_id:
        return db.session.get(User, cashier_id)
    return None

def get_effective_user_id():
    """Get the user ID for sales/sessions: cashier if active, else current_user."""
    if is_cashier_mode():
        cid = session.get('active_cashier_id')
        if cid:
            return cid
    return current_user.id

def admin_only(f):
    """Decorator to restrict access to admin users only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('Acceso restringido a administradores.', 'error')
            return redirect(url_for('pos'))
        if is_cashier_mode():
            flash('Desactiva el modo cajero para acceder aquí.', 'error')
            return redirect(url_for('pos'))
        return f(*args, **kwargs)
    return decorated_function

def get_today_session():
    """Get the active cash session for the current calendar day."""
    if not current_user.is_authenticated or not hasattr(current_user, 'store_id'):
        return None
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    today_end = today_start + timedelta(days=1)
    effective_uid = get_effective_user_id()
    return CashSession.query.filter(
        CashSession.store_id == current_user.store_id,
        CashSession.user_id == effective_uid,
        CashSession.opened_at >= today_start,
        CashSession.opened_at < today_end
    ).first()

def generate_receipt_number():
    """Generate unique receipt number: MRC-YYYYMMDD-NNNN"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f"MRC-{today}-"
    last_sale = Sale.query.filter(
        Sale.store_id == current_user.store_id,
        Sale.receipt_number.like(f"{prefix}%")
    ).order_by(Sale.id.desc()).first()
    if last_sale:
        try:
            last_num = int(last_sale.receipt_number.split('-')[-1])
            return f"{prefix}{last_num + 1:04d}"
        except (ValueError, IndexError):
            pass
    return f"{prefix}0001"

def send_verification_email(email, code):
    """Send a verification code to the specified email address via Gmail SMTP."""
    print("\n" + "="*50)
    print(f"CODIGO DE VERIFICACION PARA {email}: {code}")
    print("="*50 + "\n")
    try:
        if not app.config.get('MAIL_USERNAME'):
            print("Envío de correo omitido: MAIL_USERNAME no está configurado.")
            return True
        msg = Message(
            subject=f'MercAPP - Tu código de verificación: {code}',
            recipients=[email]
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 30px; background: #1A1F2E; color: #E8EAED; border-radius: 16px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="font-size: 1.8rem; margin: 8px 0 4px; background: linear-gradient(135deg, #2E7D32, #FFA726); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">MercAPP</h1>
                <p style="color: #9AA0A6; font-size: 0.9rem;">Sistema de Supermercado</p>
            </div>
            <hr style="border: none; border-top: 1px solid #2D3344; margin: 20px 0;">
            <p style="font-size: 1rem; text-align: center;">Tu código de verificación es:</p>
            <div style="text-align: center; margin: 24px 0;">
                <span style="font-size: 2.5rem; font-weight: 900; letter-spacing: 12px; color: #FFA726; background: rgba(255,143,0,0.1); padding: 16px 32px; border-radius: 12px; border: 2px solid rgba(255,143,0,0.3);">{code}</span>
            </div>
            <p style="font-size: 0.9rem; color: #9AA0A6; text-align: center;">
                Este código expira en <strong style="color: #FFA726;">10 minutos</strong>.<br>
                Si no solicitaste este código, ignora este mensaje.
            </p>
            <hr style="border: none; border-top: 1px solid #2D3344; margin: 20px 0;">
            <p style="font-size: 0.75rem; color: #5F6368; text-align: center;">
                © MercAPP - Sistema POS para Supermercados
            </p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"MAIL ERROR: {str(e)}")
        return True

def send_reset_email(user, token):
    """Send password reset link to user."""
    reset_url = url_for('reset_password', token=token, _external=True)
    print("\n" + "!"*50)
    print(f"LINK DE RECUPERACION PARA {user.email}: {reset_url}")
    print("!"*50 + "\n")
    try:
        if not app.config.get('MAIL_USERNAME'):
            return True
        msg = Message(
            subject='MercAPP - Recuperación de Contraseña',
            recipients=[user.email]
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 30px; background: #1A1F2E; color: #E8EAED; border-radius: 16px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="font-size: 1.8rem; margin: 8px 0 4px; color: #FFA726;">MercAPP</h1>
                <p style="color: #9AA0A6; font-size: 0.9rem;">Recuperación de Contraseña</p>
            </div>
            <p style="font-size: 1rem;">Hola <strong>{user.name}</strong>,</p>
            <p>Has solicitado restablecer tu contraseña. Haz clic en el botón a continuación:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background: #FFA726; color: #121212; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Restablecer Contraseña</a>
            </div>
            <p style="font-size: 0.85rem; color: #9AA0A6;">Este enlace expirará en 1 hora. Si no lo solicitaste, puedes ignorar este mensaje.</p>
        </div>
        """
        mail.send(msg)
        return True
    except Exception as e:
        print(f"MAIL ERROR: {e}")
        return True



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
        p = clamp_color_darkness(global_settings.theme_color_primary, max_brightness=140)
        if p and p != 'default':
            theme_vars['primary'] = p
            theme_vars['primary_light'] = mix_color(p, 'white', 0.85)
            theme_vars['primary_dark'] = mix_color(p, 'black', 0.85)
            theme_vars['primary_glow'] = color_alpha(p, 0.3)
            
        a = clamp_color_darkness(global_settings.theme_color_accent, max_brightness=165)
        if a and a != 'default':
            theme_vars['accent'] = a
            theme_vars['accent_light'] = mix_color(a, 'white', 0.85)
            theme_vars['accent_dark'] = mix_color(a, 'black', 0.85)
            
        bg = clamp_color_darkness(global_settings.theme_color_background, max_brightness=45)
        if bg and bg != 'default':
            theme_vars['bg'] = bg
            theme_vars['bg_card'] = mix_color(bg, 'white', 0.92)
            theme_vars['bg_card_hover'] = mix_color(bg, 'white', 0.87)
            theme_vars['bg_input'] = mix_color(bg, 'white', 0.96)
            theme_vars['border'] = mix_color(bg, 'white', 0.80)
            
        btn_clear = clamp_color_darkness(global_settings.theme_btn_clear_color, max_brightness=140)
        if btn_clear and btn_clear != 'default':
            theme_vars['btn_clear_color'] = btn_clear
            theme_vars['btn_clear_bg'] = color_alpha(btn_clear, 0.12)
            theme_vars['btn_clear_border'] = color_alpha(btn_clear, 0.30)
            theme_vars['btn_clear_hover_bg'] = btn_clear
            
        btn_charge = clamp_color_darkness(global_settings.theme_btn_charge_color, max_brightness=140)
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
    if current_user.is_authenticated:
        return redirect(url_for('pos'))
        
    if request.method == 'POST':
        store_name = request.form.get('store_name', '').strip() or 'Mi Tienda'
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        if not store_name or len(store_name) < 2:
            flash('El nombre de la tienda debe tener al menos 2 caracteres.', 'error')
            return render_template('registro.html')
            
        if not email or '@' not in email:
            flash('Ingresa un correo electrónico válido.', 'error')
            return render_template('registro.html')
            
        if not password or len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('registro.html')
            
        if password != password_confirm:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('registro.html')

        if User.query.filter_by(email=email).first():
            flash('El correo ya está registrado.', 'error')
            return render_template('registro.html')
        
        # Generar código de 6 dígitos y guardar verificación pendiente
        code = generate_verification_code()
        EmailVerification.query.filter_by(email=email, verified=False).delete()
        
        verification = EmailVerification(
            email=email,
            code=code,
            store_name=store_name,
            user_name=name,
            password_hash=generate_password_hash(password),
            expires_at=datetime.now() + timedelta(minutes=10)
        )
        db.session.add(verification)
        db.session.commit()
        
        # Enviar código por correo
        if send_verification_email(email, code):
            session['pending_verification_email'] = email
            flash('Se ha enviado un código de verificación a tu correo electrónico.', 'success')
            return redirect(url_for('verify_email'))
        else:
            flash('Error al enviar el correo de verificación. Verifica que el correo sea válido e intenta de nuevo.', 'error')
            return render_template('registro.html')
            
    return render_template('registro.html')


@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if current_user.is_authenticated:
        return redirect(url_for('pos'))
        
    pending_email = session.get('pending_verification_email')
    if not pending_email:
        flash('No hay verificación pendiente. Regístrate primero.', 'error')
        return redirect(url_for('register'))
        
    verification = EmailVerification.query.filter_by(
        email=pending_email, verified=False
    ).order_by(EmailVerification.created_at.desc()).first()
    
    if not verification:
        session.pop('pending_verification_email', None)
        flash('Verificación no encontrada. Regístrate de nuevo.', 'error')
        return redirect(url_for('register'))
        
    expired = datetime.now() > verification.expires_at
    
    if request.method == 'POST':
        entered_code = request.form.get('code', '').strip()
        
        if expired:
            flash('El código ha expirado. Solicita uno nuevo.', 'error')
            return render_template('verificar_email.html', email=pending_email, expired=True)
            
        if verification.attempts >= 5:
            flash('Demasiados intentos fallidos. Solicita un nuevo código.', 'error')
            return render_template('verificar_email.html', email=pending_email, expired=True)
            
        if entered_code == verification.code:
            verification.verified = True
            try:
                # 1. Crear Tienda
                store = Store(name=verification.store_name)
                db.session.add(store)
                db.session.flush()
                
                # 2. Crear Configuración
                settings_obj = StoreSettings(store_id=store.id, store_name=verification.store_name)
                db.session.add(settings_obj)
                
                # 3. Crear Categorías y Subcategorías por defecto
                default_categories = [
                    ('Bebidas', 'bebidas', 'Bebidas.jpg', 'Gaseosas, jugos, agua y más', [('Gaseosas', 'gaseosas'), ('Jugos', 'jugos'), ('Bebidas Alcohólicas', 'alcoholicas')]),
                    ('Lácteos', 'lacteos', 'Lácteos.avif', 'Leche, queso, yogurt y derivados', [('Leche', 'leche'), ('Yogures', 'yogures'), ('Quesos', 'quesos'), ('Mantequillas', 'mantequillas')]),
                    ('Despensa', 'despensa', 'Despensa.jfif', 'Granos, aceites, enlatados y básicos', [('Granos y Cereales', 'granos'), ('Enlatados', 'enlatados'), ('Aceites y Vinagres', 'aceites'), ('Condimentos y Salsas', 'condimentos'), ('Harinas y Repostería', 'harinas'), ('Pastas', 'pastas')]),
                    ('Snacks', 'snacks', 'Snacks.jfif', 'Papas, galletas, dulces y antojos', [('Ponqués y Dulces', 'dulces'), ('Paquetes de Papas', 'papas'), ('Galletas', 'galletas')]),
                    ('Frescos', 'frescos', 'frescos.webp', 'Frutas, verduras y productos frescos', [('Frutas y Verduras', 'frutas'), ('Carnicería', 'carniceria'), ('Quesos Frescos', 'quesos_frescos'), ('Panadería', 'panaderia')]),
                    ('Limpieza y Aseo', 'limpieza_y_aseo', 'limpieza_y_aseo.jfif', 'Jabones, detergentes y aseo del hogar', [('Detergentes', 'detergentes'), ('Desinfectantes', 'desinfectantes'), ('Aseo Personal', 'aseo_personal'), ('Aseo del Hogar', 'aseo_hogar')]),
                    ('Farmacia', 'farmacia', 'Farmacia.jfif', 'Medicamentos y cuidado personal', [('Medicamentos', 'medicamentos'), ('Cuidado Personal', 'cuidado_personal'), ('Vitaminas y Suplementos', 'vitaminas'), ('Primeros Auxilios', 'primeros_auxilios')]),
                    ('Mascotas', 'mascotas', 'Mascotas.jfif', 'Alimentos y accesorios para mascotas', [('Comida para Perros', 'perros'), ('Comida para Gatos', 'gatos'), ('Accesorios', 'accesorios_mascotas')]),
                ]
                for i, (cat_name, cat_slug, cat_img, cat_desc, subs) in enumerate(default_categories, start=1):
                    cat = Category(
                        store_id=store.id,
                        name=cat_name,
                        slug=cat_slug,
                        image=cat_img,
                        description=cat_desc,
                        display_order=i,
                        visible_in_pos=True
                    )
                    db.session.add(cat)
                    db.session.flush()
                    for j, (sub_name, sub_slug) in enumerate(subs, start=1):
                        sub = Subcategory(
                            store_id=store.id,
                            category_id=cat.id,
                            name=sub_name,
                            slug=sub_slug,
                            display_order=j
                        )
                        db.session.add(sub)
                
                # 4. Crear Usuario Administrador
                user = User(
                    store_id=store.id,
                    name=verification.user_name,
                    email=verification.email,
                    password_hash=verification.password_hash,
                    is_admin=True
                )
                db.session.add(user)
                db.session.commit()
                
                log_audit('REGISTER_VERIFIED', f'Usuario verificado y registrado: {user.name} ({user.email}) - Tienda: {store.name}', user.id)
                session.pop('pending_verification_email', None)
                login_user(user)
                flash('¡Cuenta creada y verificada exitosamente! Bienvenido a MercAPP.', 'success')
                return redirect(url_for('pos'))
            except Exception as e:
                db.session.rollback()
                flash('Error al crear la cuenta, intenta de nuevo.', 'error')
                print(e)
        else:
            verification.attempts += 1
            db.session.commit()
            remaining = 5 - verification.attempts
            flash(f'Código incorrecto. Te quedan {remaining} intentos.', 'error')
            
    return render_template('verificar_email.html', email=pending_email, expired=expired)


@app.route('/resend-code', methods=['POST'])
def resend_code():
    pending_email = session.get('pending_verification_email')
    if not pending_email:
        flash('No hay verificación pendiente.', 'error')
        return redirect(url_for('register'))
        
    old_verification = EmailVerification.query.filter_by(
        email=pending_email
    ).order_by(EmailVerification.created_at.desc()).first()
    
    if not old_verification:
        flash('Verificación no encontrada. Regístrate de nuevo.', 'error')
        return redirect(url_for('register'))
        
    code = generate_verification_code()
    EmailVerification.query.filter_by(email=pending_email, verified=False).delete()
    
    verification = EmailVerification(
        email=pending_email,
        code=code,
        store_name=old_verification.store_name,
        user_name=old_verification.user_name,
        password_hash=old_verification.password_hash,
        expires_at=datetime.now() + timedelta(minutes=10)
    )
    db.session.add(verification)
    db.session.commit()
    
    if send_verification_email(pending_email, code):
        flash('Se ha enviado un nuevo código de verificación a tu correo.', 'success')
    else:
        flash('Error al reenviar el correo. Intenta de nuevo más tarde.', 'error')
        
    return redirect(url_for('verify_email'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('pos'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            PasswordReset.query.filter_by(user_id=user.id, used=False).delete()
            token = secrets.token_urlsafe(32)
            reset_record = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=datetime.now() + timedelta(hours=1)
            )
            db.session.add(reset_record)
            db.session.commit()
            
            if send_reset_email(user, token):
                flash('Se ha enviado un enlace de recuperación a tu correo.', 'success')
            else:
                flash('Error al enviar el correo. Intenta de nuevo más tarde.', 'error')
        else:
            flash('Si existe una cuenta asociada a ese correo, recibirás un enlace en unos momentos.', 'success')
            
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('pos'))
        
    reset_record = PasswordReset.query.filter_by(token=token, used=False).first()
    
    if not reset_record or datetime.now() > reset_record.expires_at:
        flash('El enlace de recuperación es inválido o ha expirado.', 'error')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if not password or len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'error')
            return render_template('reset_password.html', token=token)
            
        if password != confirm:
            flash('Las contraseñas no coinciden.', 'error')
            return render_template('reset_password.html', token=token)
            
        user = reset_record.user
        user.set_password(password)
        reset_record.used = True
        db.session.commit()
        
        flash('Tu contraseña ha sido actualizada exitosamente. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html', token=token)

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
        
        # Theme visual settings con protección estricta de contraste para texto blanco
        p_raw = request.form.get('theme_color_primary', 'default').strip()
        store.theme_color_primary = clamp_color_darkness(p_raw, max_brightness=140)
        
        a_raw = request.form.get('theme_color_accent', 'default').strip()
        store.theme_color_accent = clamp_color_darkness(a_raw, max_brightness=165)
        
        bg_raw = request.form.get('theme_color_background', 'default').strip()
        store.theme_color_background = clamp_color_darkness(bg_raw, max_brightness=45)
        
        store.theme_font_family = request.form.get('theme_font_family', 'default').strip()
        store.theme_font_size = request.form.get('theme_font_size', 'default').strip()
        
        clear_raw = request.form.get('theme_btn_clear_color', 'default').strip()
        store.theme_btn_clear_color = clamp_color_darkness(clear_raw, max_brightness=140)
        
        charge_raw = request.form.get('theme_btn_charge_color', 'default').strip()
        store.theme_btn_charge_color = clamp_color_darkness(charge_raw, max_brightness=140)
        
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
    
    query = Product.query.filter(
        Product.store_id == current_user.store_id,
        db.or_(Product.barcode == None, Product.barcode != '__CUSTOM__')
    )
    
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
    query = Product.query.filter(
        Product.store_id == current_user.store_id,
        db.or_(Product.barcode == None, Product.barcode != '__CUSTOM__')
    )
    
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
    
    product_count = Product.query.filter(
        Product.category_id == cat.id,
        db.or_(Product.barcode == None, Product.barcode != '__CUSTOM__')
    ).count()
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
# ROUTES — POS (Punto de Venta / Caja) & SESIONES DE CAJA
# ============================================================

@app.route('/pos')
@login_required
def pos():
    session.pop('admin_unlocked', None)
    active_session = get_today_session()
    if not active_session:
        return redirect(url_for('session_open'))
        
    categories = Category.query.filter_by(store_id=current_user.store_id, visible_in_pos=True).order_by(Category.display_order).all()
    settings = get_store_settings()
    return render_template('caja.html', categories=categories, settings=settings, scale_mode=settings.scale_mode if settings else 'manual')


@app.route('/session/open', methods=['GET', 'POST'])
@login_required
def session_open():
    active_session = get_today_session()
    if active_session:
        return redirect(url_for('pos'))
        
    if request.method == 'POST':
        base_amount = request.form.get('base_amount', '0')
        try:
            base = int(base_amount)
            new_sess = CashSession(
                store_id=current_user.store_id,
                user_id=get_effective_user_id(),
                base_amount=base,
                expected_cash=base
            )
            db.session.add(new_sess)
            db.session.commit()
            log_audit('CASH_SESSION_OPEN', f'Caja abierta con base de {format_cop(base)}', current_user.id)
            return redirect(url_for('pos'))
        except ValueError:
            flash('Monto base inválido', 'error')
            
    return render_template('caja_apertura.html')


@app.route('/session/close', methods=['GET', 'POST'])
@login_required
def session_close():
    """Cerrar la sesión de hoy o una específica."""
    session_id = request.args.get('session_id', type=int)
    if session_id:
        active_session = db.session.get(CashSession, session_id)
        if not active_session or active_session.store_id != current_user.store_id:
            flash('Sesión no encontrada.', 'error')
            return redirect(url_for('session_history'))
        if active_session.status == 'cerrada':
            flash('Esa sesión ya está cerrada.', 'error')
            return redirect(url_for('session_history'))
    else:
        active_session = get_today_session()
        if not active_session:
            active_session = CashSession.query.filter_by(
                store_id=current_user.store_id, status='abierta'
            ).order_by(CashSession.opened_at.desc()).first()
        if not active_session:
            flash('No hay sesiones abiertas.', 'error')
            return redirect(url_for('pos'))
        
    sales_in_session = Sale.query.filter_by(cash_session_id=active_session.id, status='completada').all()
    cash = sum(s.amount_cash or 0 for s in sales_in_session)
    card = sum(s.amount_card or 0 for s in sales_in_session)
    transfer = sum(s.amount_transfer or 0 for s in sales_in_session)
    expected_cash = active_session.base_amount + cash
    
    if request.method == 'POST':
        actual = request.form.get('actual_cash', '0')
        try:
            actual = int(actual)
            active_session.cash_sales = cash
            active_session.card_sales = card
            active_session.transfer_sales = transfer
            active_session.expected_cash = expected_cash
            active_session.actual_cash = actual
            active_session.status = 'cerrada'
            active_session.closed_at = datetime.now()
            db.session.commit()
            diff = actual - expected_cash
            diff_text = f"+{format_cop(diff)}" if diff >= 0 else f"-{format_cop(abs(diff))}"
            log_audit('CASH_SESSION_CLOSE', f'Caja cerrada. Recuento: {format_cop(actual)}, Esperado: {format_cop(expected_cash)}, Diferencia: {diff_text}', current_user.id)
            flash(f'Caja cerrada exitosamente. Diferencia: {diff_text}', 'success')
            return redirect(url_for('session_history'))
        except ValueError:
            flash('Monto de recuento inválido', 'error')
            
    return render_template('caja_cierre.html', expected_cash=expected_cash, base=active_session.base_amount, cash_sales=cash, card=card, transfer=transfer, active_session=active_session)


@app.route('/session/history')
@app.route('/session-history')
@app.route('/sessions')
@login_required
@admin_only
def session_history():
    sessions = CashSession.query.filter_by(store_id=current_user.store_id).order_by(CashSession.opened_at.desc()).all()
    return render_template('caja_historial.html', sessions=sessions)


@app.route('/session/<int:session_id>')
@login_required
@admin_only
def session_detail(session_id):
    session_obj = db.session.get(CashSession, session_id)
    if not session_obj or session_obj.store_id != current_user.store_id:
        flash('Sesión no encontrada.', 'error')
        return redirect(url_for('session_history'))
    
    # Sales for this specific session
    sales = Sale.query.filter_by(cash_session_id=session_id).order_by(Sale.sale_date.desc()).all()
    
    # Calculate real-time totals from actual sales
    completed_sales = [s for s in sales if s.status == 'completada']
    cash_total = sum(
        (s.amount_cash if s.payment_method == 'mixto' and s.amount_cash else s.total)
        for s in completed_sales if s.payment_method in ('efectivo', 'mixto')
    )
    transfer_total = sum(
        (s.amount_transfer if s.payment_method == 'mixto' and s.amount_transfer else s.total)
        for s in completed_sales if s.payment_method in ('transferencia', 'mixto')
    )
    card_total = sum(
        (s.amount_card if s.payment_method == 'mixto' and s.amount_card else s.total)
        for s in completed_sales if s.payment_method in ('tarjeta', 'mixto')
    )
    expected_cash = (session_obj.base_amount or 0) + cash_total
    
    return render_template('caja_detalle.html', session_obj=session_obj, session=session_obj, sales=sales,
                           cash_total=cash_total, transfer_total=transfer_total,
                           card_total=card_total, expected_cash_live=expected_cash)


# ============================================================
# ROUTES — HISTORIAL DE VENTAS Y FACTURACIÓN
# ============================================================

@app.route('/sales')
@app.route('/sales-history')
@login_required
@admin_only
def sales_history():
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    method_filter = request.args.get('method', '')
    
    query = Sale.query.filter_by(store_id=current_user.store_id)
    
    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Sale.sale_date >= df)
        except ValueError:
            pass
    
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            dt = dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Sale.sale_date <= dt)
        except ValueError:
            pass
    
    if method_filter:
        query = query.filter_by(payment_method=method_filter)
        
    all_filtered = query.all()
    total_ventas = sum(s.total for s in all_filtered if s.status == 'completada')
    count_ventas = sum(1 for s in all_filtered if s.status == 'completada')
    count_anuladas = sum(1 for s in all_filtered if s.status == 'anulada')
    
    sales = query.order_by(Sale.sale_date.desc()).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('historial_ventas.html', sales=sales,
                           total_ventas=total_ventas, count_ventas=count_ventas,
                           count_anuladas=count_anuladas,
                           date_from=date_from, date_to=date_to, method_filter=method_filter)


@app.route('/sales/<int:sale_id>')
@login_required
@admin_only
def sale_detail(sale_id):
    sale = db.session.get(Sale, sale_id)
    if not sale or sale.store_id != current_user.store_id:
        flash('Venta no encontrada.', 'error')
        return redirect(url_for('sales_history'))
    settings = get_store_settings()
    return render_template('detalle_venta.html', sale=sale, settings=settings)


@app.route('/sales/<int:sale_id>/receipt')
@login_required
def sale_receipt(sale_id):
    sale = db.session.get(Sale, sale_id)
    if not sale or sale.store_id != current_user.store_id:
        flash('Venta no encontrada.', 'error')
        return redirect(url_for('sales_history'))
    ghost = request.args.get('ghost', '0') == '1'
    settings = get_store_settings()
    return render_template('factura.html', sale=sale, settings=settings, ghost=ghost)


@app.route('/sales/export')
@login_required
@admin_only
def sales_export():
    """Exportar historial de ventas en formato CSV."""
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Sale.query.filter_by(store_id=current_user.store_id, status='completada')
    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Sale.sale_date >= df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            dt = dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Sale.sale_date <= dt)
        except ValueError:
            pass
            
    sales = query.order_by(Sale.sale_date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Factura', 'Fecha', 'Metodo', 'Subtotal', 'Total', 'Efectivo', 'Tarjeta', 'Transferencia', 'Referencia'])
    for s in sales:
        writer.writerow([
            s.receipt_number,
            s.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
            s.payment_method,
            s.subtotal,
            s.total,
            s.amount_cash or 0,
            s.amount_card or 0,
            s.amount_transfer or 0,
            s.payment_ref or ''
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=ventas_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


# ============================================================
# API POS — BÚSQUEDA Y PROCESAMIENTO DE VENTAS
# ============================================================

@app.route('/api/product/smart-search')
@login_required
def api_smart_search():
    """Búsqueda inteligente: detecta código de barras vs nombre."""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'success': False, 'message': 'Ingresa al menos 2 caracteres.'}), 400
    
    is_barcode = bool(re.match(r'^\d{4,}$', query))
    
    def serialize_product(p):
        return {
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'price_formatted': format_cop(p.price),
            'barcode': p.barcode,
            'image': p.image,
            'stock': p.stock,
            'category': p.category.name if p.category else '',
            'sell_by_weight': p.sell_by_weight,
            'weight_unit': p.weight_unit
        }
    
    if is_barcode:
        product = Product.query.filter_by(
            store_id=current_user.store_id, barcode=query, is_active=True
        ).first()
        if product:
            return jsonify({
                'success': True,
                'mode': 'barcode',
                'product': serialize_product(product),
                'products': [serialize_product(product)]
            })
        else:
            partial = Product.query.filter(
                Product.store_id == current_user.store_id,
                Product.barcode.ilike(f'%{query}%'),
                Product.is_active == True
            ).limit(10).all()
            if partial:
                return jsonify({
                    'success': True,
                    'mode': 'barcode_partial',
                    'products': [serialize_product(p) for p in partial]
                })
            return jsonify({
                'success': False,
                'mode': 'barcode',
                'message': f'No se encontró producto con código de barras "{query}".'
            }), 404
    else:
        query_lower = query.lower()
        query_words = query_lower.split()
        all_products = Product.query.filter(
            Product.store_id == current_user.store_id,
            Product.is_active == True,
            db.or_(Product.barcode == None, Product.barcode != '__CUSTOM__')
        ).all()
        
        scored = []
        for p in all_products:
            name_lower = p.name.lower()
            score = 0
            if name_lower == query_lower:
                score = 1000
            elif name_lower.startswith(query_lower):
                score = 500
            elif query_lower in name_lower:
                score = 300
            else:
                matched_words = sum(1 for w in query_words if w in name_lower)
                if matched_words > 0:
                    score = 100 * matched_words
                else:
                    product_words = name_lower.split()
                    for qw in query_words:
                        for pw in product_words:
                            ratio = difflib.SequenceMatcher(None, qw, pw).ratio()
                            if ratio >= 0.65:
                                score = max(score, int(ratio * 80))
            if score > 0:
                score += max(0, 50 - len(p.name))
                score += min((p.sale_count or 0), 30)
                scored.append((score, p))
                
        scored.sort(key=lambda x: -x[0])
        final_matches = [p for _, p in scored[:15]]
        return jsonify({
            'success': True,
            'mode': 'name',
            'products': [serialize_product(p) for p in final_matches]
        })


@app.route('/api/product/scan/<barcode>')
@login_required
def api_scan_product(barcode):
    """Buscar producto por código de barras."""
    product = Product.query.filter_by(store_id=current_user.store_id, barcode=barcode, is_active=True).first()
    if not product:
        return jsonify({'success': False, 'message': 'Producto no encontrado con ese código de barras.'}), 404
    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'price_formatted': format_cop(product.price),
            'barcode': product.barcode,
            'image': product.image,
            'stock': product.stock,
            'category': product.category.name if product.category else '',
            'sell_by_weight': product.sell_by_weight,
            'weight_unit': product.weight_unit
        }
    })


@app.route('/api/product/search')
@login_required
def api_search_product():
    """Búsqueda simple de productos por nombre."""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'success': False, 'message': 'Ingresa al menos 2 caracteres.'}), 400
    products = Product.query.filter(
        Product.store_id == current_user.store_id,
        Product.name.ilike(f'%{query}%'),
        Product.is_active == True
    ).limit(20).all()
    return jsonify({
        'success': True,
        'products': [{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'price_formatted': format_cop(p.price),
            'barcode': p.barcode,
            'image': p.image,
            'stock': p.stock,
            'category': p.category.name if p.category else '',
            'sell_by_weight': p.sell_by_weight,
            'weight_unit': p.weight_unit
        } for p in products]
    })


@app.route('/api/product/plu')
@login_required
def api_plu_search():
    """Buscar producto por código PLU."""
    plu_code = request.args.get('code', '').strip()
    if not plu_code:
        return jsonify({'success': False, 'message': 'Código PLU no proporcionado.'}), 400
    product = Product.query.filter_by(
        store_id=current_user.store_id, plu_code=plu_code, is_active=True
    ).first()
    if product:
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'price_formatted': format_cop(product.price),
                'barcode': product.barcode,
                'image': product.image,
                'stock': product.stock,
                'sell_by_weight': product.sell_by_weight,
                'weight_unit': product.weight_unit,
                'plu_code': product.plu_code
            }
        })
    return jsonify({'success': False, 'message': f'No se encontró producto con código PLU "{plu_code}".'}), 404


@app.route('/api/category/<int:category_id>/products')
@login_required
def api_category_products(category_id):
    """Productos por categoría para la rejilla táctil de la caja."""
    products = Product.query.filter_by(
        store_id=current_user.store_id, category_id=category_id, is_active=True
    ).order_by(
        db.case(
            (db.and_(Product.plu_code.isnot(None), Product.plu_code != ''), 2),
            (db.or_(Product.barcode.is_(None), Product.barcode == ''), 0),
            else_=1
        ),
        Product.name
    ).all()
    return jsonify({
        'success': True,
        'products': [{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'price_formatted': format_cop(p.price),
            'barcode': p.barcode,
            'image': p.image,
            'stock': p.stock,
            'has_barcode': p.has_barcode,
            'sell_by_weight': p.sell_by_weight,
            'weight_unit': p.weight_unit
        } for p in products]
    })


@app.route('/api/sale', methods=['POST'])
@login_required
def api_process_sale():
    """Procesar y guardar una venta completa."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Datos inválidos.'}), 400
        
        items = data.get('items', [])
        payment = data.get('payment', {})
        if not items:
            return jsonify({'success': False, 'message': 'El carrito está vacío.'}), 400
        
        sale_items = []
        total = 0
        
        for item in items:
            if item.get('is_custom'):
                custom_name = item.get('custom_name', 'Varios').strip() or 'Varios'
                custom_price = int(item.get('custom_price', 0))
                if custom_price <= 0:
                    return jsonify({'success': False, 'message': 'Precio inválido para producto personalizado.'}), 400
                product = Product.query.filter_by(
                    store_id=current_user.store_id,
                    barcode='__CUSTOM__'
                ).first()
                if not product:
                    fallback_cat = Category.query.filter_by(store_id=current_user.store_id).first()
                    product = Product(
                        store_id=current_user.store_id,
                        name='Varios',
                        price=0,
                        category_id=fallback_cat.id if fallback_cat else None,
                        is_active=False,
                        barcode='__CUSTOM__'
                    )
                    db.session.add(product)
                    db.session.flush()
            else:
                product = db.session.get(Product, item.get('product_id'))
                if not product or product.store_id != current_user.store_id or not product.is_active:
                    return jsonify({'success': False, 'message': 'Producto no encontrado o inactivo.'}), 400
            
            if getattr(product, 'sell_by_weight', False) and not item.get('is_custom'):
                weight_grams = item.get('weight_grams', 0)
                if not isinstance(weight_grams, int) or weight_grams < 10:
                    return jsonify({'success': False, 'message': f'Peso inválido para {product.name}.'}), 400
                if weight_grams > 50000:
                    return jsonify({'success': False, 'message': f'El peso máximo para "{product.name}" es 50 kg.'}), 400
                if product.weight_unit == 'lb':
                    subtotal = round_to_50(product.price * (weight_grams / 500.0))
                else:
                    subtotal = round_to_50(product.price * (weight_grams / 1000.0))
                total += subtotal
                sale_items.append({
                    'product': product,
                    'quantity': 1,
                    'unit_price': product.price,
                    'subtotal': subtotal,
                    'weight_grams': weight_grams,
                    'weight_unit': product.weight_unit
                })
            else:
                quantity = item.get('quantity', 0)
                if not isinstance(quantity, int) or quantity < 1:
                    return jsonify({'success': False, 'message': f'Cantidad inválida para {product.name}.'}), 400
                if not item.get('is_custom') and not product.sell_by_weight and product.stock is not None:
                    if product.stock <= 0:
                        return jsonify({'success': False, 'message': f'El producto "{product.name}" está agotado.'}), 400
                    if quantity > product.stock:
                        return jsonify({'success': False, 'message': f'Stock insuficiente para "{product.name}". Disponible: {product.stock}'}), 400
                
                unit_price = custom_price if item.get('is_custom') else product.price
                subtotal = unit_price * quantity
                total += subtotal
                sale_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'subtotal': subtotal,
                    'weight_grams': None,
                    'weight_unit': None,
                    'is_custom': item.get('is_custom', False)
                })
        
        if total <= 0:
            return jsonify({'success': False, 'message': 'El total de la venta no puede ser $0.'}), 400
        
        payment_method = payment.get('method', '')
        pay_errors, pay_data = validate_payment(
            payment_method=payment_method,
            total=total,
            amount_received=payment.get('amount_received'),
            card_last4=payment.get('card_last4'),
            card_approval=payment.get('card_approval'),
            transfer_bank=payment.get('transfer_bank'),
            transfer_ref=payment.get('transfer_ref'),
            transfer_name=payment.get('transfer_name'),
            amount_cash=payment.get('amount_cash'),
            amount_card=payment.get('amount_card'),
            amount_transfer=payment.get('amount_transfer')
        )
        if pay_errors:
            return jsonify({'success': False, 'message': ' | '.join(pay_errors)}), 400
        
        active_session = get_today_session()
        if not active_session:
            return jsonify({'success': False, 'message': 'No hay una base de caja para hoy. Abre caja primero.'}), 400

        receipt_number = generate_receipt_number()
        sale = Sale(
            store_id=current_user.store_id,
            cash_session_id=active_session.id,
            receipt_number=receipt_number,
            user_id=get_effective_user_id(),
            subtotal=total,
            total=total,
            payment_method=pay_data['payment_method'],
            amount_received=pay_data.get('amount_received', total),
            change_given=pay_data.get('change_given', 0),
            payment_ref=pay_data.get('payment_ref'),
            amount_cash=pay_data.get('amount_cash', 0),
            amount_card=pay_data.get('amount_card', 0),
            amount_transfer=pay_data.get('amount_transfer', 0),
            status='completada'
        )
        db.session.add(sale)
        db.session.flush()
        
        for si in sale_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=si['product'].id,
                quantity=si['quantity'],
                unit_price=si['unit_price'],
                subtotal=si['subtotal'],
                weight_grams=si.get('weight_grams'),
                weight_unit=si.get('weight_unit')
            )
            db.session.add(sale_item)
            if not si.get('is_custom'):
                prod = si['product']
                prod.sale_count = (prod.sale_count or 0) + si['quantity']
                if not prod.sell_by_weight and prod.stock is not None:
                    prod.stock -= si['quantity']
                    
        db.session.commit()
        log_audit('SALE_COMPLETED', f'Venta {sale.receipt_number} realizada por {format_cop(sale.total)} ({sale.payment_method})', current_user.id)
        
        return jsonify({
            'success': True,
            'message': '¡Venta procesada exitosamente!',
            'sale': {
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'total': sale.total,
                'total_formatted': format_cop(sale.total),
                'change': sale.change_given,
                'change_formatted': format_cop(sale.change_given),
                'payment_method': sale.payment_method
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al procesar la venta: {str(e)}'}), 500


@app.route('/api/sale/<int:sale_id>/void', methods=['POST'])
@login_required
def api_void_sale(sale_id):
    """Anular una venta."""
    data = request.get_json() or {}
    password = data.get('password', '')
    if not current_user.check_password(password):
        return jsonify({'success': False, 'message': 'Contraseña incorrecta.'}), 403
    sale = db.session.get(Sale, sale_id)
    if not sale or sale.store_id != current_user.store_id:
        return jsonify({'success': False, 'message': 'Venta no encontrada.'}), 404
    if sale.status == 'anulada':
        return jsonify({'success': False, 'message': 'Esta venta ya fue anulada.'}), 400
    sale.status = 'anulada'
    db.session.commit()
    log_audit('SALE_VOIDED', f'Venta {sale.receipt_number} anulada', current_user.id, 'WARNING')
    return jsonify({'success': True, 'message': f'Venta {sale.receipt_number} anulada exitosamente.'})


@app.route('/api/credit-sale', methods=['POST'])
@login_required
def api_credit_sale():
    """Process a sale on credit (fiado) for a specific client."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Datos inválidos.'}), 400
        
        client_id = data.get('client_id')
        items = data.get('items', [])
        
        if not client_id:
            return jsonify({'success': False, 'message': 'Cliente no especificado.'}), 400
        
        client = db.session.get(CreditClient, client_id)
        if not client or client.store_id != current_user.store_id:
            return jsonify({'success': False, 'message': 'Cliente no encontrado.'}), 404
        
        if not items:
            return jsonify({'success': False, 'message': 'El carrito está vacío.'}), 400
        
        # Calculate totals and validate products (same as regular sale)
        sale_items = []
        total = 0
        
        for item in items:
            if item.get('is_custom'):
                custom_name = item.get('custom_name', 'Varios').strip()
                if not custom_name: custom_name = 'Varios'
                custom_price = int(item.get('custom_price', 0))
                if custom_price <= 0:
                    return jsonify({'success': False, 'message': 'Precio inválido para producto personalizado.'}), 400
                
                # Reuse single Varios product per store
                product = Product.query.filter_by(
                    store_id=current_user.store_id, barcode='__CUSTOM__'
                ).first()
                if not product:
                    fallback_cat = Category.query.filter_by(store_id=current_user.store_id).first()
                    product = Product(
                        store_id=current_user.store_id,
                        name='Varios',
                        price=0,
                        category_id=fallback_cat.id if fallback_cat else None,
                        is_active=False,
                        barcode='__CUSTOM__'
                    )
                    db.session.add(product)
                    db.session.flush()
            else:
                product = db.session.get(Product, item.get('product_id'))
                if not product or product.store_id != current_user.store_id or not product.is_active:
                    return jsonify({'success': False, 'message': 'Producto no encontrado o inactivo.'}), 400
            
            if getattr(product, 'sell_by_weight', False) and not item.get('is_custom'):
                weight_grams = item.get('weight_grams', 0)
                if not isinstance(weight_grams, int) or weight_grams < 10:
                    return jsonify({'success': False, 'message': f'Peso inválido para {product.name}.'}), 400
                if weight_grams > 50000:
                    return jsonify({'success': False, 'message': f'Peso máximo 50kg para "{product.name}".'}), 400
                
                if product.weight_unit == 'lb':
                    subtotal = round_to_50(product.price * (weight_grams / 500.0))
                else:
                    subtotal = round_to_50(product.price * (weight_grams / 1000.0))
                
                total += subtotal
                sale_items.append({
                    'product': product, 'quantity': 1, 'unit_price': product.price,
                    'subtotal': subtotal, 'weight_grams': weight_grams, 'weight_unit': product.weight_unit,
                    'is_custom': False
                })
            else:
                quantity = item.get('quantity', 0)
                if not isinstance(quantity, int) or quantity < 1:
                    return jsonify({'success': False, 'message': f'Cantidad inválida para {product.name}.'}), 400
                # Stock validation (skip for custom products)
                if not item.get('is_custom') and not product.sell_by_weight and product.stock is not None:
                    if product.stock <= 0:
                        return jsonify({'success': False, 'message': f'El producto "{product.name}" está agotado.'}), 400
                    if quantity > product.stock:
                        return jsonify({'success': False, 'message': f'Stock insuficiente para "{product.name}". Disponible: {product.stock}'}), 400
                
                unit_price = custom_price if item.get('is_custom') else product.price
                subtotal = unit_price * quantity
                total += subtotal
                sale_items.append({
                    'product': product, 'quantity': quantity, 'unit_price': unit_price,
                    'subtotal': subtotal, 'weight_grams': None, 'weight_unit': None,
                    'is_custom': item.get('is_custom', False)
                })
        
        if total <= 0:
            return jsonify({'success': False, 'message': 'El total no puede ser $0.'}), 400
        
        # Get active session
        active_session = get_today_session()
        if not active_session:
            return jsonify({'success': False, 'message': 'No hay caja abierta.'}), 400
        
        # Create the sale as 'fiado'
        receipt_number = generate_receipt_number()
        
        sale = Sale(
            store_id=current_user.store_id,
            cash_session_id=active_session.id,
            credit_client_id=client_id,
            receipt_number=receipt_number,
            user_id=get_effective_user_id(),
            subtotal=total,
            total=total,
            payment_method='fiado',
            amount_received=0,
            change_given=0,
            payment_ref=f'Fiado: {client.name}',
            status='completada'
        )
        db.session.add(sale)
        db.session.flush()
        
        # Create sale items
        for si in sale_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=si['product'].id,
                quantity=si['quantity'],
                unit_price=si['unit_price'],
                subtotal=si['subtotal'],
                weight_grams=si.get('weight_grams'),
                weight_unit=si.get('weight_unit')
            )
            db.session.add(sale_item)
        
        # Increment sale_count and decrement stock (skip for custom products)
        for si in sale_items:
            if si.get('is_custom'):
                continue
            prod = si['product']
            prod.sale_count = (prod.sale_count or 0) + si['quantity']
            
            # Decrement stock if applicable
            if not prod.sell_by_weight and prod.stock is not None:
                prod.stock -= si['quantity']
        
        # Create credit sale record
        credit_sale = CreditSale(
            client_id=client_id,
            sale_id=sale.id,
            amount=total,
            balance=total,
            status='pendiente'
        )
        db.session.add(credit_sale)
        
        db.session.commit()
        
        # Opcional: Notificación por correo electrónico si el cajero lo solicitó
        send_email_flag = data.get('send_email', False)
        recipient_email = data.get('email', '').strip()
        if send_email_flag and recipient_email:
            try:
                store = db.session.get(Store, current_user.store_id)
                store_name = store.name if store else "MercAPP"
                msg = Message(
                    subject=f"Comprobante de Venta Fiada - {store_name} (#{sale.receipt_number})",
                    recipients=[recipient_email]
                )
                items_summary = "\n".join([f"- {si['product'].name} x{si['quantity']}: {format_cop(si['subtotal'])}" for si in sale_items])
                msg.body = f"""Hola {client.name},

Se ha registrado una compra fiada a tu nombre en {store_name}:

Factura: #{sale.receipt_number}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total de esta compra: {format_cop(sale.total)}
Nueva deuda total acumulada: {format_cop(client.total_debt)}

Detalle de productos:
{items_summary}

¡Gracias por su preferencia!
"""
                mail.send(msg)
            except Exception as mail_err:
                print(f"[MAIL] Error enviando comprobante de fiado por correo: {mail_err}")

        return jsonify({
            'success': True,
            'message': f'Venta fiada registrada para {client.name}',
            'sale': {
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'total': sale.total,
                'total_formatted': format_cop(sale.total),
                'client_name': client.name,
                'new_total_debt': client.total_debt
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/verify-admin-pin', methods=['POST'])
@login_required
def api_verify_admin_pin():
    """Verificar contraseña de admin para desbloquear desde modo cajero."""
    data = request.get_json() or {}
    pin = data.get('pin', '')
    if current_user.check_password(pin):
        session['admin_unlocked'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Contraseña incorrecta.'}), 403


@app.route('/api/settings/printer', methods=['GET', 'POST'])
@login_required
def api_settings_printer():
    settings = get_store_settings()
    if request.method == 'POST':
        data = request.get_json() or {}
        printer_name = data.get('printer_name', '')
        if settings:
            settings.printer_name = printer_name
            db.session.commit()
        return jsonify({'success': True, 'printer_name': printer_name})
    return jsonify({'success': True, 'printer_name': settings.printer_name if settings else ''})


# ============================================================
# API HARDWARE STUBS / FALLBACKS
# ============================================================

@app.route('/api/hardware/printers')
@login_required
def api_hardware_printers():
    return jsonify({'success': False, 'message': 'Impresión nativa directa disponible mediante el diálogo del navegador.'}), 200

@app.route('/api/hardware/ports')
@login_required
def api_hardware_ports():
    return jsonify({'success': True, 'ports': []})

@app.route('/api/hardware/open-drawer', methods=['POST'])
@login_required
def api_hardware_open_drawer():
    return jsonify({'success': True, 'message': 'Cajón monedero listo.'})

@app.route('/api/hardware/print', methods=['POST'])
@login_required
def api_hardware_print():
    return jsonify({'success': True, 'message': 'Usa la vista de factura para imprimir térmico.'})

@app.route('/api/hardware/weight')
@login_required
def api_hardware_weight():
    return jsonify({'success': False, 'message': 'Modo báscula manual activo.'})

@app.route('/api/hardware/detect-scale')
@login_required
def api_hardware_detect_scale():
    return jsonify({'success': False, 'message': 'No se detectó báscula física. Se usará entrada manual de peso.'})

@app.route('/orders')
@login_required
def orders():
    flash('El módulo de pedidos en línea estará disponible en el siguiente sprint.', 'info')
    return redirect(url_for('settings'))

@app.route('/debts')
@login_required
@admin_only
def debts():
    """List all credit clients with their debt status."""
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    
    query = CreditClient.query.filter_by(store_id=current_user.store_id, is_active=True)
    
    if search:
        query = query.filter(
            db.or_(
                CreditClient.name.ilike(f'%{search}%'),
                CreditClient.phone.ilike(f'%{search}%')
            )
        )
    
    clients = query.order_by(CreditClient.name).all()
    
    # Filter by status in Python (since it's a computed property)
    if status_filter == 'pendiente':
        clients = [c for c in clients if c.debt_status == 'pendiente']
    elif status_filter == 'pagado':
        clients = [c for c in clients if c.debt_status == 'pagado']
    
    # Summary stats
    total_debt = sum(c.total_debt for c in clients)
    pending_count = sum(1 for c in clients if c.debt_status == 'pendiente')
    
    return render_template('deudas.html', clients=clients, total_debt=total_debt,
                           pending_count=pending_count, search=search, status_filter=status_filter)


@app.route('/debts/new-client', methods=['GET', 'POST'])
@login_required
@admin_only
def debt_new_client():
    """Create a new credit client and redirect to their POS view."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        if not name or len(name) < 2:
            flash('El nombre del cliente debe tener al menos 2 caracteres.', 'error')
            return redirect(url_for('debts'))
        
        client = CreditClient(
            store_id=current_user.store_id,
            name=name,
            phone=phone if phone else None
        )
        db.session.add(client)
        db.session.commit()
        
        flash(f'Cliente "{name}" creado exitosamente.', 'success')
        return redirect(url_for('debt_client_pos', client_id=client.id))
    
    return redirect(url_for('debts'))


@app.route('/debts/client/<int:client_id>')
@login_required
@admin_only
def debt_client_pos(client_id):
    """POS view for a credit client - identical to caja but with client info."""
    client = db.session.get(CreditClient, client_id)
    if not client or client.store_id != current_user.store_id:
        flash('Cliente no encontrado.', 'error')
        return redirect(url_for('debts'))
    
    active_session = get_today_session()
    if not active_session:
        flash('Debes abrir caja primero para realizar ventas fiadas.', 'error')
        return redirect(url_for('session_open'))
    
    categories = Category.query.filter_by(store_id=current_user.store_id, visible_in_pos=True).order_by(Category.display_order).all()
    settings = get_store_settings()
    
    # Get all credit sales for this client with their sale items
    credit_sales = CreditSale.query.options(joinedload(CreditSale.sale)).filter_by(client_id=client_id).order_by(CreditSale.created_at.desc()).all()
    payments = CreditPayment.query.filter_by(client_id=client_id).order_by(CreditPayment.payment_date.desc()).all()
    
    return render_template('deudas_caja.html', client=client, categories=categories, 
                           settings=settings, credit_sales=credit_sales, payments=payments)


@app.route('/api/credit-payment', methods=['POST'])
@login_required
def api_credit_payment():
    """Record a payment against a client's credit balance."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Datos inválidos.'}), 400
        
        client_id = data.get('client_id')
        amount = data.get('amount', 0)
        payment_method = data.get('payment_method', 'efectivo')
        notes = data.get('notes', '')
        
        if not client_id:
            return jsonify({'success': False, 'message': 'Cliente no especificado.'}), 400
        
        client = db.session.get(CreditClient, client_id)
        if not client or client.store_id != current_user.store_id:
            return jsonify({'success': False, 'message': 'Cliente no encontrado.'}), 404
        
        if not isinstance(amount, int) or amount < 100:
            return jsonify({'success': False, 'message': 'El monto mínimo de pago es $100.'}), 400
        
        if amount > client.total_debt:
            return jsonify({'success': False, 'message': f'El monto excede la deuda total ({format_cop(client.total_debt)}).'}), 400
        
        # Record the payment
        payment = CreditPayment(
            client_id=client_id,
            amount=amount,
            payment_method=payment_method,
            notes=notes
        )
        db.session.add(payment)
        
        # Apply payment to oldest unpaid credit sales first (FIFO)
        remaining = amount
        pending_sales = CreditSale.query.filter_by(
            client_id=client_id, status='pendiente'
        ).order_by(CreditSale.created_at.asc()).all()
        
        for cs in pending_sales:
            if remaining <= 0:
                break
            if cs.balance <= remaining:
                remaining -= cs.balance
                cs.balance = 0
                cs.status = 'pagado'
            else:
                cs.balance -= remaining
                remaining = 0
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Pago de {format_cop(amount)} registrado exitosamente.',
            'new_total_debt': client.total_debt,
            'new_total_debt_formatted': format_cop(client.total_debt),
            'debt_status': client.debt_status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/debts/client/<int:client_id>/invoice')
@login_required
@admin_only
def debt_client_invoice(client_id):
    """Print a complete invoice for all credit purchases of a client."""
    client = db.session.get(CreditClient, client_id)
    if not client or client.store_id != current_user.store_id:
        flash('Cliente no encontrado.', 'error')
        return redirect(url_for('debts'))
    
    settings = get_store_settings()
    all_credit_sales = CreditSale.query.options(joinedload(CreditSale.sale).joinedload(Sale.items)).filter_by(client_id=client_id).order_by(CreditSale.created_at.asc()).all()
    pending_sales = [cs for cs in all_credit_sales if cs.status == 'pendiente']
    paid_sales = [cs for cs in all_credit_sales if cs.status == 'pagado']
    payments = CreditPayment.query.filter_by(client_id=client_id).order_by(CreditPayment.payment_date.asc()).all()
    
    return render_template('deudas_factura.html', client=client, settings=settings,
                           pending_sales=pending_sales, paid_sales=paid_sales,
                           credit_sales=all_credit_sales, payments=payments,
                           now=datetime.now())

@app.route('/cashiers')
@login_required
def cashiers():
    flash('El módulo de administración de cajeros estará disponible en el siguiente sprint.', 'info')
    return redirect(url_for('settings'))

@app.route('/settings/hardware')
@login_required
def settings_hardware():
    flash('El módulo de Hardware estará disponible en el siguiente sprint.', 'info')
    return redirect(url_for('settings'))

# ============================================================
# API REST BLUEPRINTS (Arquitectura en Capas)
# ============================================================
from controllers.user_controller import user_controller
from controllers.product_controller import product_controller
from controllers.sale_controller import sale_controller

app.register_blueprint(user_controller)
app.register_blueprint(product_controller)
app.register_blueprint(sale_controller)


# ============================================================
# STARTUP
# ============================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Seed: crear categorías por defecto para tiendas existentes sin categorías
        stores_without_cats = Store.query.filter(~Store.id.in_(
            db.session.query(Category.store_id).distinct()
        )).all()
        if stores_without_cats:
            default_categories = [
                {'name': 'Bebidas',          'slug': 'bebidas',          'image': 'Bebidas.jpg',          'description': 'Gaseosas, jugos, agua y más'},
                {'name': 'Lácteos',          'slug': 'lacteos',          'image': 'Lácteos.avif',         'description': 'Leche, queso, yogurt y derivados'},
                {'name': 'Despensa',         'slug': 'despensa',         'image': 'Despensa.jfif',        'description': 'Granos, aceites, enlatados y básicos'},
                {'name': 'Snacks',           'slug': 'snacks',           'image': 'Snacks.jfif',          'description': 'Papas, galletas, dulces y antojos'},
                {'name': 'Frescos',          'slug': 'frescos',          'image': 'frescos.webp',         'description': 'Frutas, verduras y productos frescos'},
                {'name': 'Limpieza y Aseo',  'slug': 'limpieza_y_aseo',  'image': 'limpieza_y_aseo.jfif', 'description': 'Jabones, detergentes y aseo del hogar'},
                {'name': 'Farmacia',         'slug': 'farmacia',         'image': 'Farmacia.jfif',        'description': 'Medicamentos y cuidado personal'},
                {'name': 'Mascotas',         'slug': 'mascotas',         'image': 'Mascotas.jfif',        'description': 'Alimentos y accesorios para mascotas'},
            ]
            for store in stores_without_cats:
                for order, cat_data in enumerate(default_categories, start=1):
                    cat = Category(
                        store_id=store.id,
                        name=cat_data['name'],
                        slug=cat_data['slug'],
                        image=cat_data['image'],
                        description=cat_data['description'],
                        display_order=order,
                        visible_in_pos=True
                    )
                    db.session.add(cat)
            db.session.commit()
            print(f"[SEED] Categorías por defecto creadas para {len(stores_without_cats)} tienda(s).")
        
    app.run(debug=True, port=5001)
