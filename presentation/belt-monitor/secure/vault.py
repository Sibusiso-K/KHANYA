"""Keys and cryptography.

* Data at rest: AES-256-GCM with a 32-byte data key (env REEFPRINT_DATA_KEY, base64) or, for a local demo, a key file
  in the data directory. A production site keeps the key outside the data volume (env/secret store/HSM): a key on the
  same disk as the data protects backups and exports, not a fully compromised host.
* Signatures: hybrid Ed25519 + ML-DSA-65 (FIPS 204). Both must verify. Keys are sealed with the data key.
* Exports to a named recipient: hybrid KEM X25519 + ML-KEM-768 (FIPS 203) -> HKDF-SHA256 -> AES-256-GCM.
pqcrypto wraps PQClean reference code; it is not a FIPS-validated module (docs/19 section 7).
"""
import base64
import json
import os
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pqcrypto.kem import ml_kem_768
from pqcrypto.sign import ml_dsa_65

RAW = serialization.Encoding.Raw
EXPORT_INFO = b"reefprint-export-v1"


def b64(b):
    return base64.b64encode(b).decode()


def b64d(s):
    return base64.b64decode(s)


class Vault:
    def __init__(self, keydir, data_key_b64=None):
        os.makedirs(keydir, exist_ok=True)
        self.keydir = keydir
        self.key = self._data_key(data_key_b64)
        self.aes = AESGCM(self.key)
        self._signing_keys()

    def _data_key(self, b64key):
        if b64key:
            k = b64d(b64key)
            if len(k) != 32:
                raise ValueError("REEFPRINT_DATA_KEY must be 32 bytes, base64")
            return k
        p = os.path.join(self.keydir, "data.key")
        if not os.path.exists(p):
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(secrets.token_bytes(32))
        with open(p, "rb") as f:
            k = f.read()
        if len(k) != 32:
            raise ValueError("data.key is corrupt")
        return k

    def seal(self, data, aad):
        nonce = secrets.token_bytes(12)
        return nonce + self.aes.encrypt(nonce, data, aad)

    def unseal(self, blob, aad):
        return self.aes.decrypt(blob[:12], blob[12:], aad)

    def _signing_keys(self):
        p = os.path.join(self.keydir, "signing.sealed")
        if os.path.exists(p):
            with open(p, "rb") as f:
                d = json.loads(self.unseal(f.read(), b"signing-keys").decode())
            self.ed_sk = ed25519.Ed25519PrivateKey.from_private_bytes(b64d(d["ed_sk"]))
            self.ml_pk, self.ml_sk = b64d(d["ml_pk"]), b64d(d["ml_sk"])
        else:
            self.ed_sk = ed25519.Ed25519PrivateKey.generate()
            self.ml_pk, self.ml_sk = ml_dsa_65.keygen()
            raw = self.ed_sk.private_bytes(RAW, serialization.PrivateFormat.Raw, serialization.NoEncryption())
            blob = self.seal(json.dumps({"ed_sk": b64(raw), "ml_pk": b64(self.ml_pk), "ml_sk": b64(self.ml_sk)}).encode(), b"signing-keys")
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(blob)
        self.ed_pk = self.ed_sk.public_key().public_bytes(RAW, serialization.PublicFormat.Raw)

    def public_keys(self):
        return {"ed25519": b64(self.ed_pk), "ml_dsa_65": b64(self.ml_pk)}

    def sign(self, msg):
        return {"ed25519": b64(self.ed_sk.sign(msg)), "ml_dsa_65": b64(ml_dsa_65.sign(self.ml_sk, msg))}


def verify_hybrid(msg, sigs, pubs):
    """True only if BOTH the Ed25519 and the ML-DSA-65 signatures verify."""
    try:
        ed25519.Ed25519PublicKey.from_public_bytes(b64d(pubs["ed25519"])).verify(b64d(sigs["ed25519"]), msg)
        ml_dsa_65.verify(b64d(pubs["ml_dsa_65"]), msg, b64d(sigs["ml_dsa_65"]))
        return True
    except Exception:
        return False


def recipient_keypair():
    x = x25519.X25519PrivateKey.generate()
    mpk, msk = ml_kem_768.keygen()
    pub = {"x25519": b64(x.public_key().public_bytes(RAW, serialization.PublicFormat.Raw)), "ml_kem_768": b64(mpk)}
    priv = {"x25519": b64(x.private_bytes(RAW, serialization.PrivateFormat.Raw, serialization.NoEncryption())), "ml_kem_768": b64(msk)}
    return pub, priv


def _kdf(ss1, ss2, eph_pub, kem_ct):
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=EXPORT_INFO + b"|" + eph_pub + kem_ct).derive(ss1 + ss2)


def seal_for(recipient_pub, data, aad=EXPORT_INFO):
    eph = x25519.X25519PrivateKey.generate()
    ss1 = eph.exchange(x25519.X25519PublicKey.from_public_bytes(b64d(recipient_pub["x25519"])))
    kem_ct, ss2 = ml_kem_768.encaps(b64d(recipient_pub["ml_kem_768"]))
    eph_pub = eph.public_key().public_bytes(RAW, serialization.PublicFormat.Raw)
    nonce = secrets.token_bytes(12)
    ct = AESGCM(_kdf(ss1, ss2, eph_pub, kem_ct)).encrypt(nonce, data, aad)
    return {"v": 1, "kem": "X25519+ML-KEM-768", "aead": "AES-256-GCM", "eph": b64(eph_pub), "kem_ct": b64(kem_ct), "nonce": b64(nonce), "ct": b64(ct)}


def open_for(recipient_priv, env, aad=EXPORT_INFO):
    x = x25519.X25519PrivateKey.from_private_bytes(b64d(recipient_priv["x25519"]))
    ss1 = x.exchange(x25519.X25519PublicKey.from_public_bytes(b64d(env["eph"])))
    ss2 = ml_kem_768.decaps(b64d(recipient_priv["ml_kem_768"]), b64d(env["kem_ct"]))
    return AESGCM(_kdf(ss1, ss2, b64d(env["eph"]), b64d(env["kem_ct"]))).decrypt(b64d(env["nonce"]), b64d(env["ct"]), aad)
