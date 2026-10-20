import base64

from conftest import xml_compactado

from buscador_nfse.decodificacao import campo, decodificar_xml


def test_decodifica_xml_em_gzip_e_base64():
    conteudo_da_api = xml_compactado("<NFSe/>")

    assert decodificar_xml(conteudo_da_api) == b"<NFSe/>"


def test_decodifica_xml_somente_em_base64_sem_gzip():
    conteudo_da_api = base64.b64encode(b"<NFSe/>").decode()

    assert decodificar_xml(conteudo_da_api) == b"<NFSe/>"


def test_campo_aceita_pascal_case():
    assert campo({"LoteDFe": 1}, "LoteDFe") == 1


def test_campo_aceita_camel_case():
    assert campo({"loteDFe": 2}, "LoteDFe") == 2


def test_campo_aceita_minusculas():
    assert campo({"nsu": 3}, "NSU") == 3


def test_campo_inexistente_retorna_valor_padrao():
    assert campo({}, "NSU", padrao=0) == 0
