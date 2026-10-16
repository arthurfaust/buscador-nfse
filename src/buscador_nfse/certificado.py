"""Converte o certificado A1 (.pfx) em PEM temporário para uso com requests."""
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    Encoding, NoEncryption, PrivateFormat, pkcs12,
)

@contextmanager
def certificado_pem(caminho_pfx: Path, senha: str):
    """Gera (cert.pem, key.pem) temporários e apaga ao sair do bloco `with`."""
    dados = Path(caminho_pfx).read_bytes()
    chave, cert, cadeia = pkcs12.load_key_and_certificates(dados, senha.encode())
    if chave is None or cert is None:
        raise ValueError("O .pfx não contém chave privada e certificado")

    with tempfile.TemporaryDirectory(prefix="nfse_") as pasta:
        cert_path = os.path.join(pasta, "cert.pem")
        key_path = os.path.join(pasta, "key.pem")
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(Encoding.PEM))
            for c in cadeia or []:
                f.write(c.public_bytes(Encoding.PEM))
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(chave.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
        yield cert_path, key_path