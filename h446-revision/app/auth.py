"""Password checking, session cookies and a simple login rate limit.

Everything here uses the Python standard library only.

Password hash format:  scrypt:<n>:<r>:<p>:<salt>:<hash>
    salt and hash are base64url without padding. There are deliberately no
    '$' characters, because Docker Compose treats '$' in .env files as the
    start of a variable name.

Session cookie format: <expiry unix seconds>.<signature>
    signature = HMAC-SHA256(secret_key, expiry), base64url. The server keeps
    no session table: a valid signature on an unexpired timestamp is a login.
"""

import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque

COOKIE_NAME = "h446_session"

# scrypt cost settings: n=2**15 takes roughly 50-100 ms, which is fine for a
# single user and slow for anyone guessing.
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**15, 8, 1
SCRYPT_MAXMEM = 64 * 1024 * 1024


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R,
                            p=SCRYPT_P, maxmem=SCRYPT_MAXMEM, dklen=32)
    return f"scrypt:{SCRYPT_N}:{SCRYPT_R}:{SCRYPT_P}:{_b64e(salt)}:{_b64e(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt, expected = stored.split(":")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=_b64d(salt), n=int(n), r=int(r),
                                p=int(p), maxmem=SCRYPT_MAXMEM, dklen=len(_b64d(expected)))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, _b64d(expected))


def make_session_token(secret_key: str, days: int, now: float | None = None) -> str:
    expiry = str(int((now or time.time()) + days * 86400))
    sig = hmac.new(secret_key.encode(), expiry.encode(), hashlib.sha256).digest()
    return f"{expiry}.{_b64e(sig)}"


def check_session_token(token: str | None, secret_key: str, now: float | None = None) -> bool:
    if not token or "." not in token:
        return False
    expiry, sig = token.split(".", 1)
    expected = hmac.new(secret_key.encode(), expiry.encode(), hashlib.sha256).digest()
    try:
        if not hmac.compare_digest(_b64d(sig), expected):
            return False
        return int(expiry) > (now or time.time())
    except (ValueError, TypeError):
        return False


class LoginRateLimiter:
    """Allows `limit` failed logins per client IP in a sliding `window` (seconds)."""

    def __init__(self, limit: int = 5, window: int = 15 * 60):
        self.limit, self.window = limit, window
        self.failures: dict[str, deque] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> deque:
        q = self.failures[key]
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def blocked(self, key: str, now: float | None = None) -> bool:
        return len(self._prune(key, now or time.time())) >= self.limit

    def record_failure(self, key: str, now: float | None = None) -> None:
        now = now or time.time()
        self._prune(key, now).append(now)

    def reset(self, key: str) -> None:
        self.failures.pop(key, None)
