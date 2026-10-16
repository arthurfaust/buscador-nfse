import pytest
import requests
import responses

from buscador_nfse.cliente import ClienteADN

URL = "https://adn.exemplo/contribuintes"

@responses.activate
def test_consulta_dfe_envia_cnpj():
    responses.get(f"{URL}/DFe/0", json={"LoteDFe": []},
                  match=[responses.matchers.query_param_matcher({"cnpjConsulta": "12345678000199"})])
    assert ClienteADN(URL).consultar_dfe(0, "12345678000199") == {"LoteDFe": []}

@responses.activate
def test_404_vira_none():
    responses.get(f"{URL}/DFe/5", status=404)
    assert ClienteADN(URL).consultar_dfe(5) is None

@responses.activate
def test_erro_do_servidor_levanta_excecao():
    responses.get(f"{URL}/DFe/0", status=500)
    with pytest.raises(requests.HTTPError):
        ClienteADN(URL).consultar_dfe(0)