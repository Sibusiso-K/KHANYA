"""Deny-by-default permissions: which role may call which route, and which role may append which ledger event.

Guests (QR-code visitors) act only in a SANDBOX ledger (a separate database, reset daily). They may try every step of
the decision flow there, labelled DEMO, and can never write to the real decision record. The server enforces the
sandbox; this table only says which event types each staff role may append to the real ledger.
"""
ROLES = ("guest", "operator", "metallurgist", "mineralogist", "manager", "admin")
STAFF = {"operator", "metallurgist", "mineralogist", "manager"}
ANY = set(ROLES) - {"admin"}          # admin is CLI-only: no web session may act as admin

PUBLIC = {("POST", "/api/login"), ("POST", "/api/guest")}
ROUTES = {
    ("GET", "/api/me"): ANY,
    ("POST", "/api/logout"): ANY,
    ("POST", "/api/route"): ANY,
    ("POST", "/api/upload/csv"): {"guest", "metallurgist", "mineralogist"},
    ("POST", "/api/upload/image"): {"guest", "operator", "metallurgist", "mineralogist"},
    ("GET", "/api/uploads"): ANY,
    ("POST", "/api/ledger/event"): ANY,
    ("GET", "/api/ledger"): ANY,
    ("GET", "/api/ledger/verify"): ANY,
    ("POST", "/api/ledger/checkpoint"): {"guest", "metallurgist", "manager"},
}
EVENT_ROLES = {
    "advice_shown": STAFF,
    "acknowledge": {"operator", "metallurgist"},
    "fallback_applied": {"operator", "metallurgist"},
    "approve": {"metallurgist"},
    "modify": {"metallurgist"},
    "reject": {"metallurgist"},
    "escalate": {"operator", "metallurgist", "mineralogist"},
    "resolve_refusal": {"mineralogist", "metallurgist"},
    "outcome": {"mineralogist"},
    "note": STAFF,
}


def route_allowed(method, path, role):
    """None if the route does not exist (404), else True/False (403)."""
    roles = ROUTES.get((method, path))
    if roles is None:
        return None
    return role in roles


def event_allowed(event_type, role):
    """Real ledger: per-role rules. Guest: any known type, but only ever in the sandbox (enforced by the server)."""
    roles = EVENT_ROLES.get(event_type)
    if roles is None:
        return False
    return True if role == "guest" else role in roles
