import base64
import datetime as dt
import gzip

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
from cryptography.x509.oid import NameOID


@pytest.fixture
def pfx_falso(tmp_path):
    """Gera um .pfx autoassinado só para teste (não é ICP-Brasil)."""
    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA TESTE:12345678000199")])
    agora = dt.datetime.now(dt.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(nome).issuer_name(nome)
            .public_key(chave.public_key()).serial_number(1)
            .not_valid_before(agora).not_valid_after(agora + dt.timedelta(days=1))
            .sign(chave, hashes.SHA256()))
    dados = pkcs12.serialize_key_and_certificates(
        b"teste", chave, cert, None, BestAvailableEncryption(b"senha123"))
    caminho = tmp_path / "teste.pfx"
    caminho.write_bytes(dados)
    return caminho, "senha123"


def xml_compactado(xml: str) -> str:
    """Simula o formato da API: gzip + base64."""
    return base64.b64encode(gzip.compress(xml.encode())).decode()