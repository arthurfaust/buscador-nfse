"""Testes da Configuracao.

`monkeypatch.setenv` define uma variável de ambiente só durante o teste.
`_env_file=None` faz a Configuracao ignorar o arquivo .env da máquina, para
que o resultado dependa apenas do que o teste definiu.
"""
import pytest
from pydantic import ValidationError

from buscador_nfse.config import Ambiente, Configuracao


@pytest.fixture
def variaveis_obrigatorias(monkeypatch):
    """Define as variáveis sem as quais a Configuracao não pode ser criada."""
    monkeypatch.setenv("NFSE_PFX_PATH", "cert.pfx")
    monkeypatch.setenv("NFSE_PFX_SENHA", "segredo")


def test_le_variaveis_de_ambiente_e_limpa_cnpj(variaveis_obrigatorias, monkeypatch):
    monkeypatch.setenv("NFSE_CNPJ_CONSULTA", "12.345.678/0001-99")

    config = Configuracao(_env_file=None)

    assert config.cnpj_consulta == "12345678000199"  # pontuação removida
    assert config.ambiente is Ambiente.HOMOLOGACAO  # valor padrão
    assert "producaorestrita" in config.url_base


def test_senha_nao_aparece_ao_imprimir_a_configuracao(variaveis_obrigatorias):
    config = Configuracao(_env_file=None)

    assert "segredo" not in repr(config)
    assert config.pfx_senha.get_secret_value() == "segredo"


def test_cnpj_com_quantidade_errada_de_digitos_e_rejeitado(variaveis_obrigatorias, monkeypatch):
    monkeypatch.setenv("NFSE_CNPJ_CONSULTA", "123")

    with pytest.raises(ValidationError):
        Configuracao(_env_file=None)
