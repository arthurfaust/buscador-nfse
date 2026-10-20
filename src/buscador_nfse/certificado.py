"""Converte o certificado digital A1 (.pfx) em arquivos PEM temporários.

Por que isso é necessário?
    A API do ADN exige autenticação por certificado digital (mTLS). A biblioteca
    `requests` não lê arquivos .pfx diretamente: ela precisa de dois arquivos no
    formato PEM, um com o certificado e outro com a chave privada.

    Como a chave privada é um dado sensível, os arquivos PEM são criados numa
    pasta temporária e apagados automaticamente assim que deixam de ser usados.
"""
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    pkcs12,
)

# Permissão de arquivo "somente o dono pode ler e escrever" (rw-------).
# Evita que outros usuários da máquina leiam a chave privada.
PERMISSAO_SOMENTE_DONO = 0o600


@contextmanager
def certificado_pem(caminho_pfx: Path, senha: str):
    """Gera os arquivos PEM temporários e os apaga ao sair do bloco `with`.

    Exemplo de uso:
        with certificado_pem(Path("empresa.pfx"), "minha-senha") as (cert, chave):
            requests.get(url, cert=(cert, chave))
        # Aqui fora, os arquivos já foram apagados.

    Retorna (via `yield`) uma tupla `(caminho_do_certificado, caminho_da_chave)`.
    Lança `ValueError` se a senha estiver errada ou se o .pfx estiver incompleto.
    """
    conteudo_pfx = Path(caminho_pfx).read_bytes()
    chave_privada, certificado, cadeia_de_certificados = pkcs12.load_key_and_certificates(
        conteudo_pfx, senha.encode()
    )

    if chave_privada is None or certificado is None:
        raise ValueError("O .pfx não contém chave privada e certificado")

    # TemporaryDirectory apaga a pasta (e tudo dentro dela) ao sair do `with`.
    with tempfile.TemporaryDirectory(prefix="nfse_") as pasta_temporaria:
        caminho_certificado = os.path.join(pasta_temporaria, "cert.pem")
        caminho_chave = os.path.join(pasta_temporaria, "key.pem")

        _gravar_certificado(caminho_certificado, certificado, cadeia_de_certificados)
        _gravar_chave_privada(caminho_chave, chave_privada)

        yield caminho_certificado, caminho_chave


def _gravar_certificado(caminho: str, certificado, cadeia_de_certificados) -> None:
    """Grava o certificado seguido dos certificados intermediários da cadeia.

    A cadeia (autoridades certificadoras intermediárias) ajuda o servidor a
    validar o certificado. Ela pode não existir, por isso o `or []`.
    """
    with open(caminho, "wb") as arquivo:
        arquivo.write(certificado.public_bytes(Encoding.PEM))
        for certificado_intermediario in cadeia_de_certificados or []:
            arquivo.write(certificado_intermediario.public_bytes(Encoding.PEM))


def _gravar_chave_privada(caminho: str, chave_privada) -> None:
    """Grava a chave privada já criando o arquivo com permissão restrita.

    Usamos `os.open` em vez de `open` porque ele permite definir a permissão no
    momento da criação. Assim não existe nenhum instante em que o arquivo fique
    legível por outros usuários.
    """
    descritor = os.open(caminho, os.O_WRONLY | os.O_CREAT, PERMISSAO_SOMENTE_DONO)
    with os.fdopen(descritor, "wb") as arquivo:
        chave_em_pem = chave_privada.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        )
        arquivo.write(chave_em_pem)
