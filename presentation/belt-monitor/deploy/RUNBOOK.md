# REEFPRINT Live: deployment runbook (secure server)

**Status.** Prepared and tested locally. **Not deployed publicly.** A public URL (for the QR code on the slides) is a publishing decision for the team: host, account, cost and data policy. See §4.

## 1. Local, on the presentation laptop (works today)

```
cd presentation/belt-monitor
python -m pip install -r requirements-secure.txt
python manage.py init
python manage.py add-user lethabo metallurgist        # password at a hidden prompt (min 12 chars)
python manage.py add-user ops1 operator
python app_server.py                                   # http://127.0.0.1:8531/
```

- Visitors choose **Continue as guest**. Guests get a sandbox: the demo decision record, uploads deleted after 24 h, capped assistant use, separate signing keys.
- `?guest=1` in the URL skips the dialog, which is the form for a QR code.
- Tests: `python -m unittest test_secure_server -v` (17 security tests).
- The offline demo (`server.py`) still works with no sign-in.

## 2. Container

```
docker build -f deploy/Dockerfile -t reefprint-live .
docker run -d --name reefprint --read-only --tmpfs /tmp -v reefprint-data:/data \
  -e REEFPRINT_DATA_KEY="$(python -c "import os,base64;print(base64.b64encode(os.urandom(32)).decode())")" \
  -e REEFPRINT_HOSTS="demo.example.org" -e REEFPRINT_SECURE_COOKIES=1 -e REEFPRINT_TRUST_PROXY=1 \
  -p 127.0.0.1:8531:8531 reefprint-live
docker exec -it reefprint python manage.py add-user lethabo metallurgist
```

- **Keep `REEFPRINT_DATA_KEY` in a secret store, not in shell history.** Without it, backups cannot be restored.
- The container runs non-root with a read-only root filesystem and one writable volume, and binds to localhost only.

## 3. Public access without opening ports: Cloudflare Tunnel

The server stays on `127.0.0.1`. `cloudflared` makes an outbound-only connection to Cloudflare.

**What you get:**
- **TLS** at Cloudflare's edge.
- **Hybrid post-quantum key agreement (X25519MLKEM768)** where the visitor's browser supports it. Cloudflare applies it by default; for Tunnel it is "post-quantum by default, not by guarantee" **[S]**.

```
cloudflared tunnel login
cloudflared tunnel create reefprint
cloudflared tunnel route dns reefprint demo.example.org
cloudflared tunnel run --url http://127.0.0.1:8531 reefprint
```

**Then:**
1. Set `REEFPRINT_HOSTS=demo.example.org`, `REEFPRINT_SECURE_COOKIES=1` (adds `Secure` and HSTS) and `REEFPRINT_TRUST_PROXY=1` (rate limits use `CF-Connecting-IP`).
2. Generate the QR code: `python deploy/make_qr.py https://demo.example.org/?guest=1`.

## 4. Before anything is public (decisions for the team, not for the code)

- [ ] **Host and account.** Whose Cloudflare account and domain; or another host. Who pays, if anything.
- [ ] **Data policy for guest uploads.**
  - Photos are stripped and encrypted and deleted after 24 h; CSVs too.
  - Confirm that is acceptable, and add a one-line notice on the slide.
- [ ] **External LLM stays off** (`REEFPRINT_ALLOW_EXTERNAL_LLM` unset). Guests' questions are routed offline. Switch it on only with a key budget and the notice that question text leaves the machine.
- [ ] **Staff accounts.** Only accounts you create; no public sign-up.
- [ ] **The rule in docs/19:** no plant connection from this host, ever. It is a demo of public data.

## 5. Backups and ransomware

- `python manage.py backup /secure/offsite/reefprint-YYYYMMDD.bin` makes a consistent SQLite snapshot, AES-256-GCM sealed. Copy it **offline** (a removable disk or write-once storage).
- `python manage.py checkpoint cp.json` then email or print `cp.json`. Later, `verify-checkpoint cp.json` proves the record was not edited or truncated since.
- **Restore test:** decrypt with the data key to a scratch path, then open it with `sqlite3` and run `manage.py verify`. Do it once before the pilot, and record it in the BUILDLOG.
