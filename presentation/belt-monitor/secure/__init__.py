"""REEFPRINT secure server components (PLAN-v8 Track S, docs/19).

store   SQLite schema (users, sessions, append-only ledger with triggers, checkpoints, uploads)
authn   scrypt passwords, server-side sessions, lockout, CSRF
rbac    deny-by-default route and event permissions
vault   AES-256-GCM at rest, Ed25519 + ML-DSA-65 signing keys, hybrid X25519 + ML-KEM-768 export
ledger  hash-chained decision record with hybrid post-quantum-signed checkpoints
ingest  CSV and image upload validation (EXIF stripped, encrypted at rest, guest expiry)
"""
