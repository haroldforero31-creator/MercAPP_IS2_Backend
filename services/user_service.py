from repositories.user_repository import UserRepository
from dtos.user_dto import UserCreateDTO, UserUpdateDTO, UserLoginDTO, UserResponseDTO
from utilities.security import hash_password, verify_password

class UserService:
    """
    Capa de Servicio para Usuarios y Autenticación:
    Concentra la lógica de negocio y validaciones académicas.
    """

    @staticmethod
    def get_all_users(store_id: int = None):
        users = UserRepository.get_all(store_id)
        return UserResponseDTO.from_model_list(users)

    @staticmethod
    def get_user_by_id(user_id: int):
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None, "Usuario no encontrado."
        return UserResponseDTO.from_model(user), None

    @staticmethod
    def create_user(dto: UserCreateDTO):
        validation_errors = dto.validate()
        if validation_errors:
            return None, validation_errors

        existing = UserRepository.get_by_email(dto.email)
        if existing:
            return None, f"El correo '{dto.email}' ya se encuentra registrado."

        hashed = hash_password(dto.password)
        user = UserRepository.create(
            name=dto.name,
            email=dto.email,
            password_hash=hashed,
            is_admin=dto.is_admin,
            store_id=dto.store_id
        )
        return UserResponseDTO.from_model(user), None

    @staticmethod
    def update_user(user_id: int, dto: UserUpdateDTO):
        user = UserRepository.get_by_id(user_id)
        if not user:
            return None, "Usuario no encontrado."

        validation_errors = dto.validate()
        if validation_errors:
            return None, validation_errors

        if dto.email and dto.email != user.email:
            existing = UserRepository.get_by_email(dto.email)
            if existing and existing.id != user.id:
                return None, f"El correo '{dto.email}' ya está en uso."

        fields = {}
        if dto.name is not None:
            fields['name'] = dto.name
        if dto.email is not None:
            fields['email'] = dto.email
        if dto.is_admin is not None:
            fields['is_admin'] = dto.is_admin
        if dto.status is not None:
            fields['status'] = dto.status
        if dto.password:
            fields['password_hash'] = hash_password(dto.password)

        updated = UserRepository.update(user, **fields)
        return UserResponseDTO.from_model(updated), None

    @staticmethod
    def delete_user(user_id: int):
        user = UserRepository.get_by_id(user_id)
        if not user:
            return False, "Usuario no encontrado."
        UserRepository.delete(user)
        return True, None

    @staticmethod
    def authenticate(dto: UserLoginDTO):
        validation_errors = dto.validate()
        if validation_errors:
            return None, validation_errors

        user = UserRepository.get_by_email(dto.email)
        if not user or not verify_password(dto.password, user.password_hash):
            return None, "Credenciales incorrectas."

        if user.status != 'ACTIVO':
            return None, f"La cuenta se encuentra en estado '{user.status}'."

        return UserResponseDTO.from_model(user), None
