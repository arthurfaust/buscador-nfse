"""Ferramenta para baixar NFS-e da API de Distribuição do ADN.

Este arquivo contém o ponto de entrada da linha de comando (`buscador-nfse`).
O fluxo é:
    1. Ler a configuração (.env / variáveis de ambiente).
    2. Converter o certificado .pfx em PEM temporário.
    3. Baixar os documentos novos com o `sincronizar`.
"""
import argparse
from pathlib import Path

from .certificado import certificado_pem
from .cliente import ClienteADN
from .config import Configuracao
from .sincronizador import EstadoNSU, sincronizar

# Pasta onde fica salvo o último NSU processado de cada ambiente/CNPJ.
PASTA_ESTADO = Path("estado")


def main() -> None:
    argumentos = _ler_argumentos()
    config = Configuracao()
    print(f"Ambiente: {config.ambiente.value} ({config.url_base})")

    # Produção e homologação têm NSUs diferentes, então cada ambiente
    # precisa de seu próprio arquivo de estado e de sua própria pasta de XMLs.
    nome_ambiente = config.ambiente.value
    identificador = config.cnpj_consulta or "certificado"
    arquivo_estado = PASTA_ESTADO / nome_ambiente / f"nsu_{identificador}.txt"
    pasta_saida = config.pasta_saida / nome_ambiente

    senha = config.pfx_senha.get_secret_value()
    with certificado_pem(config.pfx_path, senha) as certificado:
        cliente = ClienteADN(config.url_base, cert=certificado)
        sincronizar(
            cliente=cliente,
            pasta_saida=pasta_saida,
            estado=EstadoNSU(arquivo_estado),
            cnpj_consulta=config.cnpj_consulta,
            pausa=config.pausa_segundos,
            nsu_inicial=argumentos.nsu_inicial,
        )


def _ler_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="buscador-nfse")
    parser.add_argument(
        "--nsu-inicial",
        type=int,
        help="Começa deste NSU, ignorando o último NSU salvo",
    )
    return parser.parse_args()
