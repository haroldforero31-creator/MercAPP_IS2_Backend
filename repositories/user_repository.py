from models.database import db
from models.user import User

class UserRepository:
    """
    Capa de Repositorio de Usuarios:
    Aisla y ejecuta todas las consultas a la base de datos (SELECT, INSERT, UPDATE, DELETE).
    """

    @staticmethod
    def get_all(store_id: int = None):
        query = User.query
        if store_id:
            query = query.filter_by(store_id=store_id)
        return query.all()

    @staticmethod
    def get_by_id(user_id: int):
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email: str):
        return User.query.filter_by(email=email.strip().lower()).first()

    @staticmethod
    def create(name: str, email: str, password_hash: str, is_admin: bool = True, store_id: int = 1):
        user = User(
            name=name,
            email=email.strip().lower(),
            password_hash=password_hash,
            is_admin=is_admin,
            store_id=store_id
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update(user: User, **kwargs):
        for field, value in kwargs.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        db.session.commit()
        return user

    @staticmethod
    def delete(user: User):
        db.session.delete(user)
        db.session.commit()
