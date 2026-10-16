"""Cliente HTTP da API de Distribuição do ADN."""
import requests

class ClienteADN:
    def __init__(self, url_base: str, cert: tuple[str, str] | None = None,
                 sessao: requests.Session | None = None, timeout: float = 60):
        self.url_base = url_base.rstrip("/")
        self.sessao = sessao or requests.Session()
        if cert:
            self.sessao.cert = cert
        self.sessao.headers["Accept"] = "application/json"
        self.timeout = timeout

    def consultar_dfe(self, nsu: int, cnpj_consulta: str | None = None) -> dict | None:
        """GET /DFe/{NSU}. Retorna None quando não há documentos (404)."""
        params = {"cnpjConsulta": cnpj_consulta} if cnpj_consulta else None
        resp = self.sessao.get(f"{self.url_base}/DFe/{nsu}", params=params,
                               timeout=self.timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def consultar_eventos(self, chave_acesso: str) -> dict | None:
        """GET /NFSe/{chave}/Eventos."""
        resp = self.sessao.get(f"{self.url_base}/NFSe/{chave_acesso}/Eventos",
                               timeout=self.timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()