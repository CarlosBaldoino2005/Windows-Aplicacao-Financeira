"""Engrenagem e modal de configuracao compartilhados entre telas hub."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Tool.atualizacao_automatica_helper import (
    notificar_mudanca_configuracao_atualizacao_automatica,
)
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.icone_engrenagem_helper import criar_botao_engrenagem
from src.View.janela_configuracao_painel import (
    EscopoQuantidadePainel,
    ResultadoConfiguracaoPainel,
    abrir_configuracao_painel,
)
from src.View.tema import CORES, aplicar_modo_aparencia


class ConfiguracaoHubPainel:
    """Abre configuracoes pelo icone de engrenagem e aplica mudancas no hub."""

    def __init__(
        self,
        janela: ctk.CTk | ctk.CTkToplevel,
        config: ConfigPainelIni,
        *,
        escopo_quantidade: EscopoQuantidadePainel = "acoes",
        incluir_quantidade: bool = True,
        ao_recarregar: Callable[[], None] | None = None,
        ao_mudar_fonte: Callable[[], None] | None = None,
        ao_remontar_layout: Callable[[], None] | None = None,
        ao_reagendar_auto: Callable[[], None] | None = None,
    ) -> None:
        self._janela = janela
        self._config = config
        self._escopo_quantidade = escopo_quantidade
        self._incluir_quantidade = incluir_quantidade
        self._ao_recarregar = ao_recarregar
        self._ao_mudar_fonte = ao_mudar_fonte
        self._ao_remontar_layout = ao_remontar_layout
        self._ao_reagendar_auto = ao_reagendar_auto
        self._janela_configuracao = None

    def montar_titulo_com_engrenagem(self, cabecalho: ctk.CTkFrame, titulo: str) -> None:
        linha_topo = ctk.CTkFrame(cabecalho, fg_color="transparent")
        linha_topo.pack(fill="x", padx=20, pady=(12, 0))

        ctk.CTkLabel(
            linha_topo,
            text=titulo,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        criar_botao_engrenagem(
            linha_topo,
            command=self.abrir_configuracao,
        ).pack(side="right")

    def abrir_configuracao(self) -> None:
        if self._janela_configuracao is not None:
            try:
                if self._janela_configuracao.winfo_exists():
                    self._janela_configuracao.focus_force()
                    self._janela_configuracao.lift()
                    return
            except Exception:
                pass

        def ao_aplicar(resultado: ResultadoConfiguracaoPainel) -> None:
            self.processar_configuracao(resultado)

        self._janela_configuracao = abrir_configuracao_painel(
            self._janela,
            self._config,
            ao_aplicar,
            escopo_quantidade=self._escopo_quantidade,
            incluir_quantidade=self._incluir_quantidade,
        )

    def processar_configuracao(self, resultado: ResultadoConfiguracaoPainel) -> None:
        if resultado.tema_alterado:
            aplicar_modo_aparencia(resultado.modo_aparencia)
            if self._ao_remontar_layout is not None:
                self._ao_remontar_layout()
            if resultado.atualizacao_alterada:
                notificar_mudanca_configuracao_atualizacao_automatica()
                if self._ao_reagendar_auto is not None:
                    self._ao_reagendar_auto()
            return

        if resultado.quantidade_alterada and self._ao_recarregar is not None:
            self._ao_recarregar()
        elif resultado.fonte_alterada and self._ao_mudar_fonte is not None:
            self._ao_mudar_fonte()

        if resultado.atualizacao_alterada:
            notificar_mudanca_configuracao_atualizacao_automatica()
            if self._ao_reagendar_auto is not None:
                self._ao_reagendar_auto()

    def limpar_referencia_modal(self) -> None:
        self._janela_configuracao = None
