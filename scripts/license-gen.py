#!/usr/bin/env python3
"""
Sentinel License Generator — v1.0
Generates encrypted license.dat + public.pem for cci-ft2-intelligence.
Usage:
chmod +x scripts/license-gen.py
./scripts/license-gen.py --install [--expiry DAYS]
"""
import argparse
import json
import os
import platform
import sys
import uuid
from datetime import datetime as dt
from datetime import timedelta, timezone

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


# ───────────────────────────────────────────────────────────────
# Windows Unicode Compatibility
# ───────────────────────────────────────────────────────────────
def safe_print(message: str) -> None:
    """طباعة آمنة متوافقة مع Windows وLinux"""
    try:
        print(message)
    except UnicodeEncodeError:
        replacements = {
            "✅": "[OK]",
            "❌": "[ERR]",
            "⚠️": "[WARN]",
            "🔒": "[LOCK]",
            "🛡️": "[SHIELD]",
            "🎯": "[TARGET]",
            "🚀": "[ROCKET]",
            "📁": "[DIR]",
            "📄": "[FILE]",
            "•": "-",
        }
        for emoji, text in replacements.items():
            message = message.replace(emoji, text)
        print(message)


# ───────────────────────────────────────────────────────────────
# ضبط encoding للـ stdout على Windows
# ───────────────────────────────────────────────────────────────
if sys.platform == "win32":
    try:
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except Exception:
        pass  # fallback


# ───────────────────────────────────────────────────────────────
# Cross-platform home directory
# ───────────────────────────────────────────────────────────────
def get_home_dir() -> str:
    """Return home directory cross-platform, respecting HOME override."""
    if "HOME" in os.environ:
        return os.environ["HOME"]
    elif sys.platform == "win32":
        return os.environ.get("USERPROFILE", os.path.expanduser("~"))
    else:
        return os.path.expanduser("~")


# ───────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate Sentinel license")
    parser.add_argument(
        "--install", action="store_true", help="Generate license for current machine"
    )
    parser.add_argument("--expiry", type=int, default=30, help="Trial duration in days")
    args = parser.parse_args()

    if not args.install:
        parser.print_help()
        return

    # 1. Generate keypair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # 2. Fingerprint
    machine_id = platform.node().lower()
    try:
        with open("/proc/sys/kernel/random/uuid", "r", encoding="utf-8") as f:
            os_uuid = f.read().strip()
    except Exception:
        os_uuid = str(uuid.getnode())

    install_ts = dt.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
    fingerprint = f"{machine_id}|{os_uuid}|{install_ts}"

    # 3. License payload
    expiry = (dt.now(timezone.utc) + timedelta(days=args.expiry)).replace(
        microsecond=0
    ).isoformat() + "Z"
    payload = {
        "fingerprint": fingerprint,
        "expiry": expiry,
        "install_time": install_ts,
        "signature": "",
    }

    # 4. Sign payload
    data_to_sign = json.dumps(
        {
            "fingerprint": payload["fingerprint"],
            "expiry": payload["expiry"],
            "install_time": payload["install_time"],
        },
        sort_keys=True,
    ).encode()
    signature = private_key.sign(data_to_sign, ec.ECDSA(hashes.SHA256()))
    payload["signature"] = signature.hex()

    # 5. Encrypt with AES-256-GCM
    def derive_key(fp: str) -> bytes:
        return HKDF(
            algorithm=SHA256(),
            length=32,
            salt=b"cci-ft2-license-salt",
            info=b"cci-ft2-license-key",
        ).derive(fp.encode())

    key = derive_key(fingerprint)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, json.dumps(payload).encode(), None)
    encrypted_license = nonce + ciphertext

    # 6. Save
    home = get_home_dir()
    license_dir = os.path.join(home, ".cci_ft2")
    os.makedirs(license_dir, exist_ok=True)
    license_path = os.path.join(license_dir, "license.dat")
    pub_path = os.path.join(license_dir, "public.pem")

    with open(license_path, "wb") as f:
        f.write(encrypted_license)
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(pub_path, "wb") as f:
        f.write(pub_pem)

    safe_print(f"✅ License generated at: {license_dir}/")
    safe_print("   • license.dat  (AES-256-GCM encrypted)")
    safe_print("   • public.pem   (ECDSA public key)")
    safe_print(f"   • Fingerprint: {fingerprint}")
    safe_print(f"   • Expiry: {expiry}")


if __name__ == "__main__":
    main()
