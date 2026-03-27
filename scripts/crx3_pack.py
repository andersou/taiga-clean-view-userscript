"""
Build a Chrome CRX3 file (magic Cr24, protobuf header, ZIP payload).
Compatible with the algorithm used by https://github.com/ahwayakchih/crx3 (RSA + SHA-256).

Requires: cryptography
"""

from __future__ import annotations

import hashlib
import struct
from pathlib import Path

CRX_MAGIC = b"Cr24"
CRX_VERSION_LE = struct.pack("<I", 3)
SIGNATURE_CONTEXT = b"CRX3 SignedData\x00"


def _encode_varint(n: int) -> bytes:
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _encode_signed_data(crx_id: bytes) -> bytes:
    """SignedData { optional bytes crx_id = 1; }"""
    return _encode_varint((1 << 3) | 2) + _encode_varint(len(crx_id)) + crx_id


def _encode_asymmetric_key_proof(public_key_der: bytes, signature: bytes) -> bytes:
    """AsymmetricKeyProof { optional bytes public_key = 1; optional bytes signature = 2; }"""
    b = bytearray()
    b.extend(_encode_varint((1 << 3) | 2) + _encode_varint(len(public_key_der)) + public_key_der)
    b.extend(_encode_varint((2 << 3) | 2) + _encode_varint(len(signature)) + signature)
    return bytes(b)


def _encode_crx_file_header(public_key_der: bytes, signature: bytes, signed_header_data: bytes) -> bytes:
    """CrxFileHeader with field 2 (sha256_with_rsa) and field 10000 (signed_header_data)."""
    proof = _encode_asymmetric_key_proof(public_key_der, signature)
    b = bytearray()
    b.extend(_encode_varint((2 << 3) | 2) + _encode_varint(len(proof)) + proof)
    tag_10k = (10000 << 3) | 2
    b.extend(_encode_varint(tag_10k) + _encode_varint(len(signed_header_data)) + signed_header_data)
    return bytes(b)


def load_or_create_rsa_pem(pem_path: Path):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if pem_path.is_file():
        data = pem_path.read_bytes()
        return serialization.load_pem_private_key(data, password=None)

    pem_path.parent.mkdir(parents=True, exist_ok=True)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pem_path.write_bytes(pem)
    return private_key


def pack_crx3(zip_bytes: bytes, private_key_pem_path: Path) -> bytes:
    """Return full .crx bytes from a ZIP archive (extension root layout)."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import serialization

    private_key = load_or_create_rsa_pem(private_key_pem_path)
    public_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    crx_id = hashlib.sha256(public_der).digest()[:16]
    signed_header_data = _encode_signed_data(crx_id)

    sign_payload = (
        SIGNATURE_CONTEXT
        + struct.pack("<I", len(signed_header_data))
        + signed_header_data
        + zip_bytes
    )

    signature = private_key.sign(sign_payload, padding.PKCS1v15(), hashes.SHA256())

    header_proto = _encode_crx_file_header(public_der, signature, signed_header_data)

    return CRX_MAGIC + CRX_VERSION_LE + struct.pack("<I", len(header_proto)) + header_proto + zip_bytes
