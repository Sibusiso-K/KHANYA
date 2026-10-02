"""Passwords (scrypt), server-side sessions, lockout, CSRF. Stdlib only."""
import base64
import hashlib
import hmac
import secrets
import time

SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1, "dklen": 32, "maxmem": 64 * 1024 * 1024}
IDLE_S, ABS_S, GUEST_ABS_S = 30 * 60, 12 * 3600, 2 * 3600
MAX_FAILED, LOCK_S = 5, 15 * 60
COMMON = {"password1234", "123456789012", "qwertyuiop12", "reefprint123", "platinum1234", "letmein12345"}
_DUMMY = None


def _b64(b):
    return base64.b64encode(b).decode()


def hash_password(pw):
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(pw.encode("utf-8"), salt=salt, **SCRYPT)
    return f"scrypt${SCRYPT['n']}${SCRYPT['r']}${SCRYPT['p']}${_b64(salt)}${_b64(dk)}"


def verify_password(pw, stored):
    try:
        _, n, r, p, salt, dk = stored.split("$")
        got = hashlib.scrypt(pw.encode("utf-8"), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p),
                             dklen=len(base64.b64decode(dk)), maxmem=SCRYPT["maxmem"])
        return hmac.compare_digest(got, base64.b64decode(dk))
    except Exception:
        return False


def password_problem(pw):
    if len(pw) < 12:
        return "at least 12 characters"
    if pw.lower() in COMMON or len(set(pw)) < 5:
        return "too common or too repetitive"
    return None


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def login(con, username, pw, now=None):
    """Returns (token, csrf, role) or raises PermissionError with a generic message (no user enumeration)."""
    global _DUMMY
    now = now or time.time()
    row = con.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if row is None:
        _DUMMY = _DUMMY or hash_password(secrets.token_urlsafe(16))
        verify_password(pw, _DUMMY)  # equalise timing
        raise PermissionError("invalid credentials")
    if row["disabled"] or row["locked_until"] > now:
        verify_password(pw, row["pw"])
        raise PermissionError("invalid credentials")
    if not verify_password(pw, row["pw"]):
        failed = row["failed"] + 1
        locked = now + LOCK_S if failed >= MAX_FAILED else 0
        con.execute("UPDATE users SET failed = ?, locked_until = ? WHERE id = ?", (0 if locked else failed, locked, row["id"]))
        raise PermissionError("invalid credentials")
    con.execute("UPDATE users SET failed = 0, locked_until = 0 WHERE id = ?", (row["id"],))
    return _new_session(con, row["id"], row["role"], f"u{row['id']}", now)


def guest(con, now=None):
    now = now or time.time()
    return _new_session(con, None, "guest", "guest-" + secrets.token_hex(4), now)


def _new_session(con, user_id, role, actor, now):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    con.execute("INSERT INTO sessions(token_hash, user_id, role, actor, csrf, created, last_seen) VALUES (?,?,?,?,?,?,?)",
                (_token_hash(token), user_id, role, actor, csrf, now, now))
    return token, csrf, role


def session(con, token, now=None):
    """The live session for a cookie token, or None. Applies idle and absolute timeouts."""
    if not token or len(token) > 100:
        return None
    now = now or time.time()
    row = con.execute("SELECT * FROM sessions WHERE token_hash = ?", (_token_hash(token),)).fetchone()
    if row is None:
        return None
    limit = GUEST_ABS_S if row["role"] == "guest" else ABS_S
    if now - row["last_seen"] > IDLE_S or now - row["created"] > limit:
        con.execute("DELETE FROM sessions WHERE token_hash = ?", (row["token_hash"],))
        return None
    if row["user_id"] is not None:
        u = con.execute("SELECT disabled, role FROM users WHERE id = ?", (row["user_id"],)).fetchone()
        if u is None or u["disabled"] or u["role"] != row["role"]:
            con.execute("DELETE FROM sessions WHERE token_hash = ?", (row["token_hash"],))
            return None
    con.execute("UPDATE sessions SET last_seen = ? WHERE token_hash = ?", (now, row["token_hash"]))
    return dict(row)


def logout(con, token):
    if token:
        con.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


def csrf_ok(sess, header_value):
    return bool(sess) and bool(header_value) and hmac.compare_digest(sess["csrf"], header_value)


def create_user(con, username, role, pw):
    problem = password_problem(pw)
    if problem:
        raise ValueError("password " + problem)
    con.execute("INSERT INTO users(username, role, pw, created) VALUES (?,?,?,?)", (username, role, hash_password(pw), time.time()))
