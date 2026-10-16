"""Percorre os NSUs, salva os XMLs e guarda o último NSU processado."""
import json
import time
from pathlib import Path

from .cliente import ClienteADN
from .decodificacao import campo, decodificar_xml

class EstadoNSU:
    def __init__(self, arquivo: Path):
        self.arquivo = Path(arquivo)

    def ler(self) -> int:
        if self.arquivo.exists():
            return int(self.arquivo.read_text().strip() or 0)
        return 0

    def gravar(self, nsu: int) -> None:
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo.write_text(str(nsu))

def sincronizar(cliente: ClienteADN, pasta_saida: Path, estado: EstadoNSU,
                cnpj_consulta: str | None = None, pausa: float = 1.0,
                nsu_inicial: int | None = None, log=print) -> int:
    """Baixa tudo a partir do NSU salvo. Retorna a quantidade de XMLs gravados."""
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    nsu = estado.ler() if nsu_inicial is None else nsu_inicial
    total = 0
    log(f"Iniciando em NSU {nsu}")

    while True:
        dados = cliente.consultar_dfe(nsu, cnpj_consulta)
        lote = (campo(dados, "LoteDFe", padrao=[]) or []) if dados else []
        if not lote:
            log("Nenhum documento novo.")
            break

        maior = nsu
        for doc in lote:
            doc_nsu = int(campo(doc, "NSU", padrao=0))
            chave = campo(doc, "ChaveAcesso", padrao=f"nsu_{doc_nsu}")
            tipo = campo(doc, "TipoDocumento", padrao="DFE")
            xml_b64 = campo(doc, "ArquivoXml")
            if xml_b64:
                (pasta_saida / f"{tipo}_{chave}_{doc_nsu}.xml").write_bytes(
                    decodificar_xml(xml_b64))
                total += 1
                log(f"  NSU {doc_nsu}: {tipo} {chave}")
            else:
                (pasta_saida / f"raw_nsu_{doc_nsu}.json").write_text(
                    json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            maior = max(maior, doc_nsu)

        if maior <= nsu:
            break  # proteção contra loop infinito
        nsu = maior
        estado.gravar(nsu)
        if pausa:
            time.sleep(pausa)

    log(f"Concluído: {total} XML(s). Último NSU: {nsu}")
    return total