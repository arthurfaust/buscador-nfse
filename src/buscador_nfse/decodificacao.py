"""Funções auxiliares para interpretar as respostas do ADN.

São funções "puras": não acessam rede nem disco, só transformam dados.
Por isso são fáceis de testar.
"""
import base64
import gzip


def decodificar_xml(conteudo_base64: str) -> bytes:
    """Transforma o campo `ArquivoXml` da API no XML original.

    A API envia o XML compactado com gzip e depois codificado em base64
    (base64 transforma bytes em texto, para caber dentro do JSON).
    Fazemos o caminho inverso: base64 → bytes → descompacta o gzip.

    Se o conteúdo não estiver compactado, devolvemos os bytes como vieram.
    """
    conteudo_bruto = base64.b64decode(conteudo_base64)
    try:
        return gzip.decompress(conteudo_bruto)
    except gzip.BadGzipFile:
        return conteudo_bruto


def campo(dicionario: dict, *nomes: str, padrao=None):
    """Lê um campo do JSON aceitando variações de maiúsculas/minúsculas.

    A API não é consistente no formato dos nomes, então para cada nome
    informado tentamos três versões. Exemplo para "LoteDFe":
        "LoteDFe" (PascalCase), "loteDFe" (camelCase) e "lotedfe" (minúsculas).

    Também é possível passar vários nomes alternativos; o primeiro encontrado
    é retornado. Se nenhum existir, retorna `padrao`.

    Exemplo:
        campo({"nsu": 3}, "NSU")            → 3
        campo({}, "NSU", padrao=0)          → 0
    """
    for nome in nomes:
        pascal_case = nome
        camel_case = nome[0].lower() + nome[1:]
        minusculas = nome.lower()

        for variacao in (pascal_case, camel_case, minusculas):
            if variacao in dicionario:
                return dicionario[variacao]

    return padrao
