"""Ferramenta para baixar NFS-e da API de Distribuição do ADN."""
import argparse
from pathlib import Path

from .certificado import certificado_pem
from .cliente import ClienteADN
from .config import Configuracao
from .sincronizador import EstadoNSU, sincronizar

def main() -> None:
    ap = argparse.ArgumentParser(prog="buscador-nfse")
    ap.add_argument("--nsu-inicial", type=int, help="Ignora o NSU salvo")
    args = ap.parse_args()

    cfg = Configuracao()
    print(f"Ambiente: {cfg.ambiente.value} ({cfg.url_base})")
    pasta = Path("estado") / cfg.ambiente.value
    estado = EstadoNSU(pasta / f"nsu_{cfg.cnpj_consulta or 'certificado'}.txt")
    pasta_saida = cfg.pasta_saida / cfg.ambiente.value

    with certificado_pem(cfg.pfx_path, cfg.pfx_senha.get_secret_value()) as cert:
        cliente = ClienteADN(cfg.url_base, cert=cert)
        sincronizar(cliente, pasta_saida, estado, cfg.cnpj_consulta, cfg.pausa_segundos, args.nsu_inicial)