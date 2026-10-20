import os

import pytest

from buscador_nfse.certificado import certificado_pem


def test_gera_arquivos_pem_e_apaga_ao_sair_do_with(pfx_falso):
    caminho_pfx, senha = pfx_falso

    with certificado_pem(caminho_pfx, senha) as (caminho_cert, caminho_chave):
        # Dentro do `with`, os arquivos existem e estão no formato PEM.
        with open(caminho_cert) as arquivo:
            assert arquivo.read().startswith("-----BEGIN CERTIFICATE-----")
        with open(caminho_chave) as arquivo:
            assert "PRIVATE KEY" in arquivo.read()

    # Fora do `with`, os arquivos temporários já foram apagados.
    assert not os.path.exists(caminho_cert)
    assert not os.path.exists(caminho_chave)


def test_senha_errada_lanca_value_error(pfx_falso):
    caminho_pfx, _senha_correta = pfx_falso

    with pytest.raises(ValueError):
        with certificado_pem(caminho_pfx, "senha-errada"):
            pass
