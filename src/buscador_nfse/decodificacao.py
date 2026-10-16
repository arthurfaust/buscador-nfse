"""Funções puras para interpretar as respostas do ADN."""
import base64
import gzip

def decodificar_xml(conteudo_b64: str) -> bytes:
    """Os XMLs do ADN vêm compactados em gzip e codificados em base64."""
    bruto = base64.b64decode(conteudo_b64)
    try:
        return gzip.decompress(bruto)
    except gzip.BadGzipFile:
        return bruto  # veio sem compactação

def campo(d: dict, *nomes, padrao=None):
    """Lê um campo tolerando PascalCase, camelCase ou minúsculas."""
    for nome in nomes:
        for chave in (nome, nome[0].lower() + nome[1:], nome.lower()):
            if chave in d:
                return d[chave]
    return padrao