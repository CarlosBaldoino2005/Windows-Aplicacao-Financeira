"""Download e cache de miniaturas de noticias para a interface."""
from __future__ import annotations

import io
from urllib.request import Request, urlopen

import customtkinter as ctk
from PIL import Image

from src.Tool.registrador_log import RegistradorLog

_TIMEOUT_SEGUNDOS = 8
_USER_AGENT = "Financeiro-Desktop/1.0"

# Cache em memoria: chave url+largura+altura -> CTkImage (manter referencia viva).
_cache_imagens: dict[str, ctk.CTkImage] = {}
_log = RegistradorLog()


def limpar_cache_imagens_noticias() -> None:
    """Libera cache ao trocar tamanho das fotos na mesma sessao."""
    _cache_imagens.clear()


def precarregar_imagens_noticias(
    urls: list[str],
    largura: int,
    altura: int,
) -> None:
    """Carrega imagens em segundo plano antes de montar a lista."""
    for url in urls:
        if url:
            obter_imagem_noticia(url, largura, altura)


def obter_imagem_noticia(
    url: str,
    largura: int,
    altura: int,
) -> ctk.CTkImage | None:
    """Retorna CTkImage redimensionada ou None se falhar."""
    if not url or largura <= 0 or altura <= 0:
        return None

    chave = f"{url}|{largura}|{altura}"
    if chave in _cache_imagens:
        return _cache_imagens[chave]

    try:
        requisicao = Request(url, headers={"User-Agent": _USER_AGENT})
        with urlopen(requisicao, timeout=_TIMEOUT_SEGUNDOS) as resposta:
            dados = resposta.read()
        imagem = Image.open(io.BytesIO(dados))
        if imagem.mode not in ("RGB", "RGBA"):
            imagem = imagem.convert("RGB")
        imagem.thumbnail((largura, altura), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(
            light_image=imagem,
            dark_image=imagem,
            size=(imagem.width, imagem.height),
        )
        _cache_imagens[chave] = ctk_img
        return ctk_img
    except Exception as exc:
        _log.aviso(f"Miniatura de noticia indisponivel: {exc}")
        return None
