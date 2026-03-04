"""
License Generation CLI — genera keypair RSA e firma token licenza JWT.

Uso:
  python -m tools.admin_scripts.generate_license generate-keys
  python -m tools.admin_scripts.generate_license sign --client "gym-roma" --tier pro --months 12
  python -m tools.admin_scripts.generate_license verify data/license.key

Keypair salvate in ~/.fitmanager/ (PRIVATA: mai distribuire).
Chiave pubblica da copiare in data/license_public.pem per l'app.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt


KEYS_DIR = Path.home() / ".fitmanager"
PRIVATE_KEY_FILE = KEYS_DIR / "private_key.pem"
PUBLIC_KEY_FILE = KEYS_DIR / "public_key.pem"
LICENSE_ALGORITHM = "RS256"


def cmd_generate_keys(args: argparse.Namespace) -> None:
    """Genera keypair RSA 2048 in ~/.fitmanager/."""
    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    if PRIVATE_KEY_FILE.exists() and not args.force:
        print(f"Chiave privata gia' esistente: {PRIVATE_KEY_FILE}")
        print("Usa --force per sovrascrivere.")
        sys.exit(1)

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    PRIVATE_KEY_FILE.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    PUBLIC_KEY_FILE.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    print(f"Keypair generata:")
    print(f"  Privata: {PRIVATE_KEY_FILE}")
    print(f"  Pubblica: {PUBLIC_KEY_FILE}")
    print()
    print("IMPORTANTE: la chiave privata NON deve MAI essere distribuita.")
    print(f"Copia la pubblica nell'app: cp {PUBLIC_KEY_FILE} data/license_public.pem")


def cmd_sign(args: argparse.Namespace) -> None:
    """Firma un token licenza JWT con la chiave privata."""
    if not PRIVATE_KEY_FILE.exists():
        print(f"Chiave privata non trovata: {PRIVATE_KEY_FILE}")
        print("Esegui prima: python -m tools.admin_scripts.generate_license generate-keys")
        sys.exit(1)

    private_key_pem = PRIVATE_KEY_FILE.read_text(encoding="utf-8")

    exp = datetime.now(tz=timezone.utc) + timedelta(days=args.months * 30)

    claims = {
        "client_id": args.client,
        "tier": args.tier,
        "exp": int(exp.timestamp()),
    }
    if args.max_clients is not None:
        claims["max_clients"] = args.max_clients

    token = jwt.encode(claims, private_key_pem, algorithm=LICENSE_ALGORITHM)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(token, encoding="utf-8")

    print(f"Licenza firmata:")
    print(f"  Client: {args.client}")
    print(f"  Tier: {args.tier}")
    print(f"  Scadenza: {exp.strftime('%Y-%m-%d')}")
    if args.max_clients:
        print(f"  Max clienti: {args.max_clients}")
    print(f"  Output: {output_path}")


def cmd_verify(args: argparse.Namespace) -> None:
    """Verifica un token licenza usando check_license() dell'app."""
    token_path = Path(args.license_file)
    if not token_path.exists():
        print(f"File licenza non trovato: {token_path}")
        sys.exit(1)

    # Usa la pubblica da ~/.fitmanager/ se esiste, altrimenti quella dell'app
    pub_key = None
    if PUBLIC_KEY_FILE.exists():
        pub_key = PUBLIC_KEY_FILE.read_text(encoding="utf-8")

    from api.services.license import check_license

    result = check_license(token_path=token_path, public_key=pub_key)

    print(f"Status: {result.status}")
    print(f"Messaggio: {result.message}")
    if result.expires_at:
        print(f"Scadenza: {result.expires_at.strftime('%Y-%m-%d %H:%M UTC')}")
    if result.claims:
        print(f"Client: {result.claims.client_id}")
        print(f"Tier: {result.claims.tier}")
        if result.claims.max_clients:
            print(f"Max clienti: {result.claims.max_clients}")

    sys.exit(0 if result.is_valid else 1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FitManager License CLI — genera keypair e firma licenze JWT RSA.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # generate-keys
    gen = sub.add_parser("generate-keys", help="Genera keypair RSA 2048")
    gen.add_argument("--force", action="store_true", help="Sovrascrive keypair esistente")

    # sign
    sign = sub.add_parser("sign", help="Firma un token licenza")
    sign.add_argument("--client", required=True, help="ID cliente (es. gym-roma)")
    sign.add_argument("--tier", required=True, choices=["basic", "pro", "enterprise"], help="Tier licenza")
    sign.add_argument("--months", type=int, default=12, help="Durata in mesi (default 12)")
    sign.add_argument("--max-clients", type=int, default=None, help="Limite clienti (default illimitato)")
    sign.add_argument("--output", default="data/license.key", help="Path output (default data/license.key)")

    # verify
    ver = sub.add_parser("verify", help="Verifica un file licenza")
    ver.add_argument("license_file", help="Path al file .key da verificare")

    args = parser.parse_args()

    if args.command == "generate-keys":
        cmd_generate_keys(args)
    elif args.command == "sign":
        cmd_sign(args)
    elif args.command == "verify":
        cmd_verify(args)


if __name__ == "__main__":
    main()
