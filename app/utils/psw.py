from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def generate_user_uuid():
    import uuid

    return "user-" + uuid.uuid4().hex


def generate_random_username(phone: str):
    import uuid

    return phone + "-" + uuid.uuid4().hex[:4]
