"""Traducao de titulos e resumos de noticias para portugues."""
from __future__ import annotations

from deep_translator import GoogleTranslator

from src.Model.noticia_mercado import NoticiaMercado
from src.Tool.registrador_log import RegistradorLog

_LIMITE_CARACTERES = 4500


class TraducaoNoticiasServico:
    """Traduz textos com cache em memoria (Google Translate via deep-translator)."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._cache: dict[str, tuple[str, str]] = {}

    def traduzir_lote(
        self, noticias: list[NoticiaMercado]
    ) -> tuple[dict[str, tuple[str, str]], str | None]:
        """Retorna mapa id -> (titulo_pt, resumo_pt) para cada noticia."""
        if not noticias:
            return {}, None

        resultado: dict[str, tuple[str, str]] = {}

        for noticia in noticias:
            if noticia.id in self._cache:
                resultado[noticia.id] = self._cache[noticia.id]
                continue
            titulo_pt = self._traduzir_fragmento(noticia.titulo)
            resumo_pt = self._traduzir_fragmento(noticia.resumo) if noticia.resumo else ""
            par = (titulo_pt, resumo_pt)
            self._cache[noticia.id] = par
            resultado[noticia.id] = par

        if not resultado:
            return {}, "Nao foi possivel traduzir. Verifique a internet e tente novamente."

        return resultado, None

    def _traduzir_fragmento(self, texto: str) -> str:
        fragmento = (texto or "").strip()
        if not fragmento:
            return fragmento
        if len(fragmento) > _LIMITE_CARACTERES:
            fragmento = fragmento[:_LIMITE_CARACTERES]

        try:
            traduzido = GoogleTranslator(source="auto", target="pt").translate(fragmento)
            return (traduzido or fragmento).strip()
        except Exception as exc:
            self._log.aviso(f"Falha ao traduzir noticia: {exc}")
            return fragmento
