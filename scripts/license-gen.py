#!/usr/bin/env python3
"""
Sentinel License Generator — v1.0
Generates encrypted license.dat + public.pem for cci-ft2-intelligence.

Usage:
  chmod +x scripts/license-gen.py
  ./scripts/license-gen.py --install [--expiry DAYS]
"""

import argparse
import os
import json
import datetime
from datetime import datetime as dt, timezone
from datetime import timedelta
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.exceptions import InvalidSignature
import platform
import uuid

def main():
    parser = argparse.ArgumentParser(description="Generate Sentinel license")
    parser.add_argument("--install", action="store_true", help="Generate license for current machine")
    parser.add_argument("--expiry", type=int, default=30, help="Trial duration in days")
    args = parser.parse_args()

    if not args.install:
        parser.print_help()
        return

    # 1. Generate keypair
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # 2. Fingerprint (machine_id | os_uuid | install_time)
    machine_id = platform.node().lower()
    try:
        with open("/proc/sys/kernel/random/uuid", "r") as f:
            os_uuid = f.read().strip()
    except Exception:
        os_uuid = str(uuid.getnode())
    
    # ✅ التصحيح: استخدام dt.now(timezone.utc) بدل datetime.utcnow()
    install_ts = dt.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"

    fingerprint = f"{machine_id}|{os_uuid}|{install_ts}"

    # 3. License payload
    expiry = (dt.now(timezone.utc) + timedelta(days=args.expiry)).replace(microsecond=0).isoformat() + "Z"
    payload = {
        "fingerprint": fingerprint,
        "expiry": expiry,
        "install_time": install_ts,
        "signature": ""
    }

    # 4. Sign payload
    data_to_sign = json.dumps({
        "fingerprint": payload["fingerprint"],
        "expiry": payload["expiry"],
        "install_time": payload["install_time"]
    }, sort_keys=True).encode()
    signature = private_key.sign(data_to_sign, ec.ECDSA(hashes.SHA256()))
    payload["signature"] = signature.hex()

    # 5. Encrypt with AES-256-GCM
    def derive_key(fp: str) -> bytes:
        return HKDF(
            algorithm=SHA256(),
            length=32,
            salt=b"cci-ft2-license-salt",
            info=b"cci-ft2-license-key"
        ).derive(fp.encode())

    key = derive_key(fingerprint)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, json.dumps(payload).encode(), None)
    encrypted_license = nonce + ciphertext

    # 6. Save
    home = os.path.expanduser("~")
    license_dir = os.path.join(home, ".cci_ft2")
    os.makedirs(license_dir, exist_ok=True)

    license_path = os.path.join(license_dir, "license.dat")
    pub_path = os.path.join(license_dir, "public.pem")

    with open(license_path, "wb") as f:
        f.write(encrypted_license)

    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(pub_path, "wb") as f:
        f.write(pub_pem)

    print(f"✅ License generated at: {license_dir}/")
    print(f"   • license.dat  (AES-256-GCM encrypted)")
    print(f"   • public.pem   (ECDSA public key)")
    print(f"   • Fingerprint: {fingerprint}")
    print(f"   • Expiry: {expiry}")

if __name__ == "__main__":
    main()