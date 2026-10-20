"""Cliente HTTP da API de Distribuição do ADN (Ambiente de Dados Nacional).

Esta classe só sabe *conversar* com a API: monta a URL, envia a requisição e
devolve o JSON. Ela não salva arquivos nem decide qual NSU consultar; isso é
responsabilidade do módulo `sincronizador`.
"""
import requests

# Código HTTP que a API usa para dizer "não há documentos para essa consulta".
HTTP_NAO_ENCONTRADO = 404


class ClienteADN:
    """Faz as consultas à API do ADN.

    Parâmetros:
        url_base: endereço da API (produção ou homologação), ex.:
            "https://adn.nfse.gov.br/contribuintes".
        cert: tupla `(caminho_cert_pem, caminho_chave_pem)` usada na autenticação.
            Veja `certificado.certificado_pem`.
        sessao: sessão do `requests`. Normalmente não é informada; existe para
            facilitar testes.
        timeout: tempo máximo, em segundos, esperando a resposta da API.
    """

    def __init__(
        self,
        url_base: str,
        cert: tuple[str, str] | None = None,
        sessao: requests.Session | None = None,
        timeout: float = 60,
    ):
        # Remove a "/" do final para não gerar URLs como ".../contribuintes//DFe/1".
        self.url_base = url_base.rstrip("/")
        self.timeout = timeout

        # Uma Session reaproveita a conexão entre requisições (mais rápido)
        # e guarda configurações comuns, como o certificado e os cabeçalhos.
        self.sessao = sessao or requests.Session()
        if cert:
            self.sessao.cert = cert
        self.sessao.headers["Accept"] = "application/json"

    def consultar_dfe(self, nsu: int, cnpj_consulta: str | None = None) -> dict | None:
        """Consulta os documentos fiscais a partir de um NSU (GET /DFe/{nsu}).

        Retorna o JSON da resposta ou `None` quando não há documentos (HTTP 404).
        """
        url = f"{self.url_base}/DFe/{nsu}"

        # O CNPJ só é enviado quando informado; sem ele, a API usa o CNPJ do certificado.
        parametros = {"cnpjConsulta": cnpj_consulta} if cnpj_consulta else None

        resposta = self.sessao.get(url, params=parametros, timeout=self.timeout)
        return self._tratar_resposta(resposta)

    def consultar_eventos(self, chave_acesso: str) -> dict | None:
        """Consulta os eventos de uma NFS-e (GET /NFSe/{chave}/Eventos).

        Eventos são, por exemplo, cancelamentos. Retorna `None` se não houver nenhum.
        """
        url = f"{self.url_base}/NFSe/{chave_acesso}/Eventos"
        resposta = self.sessao.get(url, timeout=self.timeout)
        return self._tratar_resposta(resposta)

    @staticmethod
    def _tratar_resposta(resposta: requests.Response) -> dict | None:
        """Converte a resposta HTTP em dicionário.

        - 404: não é erro, apenas significa "nada encontrado" → retorna `None`.
        - Outros erros (400, 500...): `raise_for_status` lança `requests.HTTPError`.
        - Sucesso: retorna o corpo da resposta convertido de JSON.
        """
        if resposta.status_code == HTTP_NAO_ENCONTRADO:
            return None
        resposta.raise_for_status()
        return resposta.json()
