import responses

from conftest import xml_compactado
from buscador_nfse.cliente import ClienteADN
from buscador_nfse.sincronizador import EstadoNSU, sincronizar

URL = "https://adn.exemplo/contribuintes"

def doc(nsu, chave):
    return {"NSU": nsu, "ChaveAcesso": chave, "TipoDocumento": "NFSE",
            "ArquivoXml": xml_compactado(f"<NFSe id='{chave}'/>")}

@responses.activate
def test_baixa_lotes_e_salva_estado(tmp_path):
    responses.get(f"{URL}/DFe/0", json={"LoteDFe": [doc(1, "A"), doc(2, "B")]})
    responses.get(f"{URL}/DFe/2", json={"LoteDFe": [doc(3, "C")]})
    responses.get(f"{URL}/DFe/3", status=404)

    estado = EstadoNSU(tmp_path / "nsu.txt")
    total = sincronizar(ClienteADN(URL), tmp_path / "xml", estado, pausa=0, log=lambda *_: None)

    assert total == 3
    assert estado.ler() == 3
    assert (tmp_path / "xml" / "NFSE_C_3.xml").read_bytes() == b"<NFSe id='C'/>"

@responses.activate
def test_continua_de_onde_parou(tmp_path):
    estado = EstadoNSU(tmp_path / "nsu.txt")
    estado.gravar(10)
    responses.get(f"{URL}/DFe/10", status=404)
    assert sincronizar(ClienteADN(URL), tmp_path, estado, pausa=0, log=lambda *_: None) == 0