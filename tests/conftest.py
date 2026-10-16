import base64
import gzip

def xml_compactado(xml: str) -> str:
    """Simula o formato da API: gzip + base64."""
    return base64.b64encode(gzip.compress(xml.encode())).decode()