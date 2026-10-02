"""Make the QR code for the slides: python deploy/make_qr.py <https URL> [out.png]

Refuses anything that is not https (a QR code on a slide must not send phones to a plain-http page), and refuses
URLs carrying credentials or tokens. qrcode (BSD) + Pillow."""
import sys
import urllib.parse

import qrcode


def main(url, out="reefprint_qr.png"):
    u = urllib.parse.urlparse(url)
    if u.scheme != "https":
        sys.exit("refused: the QR code must point to an https URL")
    if u.username or u.password or any(k in u.query.lower() for k in ("token", "key", "password", "session")):
        sys.exit("refused: never put credentials or tokens in a QR code")
    img = qrcode.make(url, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=2)
    img.save(out)
    print("wrote", out, "->", url)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(*sys.argv[1:3])
