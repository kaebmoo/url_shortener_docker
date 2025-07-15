# shortener_app/keygen.py

import secrets
import string

from sqlalchemy.orm import Session

import crud


def create_random_key(length: int = 5) -> str:
    # chars = string.ascii_uppercase + string.digits
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))

def create_unique_random_key(db: Session) -> str:
    key = create_random_key()
    while crud.get_db_url_by_key(db, key):
        key = create_random_key()
    return key

def is_valid_custom_key(key: str) -> bool:
    chars = string.ascii_letters + string.digits
    return all(c in chars for c in key)