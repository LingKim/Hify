"""Password hashing helpers for local account authentication."""

import hashlib
import hmac
import secrets

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 390000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return a salted password hash suitable for storage."""
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    ).hex()
    return (
        f"{PASSWORD_HASH_ALGORITHM}"
        f"${PASSWORD_HASH_ITERATIONS}"
        f"${salt}"
        f"${digest}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether the raw password matches the stored hash."""
    try:
        algorithm, iterations_value, salt, expected_digest = (
            password_hash.split("$", 3)
        )
        iterations = int(iterations_value)
    except ValueError:
        return False

    if algorithm != PASSWORD_HASH_ALGORITHM:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return hmac.compare_digest(actual_digest, expected_digest)
