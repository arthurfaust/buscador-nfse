"""Testes do sincronizador, usando uma API falsa (biblioteca `responses`)."""
import responses
from conftest import xml_compactado

from buscador_nfse.cliente import ClienteADN
from buscador_nfse.sincronizador import EstadoNSU, sincronizar

URL_BASE = "https://adn.exemplo/contribuintes"


def documento_falso(nsu: int, chave: str) -> dict:
    """Monta um documento no mesmo formato que a API devolve dentro do LoteDFe."""
    return {
        "NSU": nsu,
        "ChaveAcesso": chave,
        "TipoDocumento": "NFSE",
        "ArquivoXml": xml_compactado(f"<NFSe id='{chave}'/>"),
    }


def nao_mostrar_log(*_):
    """Substitui o `print` para os testes não poluírem a saída."""


@responses.activate
def test_baixa_todos_os_lotes_e_salva_o_ultimo_nsu(tmp_path):
    # A API falsa responde em dois lotes e depois diz que não há mais nada (404).
    responses.get(f"{URL_BASE}/DFe/0", json={"LoteDFe": [documento_falso(1, "A"), documento_falso(2, "B")]})
    responses.get(f"{URL_BASE}/DFe/2", json={"LoteDFe": [documento_falso(3, "C")]})
    responses.get(f"{URL_BASE}/DFe/3", status=404)
    estado = EstadoNSU(tmp_path / "nsu.txt")
    pasta_xml = tmp_path / "xml"

    total = sincronizar(ClienteADN(URL_BASE), pasta_xml, estado, pausa=0, log=nao_mostrar_log)

    assert total == 3
    assert estado.ler() == 3
    assert (pasta_xml / "NFSE_C_3.xml").read_bytes() == b"<NFSe id='C'/>"


@responses.activate
def test_continua_a_partir_do_nsu_salvo(tmp_path):
    estado = EstadoNSU(tmp_path / "nsu.txt")
    estado.gravar(10)
    # Só registramos a URL do NSU 10: se o sincronizador consultasse outro
    # NSU (ex.: 0), o `responses` lançaria um erro de conexão.
    responses.get(f"{URL_BASE}/DFe/10", status=404)

    total = sincronizar(ClienteADN(URL_BASE), tmp_path, estado, pausa=0, log=nao_mostrar_log)

    assert total == 0
