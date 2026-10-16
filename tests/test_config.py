import pytest
from pydantic import ValidationError

from buscador_nfse.config import Ambiente, Configuracao

def test_le_variaveis_de_ambiente(monkeypatch):
    monkeypatch.setenv("NFSE_PFX_PATH", "cert.pfx")
    monkeypatch.setenv("NFSE_PFX_SENHA", "segredo")
    monkeypatch.setenv("NFSE_CNPJ_CONSULTA", "12.345.678/0001-99")
    cfg = Configuracao(_env_file=None)
    assert cfg.cnpj_consulta == "12345678000199"
    assert cfg.ambiente is Ambiente.HOMOLOGACAO
    assert "producaorestrita" in cfg.url_base

def test_senha_nao_vaza_em_print(monkeypatch):
    monkeypatch.setenv("NFSE_PFX_PATH", "cert.pfx")
    monkeypatch.setenv("NFSE_PFX_SENHA", "segredo")
    cfg = Configuracao(_env_file=None)
    assert "segredo" not in repr(cfg)
    assert cfg.pfx_senha.get_secret_value() == "segredo"

def test_cnpj_invalido(monkeypatch):
    monkeypatch.setenv("NFSE_PFX_PATH", "cert.pfx")
    monkeypatch.setenv("NFSE_PFX_SENHA", "x")
    monkeypatch.setenv("NFSE_CNPJ_CONSULTA", "123")
    with pytest.raises(ValidationError):
        Configuracao(_env_file=None)