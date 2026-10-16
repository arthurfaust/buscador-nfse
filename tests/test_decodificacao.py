import base64

from conftest import xml_compactado
from buscador_nfse.decodificacao import campo, decodificar_xml

def test_decodifica_gzip_base64():
    assert decodificar_xml(xml_compactado("<NFSe/>")) == b"<NFSe/>"

def test_decodifica_base64_sem_gzip():
    assert decodificar_xml(base64.b64encode(b"<NFSe/>").decode()) == b"<NFSe/>"

def test_campo_aceita_variacoes_de_nome():
    assert campo({"LoteDFe": 1}, "LoteDFe") == 1
    assert campo({"loteDFe": 2}, "LoteDFe") == 2
    assert campo({"nsu": 3}, "NSU") == 3
    assert campo({}, "NSU", padrao=0) == 0