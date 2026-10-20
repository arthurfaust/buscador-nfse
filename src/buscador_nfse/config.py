"""Configuração da aplicação, lida de variáveis de ambiente e do arquivo .env.

O pydantic-settings faz o trabalho pesado: para cada campo da classe
`Configuracao`, ele procura uma variável de ambiente com o prefixo `NFSE_`.
Exemplo: o campo `pfx_senha` é lido da variável `NFSE_PFX_SENHA`.
Veja o arquivo `.env.example` para a lista completa.
"""
from enum import Enum
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

QUANTIDADE_DIGITOS_CNPJ = 14


class Ambiente(str, Enum):
    """Ambientes disponíveis da API do ADN.

    - PRODUCAO: notas reais.
    - HOMOLOGACAO: ambiente de testes ("produção restrita").
    """

    PRODUCAO = "producao"
    HOMOLOGACAO = "homologacao"


URLS_BASE = {
    Ambiente.PRODUCAO: "https://adn.nfse.gov.br/contribuintes",
    Ambiente.HOMOLOGACAO: "https://adn.producaorestrita.nfse.gov.br/contribuintes",
}


class Configuracao(BaseSettings):
    """Todas as opções da aplicação em um só lugar.

    Campos sem valor padrão (`pfx_path` e `pfx_senha`) são obrigatórios: se a
    variável de ambiente não existir, o pydantic lança um `ValidationError`.
    """

    model_config = SettingsConfigDict(
        env_prefix="NFSE_",  # NFSE_PFX_PATH, NFSE_PFX_SENHA, ...
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignora variáveis do .env que não são campos desta classe
    )

    # Caminho do certificado digital A1 (.pfx).
    pfx_path: Path
    # SecretStr esconde o valor em print/log; use .get_secret_value() para lê-lo.
    pfx_senha: SecretStr
    # CNPJ a consultar. Se vazio, a API usa o CNPJ do próprio certificado.
    cnpj_consulta: str | None = None
    ambiente: Ambiente = Ambiente.HOMOLOGACAO
    # Pasta onde os XMLs baixados são salvos.
    pasta_saida: Path = Path("nfse_xml")
    # Pausa entre as consultas, para não sobrecarregar a API.
    pausa_segundos: float = 1.0

    @field_validator("cnpj_consulta", mode="before")
    @classmethod
    def limpar_cnpj(cls, valor):
        """Aceita o CNPJ com ou sem pontuação e guarda apenas os dígitos.

        Exemplo: "12.345.678/0001-99" vira "12345678000199".
        `mode="before"` faz esta função rodar antes da validação de tipo do pydantic.
        """
        if not valor:
            return None

        somente_digitos = "".join(caractere for caractere in str(valor) if caractere.isdigit())
        if len(somente_digitos) != QUANTIDADE_DIGITOS_CNPJ:
            raise ValueError("CNPJ deve ter 14 dígitos")
        return somente_digitos

    @property
    def url_base(self) -> str:
        """URL da API correspondente ao ambiente escolhido."""
        return URLS_BASE[self.ambiente]
