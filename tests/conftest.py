"""Fixtures e funções auxiliares compartilhadas entre os testes.

O pytest carrega este arquivo automaticamente. Qualquer função marcada com
`@pytest.fixture` pode ser recebida como parâmetro por um teste, pelo nome.
"""
import base64
import datetime as dt
import gzip

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
from cryptography.x509.oid import NameOID

SENHA_PFX_FALSO = "senha123"


@pytest.fixture
def pfx_falso(tmp_path):
    """Cria um certificado .pfx autoassinado, válido só para os testes.

    Não é um certificado ICP-Brasil de verdade e não funciona na API real.
    Retorna a tupla `(caminho_do_pfx, senha)`.

    `tmp_path` é uma fixture do próprio pytest: uma pasta temporária que é
    apagada depois do teste.
    """
    chave_privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "EMPRESA TESTE:12345678000199")])
    agora = dt.datetime.now(dt.timezone.utc)

    # Autoassinado: o emissor (issuer) é o próprio titular (subject).
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(chave_privada.public_key())
        .serial_number(1)
        .not_valid_before(agora)
        .not_valid_after(agora + dt.timedelta(days=1))
        .sign(chave_privada, hashes.SHA256())
    )

    conteudo_pfx = pkcs12.serialize_key_and_certificates(
        name=b"teste",
        key=chave_privada,
        cert=certificado,
        cas=None,
        encryption_algorithm=BestAvailableEncryption(SENHA_PFX_FALSO.encode()),
    )
    caminho = tmp_path / "teste.pfx"
    caminho.write_bytes(conteudo_pfx)
    return caminho, SENHA_PFX_FALSO


def xml_compactado(xml: str) -> str:
    """Simula o formato em que a API envia os XMLs: gzip + base64."""
    xml_gzip = gzip.compress(xml.encode())
    return base64.b64encode(xml_gzip).decode()
