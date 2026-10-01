import re

class UserCreateDTO:
    """DTO para crear un usuario/administrador."""
    def __init__(self, name, email, password, is_admin=True, store_id=1):
        self.name = name.strip() if name else ""
        self.email = email.strip().lower() if email else ""
        self.password = password if password else ""
        self.is_admin = bool(is_admin)
        self.store_id = int(store_id) if store_id else 1

    def validate(self):
        errors = []
        if not self.name or len(self.name) < 2:
            errors.append("El nombre es obligatorio y debe tener al menos 2 caracteres.")
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not self.email or not re.match(email_regex, self.email):
            errors.append("Debe proporcionar un correo electrónico válido.")
        if not self.password or len(self.password) < 6:
            errors.append("La contraseña debe tener al menos 6 caracteres.")
        return errors


class UserUpdateDTO:
    """DTO para actualizar datos de un usuario."""
    def __init__(self, name=None, email=None, password=None, is_admin=None, status=None):
        self.name = name.strip() if name is not None else None
        self.email = email.strip().lower() if email is not None else None
        self.password = password if password is not None else None
        self.is_admin = bool(is_admin) if is_admin is not None else None
        self.status = status.strip().upper() if status is not None else None

    def validate(self):
        errors = []
        if self.name is not None and len(self.name) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres.")
        if self.email is not None:
            email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_regex, self.email):
                errors.append("Debe proporcionar un correo electrónico válido.")
        if self.password is not None and len(self.password) < 6:
            errors.append("La contraseña debe tener al menos 6 caracteres.")
        return errors


class UserLoginDTO:
    """DTO para autenticación en la API."""
    def __init__(self, email, password):
        self.email = email.strip().lower() if email else ""
        self.password = password if password else ""

    def validate(self):
        errors = []
        if not self.email:
            errors.append("El correo electrónico es requerido.")
        if not self.password:
            errors.append("La contraseña es requerida.")
        return errors


class UserResponseDTO:
    """DTO de salida: serializa el usuario omitiendo información sensible."""
    @staticmethod
    def from_model(user):
        if not user:
            return None
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "role": "Administrador" if user.is_admin else "Cajero",
            "status": user.status,
            "store_id": user.store_id,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else None
        }

    @staticmethod
    def from_model_list(users):
        return [UserResponseDTO.from_model(u) for u in users]
