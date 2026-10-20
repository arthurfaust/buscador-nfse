"""Baixa os documentos fiscais do ADN, salva os XMLs e lembra onde parou.

Como funciona a API de distribuição:
    Cada documento recebe um número sequencial chamado NSU (Número Sequencial
    Único). Perguntamos à API "o que existe depois do NSU X?" e ela responde
    com um lote de documentos. Repetimos a pergunta usando o maior NSU recebido,
    até a API dizer que não há mais nada.

    O último NSU processado é salvo em arquivo (`EstadoNSU`). Assim, na próxima
    execução, continuamos de onde paramos em vez de baixar tudo de novo.
"""
import json
import time
from pathlib import Path

from .cliente import ClienteADN
from .decodificacao import campo, decodificar_xml


class EstadoNSU:
    """Guarda em um arquivo de texto o último NSU já processado."""

    def __init__(self, arquivo: Path):
        self.arquivo = Path(arquivo)

    def ler(self) -> int:
        """Retorna o NSU salvo, ou 0 se ainda não houver nada salvo."""
        if not self.arquivo.exists():
            return 0

        conteudo = self.arquivo.read_text().strip()
        return int(conteudo or 0)

    def gravar(self, nsu: int) -> None:
        """Salva o NSU, criando a pasta do arquivo se ela não existir."""
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo.write_text(str(nsu))


def sincronizar(
    cliente: ClienteADN,
    pasta_saida: Path,
    estado: EstadoNSU,
    cnpj_consulta: str | None = None,
    pausa: float = 1.0,
    nsu_inicial: int | None = None,
    log=print,
) -> int:
    """Baixa todos os documentos novos e retorna quantos XMLs foram gravados.

    Parâmetros:
        cliente: cliente HTTP já configurado com o certificado.
        pasta_saida: onde os XMLs serão salvos.
        estado: onde o último NSU é lido e gravado.
        cnpj_consulta: CNPJ a consultar (opcional).
        pausa: segundos de espera entre um lote e outro.
        nsu_inicial: se informado, ignora o NSU salvo e começa deste número.
        log: função usada para mostrar mensagens (nos testes, passamos uma
            função que não faz nada para não poluir a saída).
    """
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    nsu_atual = estado.ler() if nsu_inicial is None else nsu_inicial
    total_xmls_salvos = 0
    log(f"Iniciando em NSU {nsu_atual}")

    while True:
        lote = _buscar_lote(cliente, nsu_atual, cnpj_consulta)
        if not lote:
            log("Nenhum documento novo.")
            break

        maior_nsu_do_lote = nsu_atual
        for documento in lote:
            nsu_do_documento = int(campo(documento, "NSU", padrao=0))
            if _salvar_documento(documento, nsu_do_documento, pasta_saida, log):
                total_xmls_salvos += 1
            maior_nsu_do_lote = max(maior_nsu_do_lote, nsu_do_documento)

        # Proteção contra loop infinito: se a API devolver um lote sem NSU maior
        # que o atual, perguntaríamos a mesma coisa para sempre.
        if maior_nsu_do_lote <= nsu_atual:
            break

        # Salva o progresso a cada lote. Se o programa cair no meio do caminho,
        # a próxima execução continua daqui.
        nsu_atual = maior_nsu_do_lote
        estado.gravar(nsu_atual)

        if pausa:
            time.sleep(pausa)

    log(f"Concluído: {total_xmls_salvos} XML(s). Último NSU: {nsu_atual}")
    return total_xmls_salvos


def _buscar_lote(cliente: ClienteADN, nsu: int, cnpj_consulta: str | None) -> list[dict]:
    """Consulta a API e retorna a lista de documentos (vazia se não houver nada)."""
    resposta = cliente.consultar_dfe(nsu, cnpj_consulta)
    if not resposta:
        return []

    # O `or []` cobre o caso em que a API manda o campo com valor null.
    return campo(resposta, "LoteDFe", padrao=[]) or []


def _salvar_documento(documento: dict, nsu: int, pasta_saida: Path, log) -> bool:
    """Grava um documento do lote em disco.

    - Se o documento tiver XML, salva como `{tipo}_{chave}_{nsu}.xml`.
    - Se não tiver, salva o JSON original como `raw_nsu_{nsu}.json` para
      análise posterior (assim nenhum dado recebido é perdido).

    Retorna True quando um XML foi salvo.
    """
    chave_acesso = campo(documento, "ChaveAcesso", padrao=f"nsu_{nsu}")
    tipo_documento = campo(documento, "TipoDocumento", padrao="DFE")
    xml_em_base64 = campo(documento, "ArquivoXml")

    if not xml_em_base64:
        arquivo_json = pasta_saida / f"raw_nsu_{nsu}.json"
        conteudo_json = json.dumps(documento, ensure_ascii=False, indent=2)
        arquivo_json.write_text(conteudo_json, encoding="utf-8")
        return False

    arquivo_xml = pasta_saida / f"{tipo_documento}_{chave_acesso}_{nsu}.xml"
    arquivo_xml.write_bytes(decodificar_xml(xml_em_base64))
    log(f"  NSU {nsu}: {tipo_documento} {chave_acesso}")
    return True
