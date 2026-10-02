"""Admin CLI for the secure server. Admin actions are CLI-only by design: there is no web admin to attack.

    python manage.py init
    python manage.py add-user <username> <operator|metallurgist|mineralogist|manager>     (password at a hidden prompt)
    python manage.py hash-password                 scrypt hash for REEFPRINT_SEED_USERS on a host with no shell (hidden prompt)
    python manage.py disable <username>
    python manage.py users
    python manage.py verify                       chain check of the real ledger
    python manage.py checkpoint <out.json>        sign the head (Ed25519 + ML-DSA-65); keep the file OFF this server
    python manage.py verify-checkpoint <in.json>  proves no edit or truncation since that checkpoint
    python manage.py backup <out.bin>             consistent SQLite snapshot, AES-256-GCM sealed (copy it offline)
    python manage.py recipient-keygen <name>      hybrid X25519 + ML-KEM-768 keypair for receiving exports
    python manage.py export-ledger <recipient.pub.json> <out.json>   ledger encrypted to that recipient
"""
import getpass
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from secure import authn, ledger, store  # noqa: E402
from secure import vault as vlt  # noqa: E402

DATA = Path(os.environ.get("REEFPRINT_DATA", str(ROOT / "data_secure")))
DB = DATA / "reefprint.db"


def vault():
    return vlt.Vault(str(DATA / "keys"), os.environ.get("REEFPRINT_DATA_KEY"))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    DATA.mkdir(parents=True, exist_ok=True)
    store.init(str(DB))
    con = store.connect(str(DB))
    if cmd == "init":
        vault()
        print("initialised", DATA)
    elif cmd == "add-user":
        name, role = args
        if role not in ("operator", "metallurgist", "mineralogist", "manager"):
            sys.exit("role must be operator, metallurgist, mineralogist or manager (admin is CLI-only)")
        pw = os.environ.get("REEFPRINT_NEW_PASSWORD") or getpass.getpass("password (min 12 chars): ")
        authn.create_user(con, name, role, pw)
        print("created", name, role)
    elif cmd == "hash-password":
        pw = getpass.getpass("password (min 12 chars): ")
        problem = authn.password_problem(pw)
        if problem:
            sys.exit("password " + problem)
        print(authn.hash_password(pw))
    elif cmd == "disable":
        con.execute("UPDATE users SET disabled = 1 WHERE username = ?", (args[0],))
        con.execute("DELETE FROM sessions WHERE user_id = (SELECT id FROM users WHERE username = ?)", (args[0],))
        print("disabled", args[0])
    elif cmd == "users":
        for r in con.execute("SELECT username, role, disabled, failed, locked_until FROM users ORDER BY username"):
            print(dict(r))
    elif cmd == "verify":
        print(json.dumps(ledger.verify(con)))
    elif cmd == "checkpoint":
        doc = ledger.checkpoint(con, vault())
        Path(args[0]).write_text(json.dumps(doc, indent=1))
        print("checkpoint seq", doc["seq"], "written to", args[0], "- store it off this server")
    elif cmd == "verify-checkpoint":
        print(json.dumps(ledger.verify_checkpoint(con, json.loads(Path(args[0]).read_text()))))
    elif cmd == "backup":
        with tempfile.TemporaryDirectory() as td:
            snap = os.path.join(td, "snap.db")
            dst = sqlite3.connect(snap)
            con.backup(dst)
            dst.close()
            blob = vault().seal(Path(snap).read_bytes(), b"reefprint-backup")
        Path(args[0]).write_bytes(blob)
        print("sealed backup", len(blob), "bytes ->", args[0], "(copy offline; restore needs the data key)")
    elif cmd == "recipient-keygen":
        pub, priv = vlt.recipient_keypair()
        Path(args[0] + ".pub.json").write_text(json.dumps(pub))
        fd = os.open(args[0] + ".priv.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(priv))
        print("wrote", args[0] + ".pub.json", "and", args[0] + ".priv.json (keep private)")
    elif cmd == "export-ledger":
        rows = [dict(r) for r in con.execute("SELECT * FROM ledger ORDER BY seq")]
        env = vlt.seal_for(json.loads(Path(args[0]).read_text()), json.dumps(rows).encode())
        Path(args[1]).write_text(json.dumps(env))
        print("exported", len(rows), "events, sealed with X25519 + ML-KEM-768 ->", args[1])
    else:
        print(__doc__)
        return 2
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
