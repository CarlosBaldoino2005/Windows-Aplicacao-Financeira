"""Coordena relatorios da carteira e IPOs recentes."""
from __future__ import annotations

from pathlib import Path

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.ipo_recente import LinhaIpoRecente, TipoAtivoIpo
from src.Service.ipo_recentes_servico import IpoRecentesServico


class ControladorRelatorios:
    """API usada pelo hub de relatorios."""

    def __init__(self) -> None:
        self._carteira = ControladorCarteira()
        self._ipos = IpoRecentesServico()

    def gerar_relatorio_pdf_carteira(self) -> tuple[Path | None, str | None, str | None]:
        return self._carteira.gerar_relatorio_pdf()

    def carregar_relatorio_automatico_carteira(self):
        return self._carteira.carregar_relatorio_automatico()

    def listar_ipos_ultimos_30_dias(
        self,
    ) -> tuple[dict[TipoAtivoIpo, list[LinhaIpoRecente]], str | None]:
        return self._ipos.listar_ultimos_30_dias()
