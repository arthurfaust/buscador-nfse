"""Testes do ClienteADN.

A biblioteca `responses` intercepta as chamadas do `requests`: nenhuma
requisição sai para a internet. Com `responses.get(url, ...)` definimos o
que a "API falsa" deve responder para aquela URL.
"""
import pytest
import requests
import responses

from buscador_nfse.cliente import ClienteADN

URL_BASE = "https://adn.exemplo/contribuintes"
CNPJ = "12345678000199"


@responses.activate
def test_consulta_dfe_envia_cnpj_como_parametro():
    # O matcher faz a API falsa só responder se o parâmetro cnpjConsulta for enviado.
    responses.get(
        f"{URL_BASE}/DFe/0",
        json={"LoteDFe": []},
        match=[responses.matchers.query_param_matcher({"cnpjConsulta": CNPJ})],
    )

    resposta = ClienteADN(URL_BASE).consultar_dfe(0, CNPJ)

    assert resposta == {"LoteDFe": []}


@responses.activate
def test_resposta_404_retorna_none():
    responses.get(f"{URL_BASE}/DFe/5", status=404)

    resposta = ClienteADN(URL_BASE).consultar_dfe(5)

    assert resposta is None


@responses.activate
def test_erro_do_servidor_lanca_http_error():
    responses.get(f"{URL_BASE}/DFe/0", status=500)

    with pytest.raises(requests.HTTPError):
        ClienteADN(URL_BASE).consultar_dfe(0)
