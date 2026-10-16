"""Configuração lida de variáveis de ambiente e do arquivo .env."""
from enum import Enum
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Ambiente(str, Enum):
    PRODUCAO = "producao"
    HOMOLOGACAO = "homologacao"

URLS_BASE = {
    Ambiente.PRODUCAO: "https://adn.nfse.gov.br/contribuintes",
    Ambiente.HOMOLOGACAO: "https://adn.producaorestrita.nfse.gov.br/contribuintes",
}

class Configuracao(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NFSE_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    pfx_path: Path
    pfx_senha: SecretStr  # SecretStr não aparece em print/log
    cnpj_consulta: str | None = None
    ambiente: Ambiente = Ambiente.HOMOLOGACAO
    pasta_saida: Path = Path("nfse_xml")
    pausa_segundos: float = 1.0

    @field_validator("cnpj_consulta", mode="before")
    @classmethod
    def limpar_cnpj(cls, v):
        if not v:
            return None
        digitos = "".join(c for c in str(v) if c.isdigit())
        if len(digitos) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")
        return digitos

    @property
    def url_base(self) -> str:
        return URLS_BASE[self.ambiente]