import os
import pytest
from buscador_nfse.certificado import certificado_pem

def test_gera_pem_e_apaga_ao_sair(pfx_falso):
    caminho, senha = pfx_falso
    with certificado_pem(caminho, senha) as (cert, chave):
        assert open(cert).read().startswith("-----BEGIN CERTIFICATE-----")
        assert "PRIVATE KEY" in open(chave).read()
    assert not os.path.exists(cert)
    assert not os.path.exists(chave)

def test_senha_errada(pfx_falso):
    caminho, _ = pfx_falso
    with pytest.raises(ValueError):
        with certificado_pem(caminho, "errada"):
            pass