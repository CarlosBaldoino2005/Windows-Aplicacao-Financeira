"""Painel de destaque com cotacao atual em real e dolar."""
from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk

from src.Model.cotacao import CotacaoResumo
from src.Service.cambio_servico import CambioServico
from src.Tool.cotacao_dual_helper import (
    calcular_precos_brl_usd,
    codigo_exibicao,
    rotulo_tipo_ativo,
)
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.tema import CORES


def _formatar_taxa_cambio(taxa_usd_brl: float | None) -> str | None:
    """Texto compacto da taxa USD/BRL usada na conversao."""
    if not taxa_usd_brl or taxa_usd_brl <= 0:
        return None
    return f"US$ 1 = {formatar_moeda(taxa_usd_brl, 'BRL')}"


class PainelDestaqueCotacao(ctk.CTkFrame):
    """Destaque visual do valor atual do ativo em BRL e USD."""

    def __init__(self, pai: ctk.CTkFrame, modo_multiplo: bool = False) -> None:
        super().__init__(
            pai,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=2,
            border_color=CORES["primaria"],
        )
        self._modo_multiplo = modo_multiplo
        self._cotacao_atual: CotacaoResumo | None = None
        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="x", padx=14, pady=12)
        self.mostrar_carregando("Carregando cotacao atual...")

    def mostrar_carregando(self, texto: str = "Carregando cotacao atual...") -> None:
        self._limpar()
        ctk.CTkLabel(
            self._container,
            text=texto,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w")

    def mostrar_erro(self, texto: str) -> None:
        self._limpar()
        ctk.CTkLabel(
            self._container,
            text=texto,
            font=ctk.CTkFont(size=13),
            text_color=CORES["erro"],
            wraplength=860,
            justify="left",
        ).pack(anchor="w")

    @property
    def cotacao_atual(self) -> CotacaoResumo | None:
        """Ultima cotacao exibida no painel (usada ao abrir monitoramento do grafico)."""
        return self._cotacao_atual

    def mostrar_cotacao(
        self,
        cotacao: CotacaoResumo,
        taxa_usd_brl: float | None,
        aviso_cambio: str | None = None,
    ) -> None:
        self._cotacao_atual = cotacao
        self._limpar()
        codigo = codigo_exibicao(cotacao.simbolo)
        tipo = rotulo_tipo_ativo(cotacao.simbolo)
        preco_brl, preco_usd = calcular_precos_brl_usd(
            cotacao.preco,
            cotacao.moeda,
            taxa_usd_brl,
        )

        linha_topo = ctk.CTkFrame(self._container, fg_color="transparent")
        linha_topo.pack(fill="x")

        ctk.CTkLabel(
            linha_topo,
            text=f"Valor atual — {codigo}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["primaria"],
        ).pack(side="left")

        ctk.CTkLabel(
            linha_topo,
            text=f"  ({tipo})",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(side="left")

        if cotacao.nome and cotacao.nome != codigo:
            ctk.CTkLabel(
                linha_topo,
                text=f"  —  {cotacao.nome}",
                font=ctk.CTkFont(size=12),
                text_color=CORES["textoSecundario"],
            ).pack(side="left")

        self._adicionar_campo_taxa_cambio(linha_topo, taxa_usd_brl, lado="right")

        linha_valores = ctk.CTkFrame(self._container, fg_color="transparent")
        linha_valores.pack(fill="x", pady=(8, 4))

        texto_brl = formatar_moeda(preco_brl, "BRL") if preco_brl is not None else "R$ —"
        texto_usd = formatar_moeda(preco_usd, "USD") if preco_usd is not None else "US$ —"

        ctk.CTkLabel(
            linha_valores,
            text=texto_brl,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        ctk.CTkLabel(
            linha_valores,
            text="   |   ",
            font=ctk.CTkFont(size=22),
            text_color=CORES["textoSecundario"],
        ).pack(side="left")

        ctk.CTkLabel(
            linha_valores,
            text=texto_usd,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        cor_variacao = CORES["sucesso"] if cotacao.variacao_percentual >= 0 else CORES["erro"]
        ctk.CTkLabel(
            linha_valores,
            text=formatar_variacao(
                cotacao.variacao_valor,
                cotacao.variacao_percentual,
                cotacao.moeda,
            ),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=cor_variacao,
        ).pack(side="left", padx=(16, 0))

        linha_rodape = ctk.CTkFrame(self._container, fg_color="transparent")
        linha_rodape.pack(fill="x")

        ctk.CTkLabel(
            linha_rodape,
            text="Real (BRL)",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(side="left", padx=(2, 0))

        ctk.CTkLabel(
            linha_rodape,
            text="Dolar (USD)",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(side="left", padx=(118, 0))

        if aviso_cambio and (preco_brl is None or preco_usd is None):
            ctk.CTkLabel(
                self._container,
                text=aviso_cambio,
                font=ctk.CTkFont(size=11),
                text_color=CORES["aviso"],
                wraplength=860,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))

    def mostrar_varias(
        self,
        cotacoes: list[CotacaoResumo],
        taxa_usd_brl: float | None,
        aviso_cambio: str | None = None,
    ) -> None:
        self._limpar()
        if not cotacoes:
            self.mostrar_erro("Cotacoes indisponiveis.")
            return

        linha_titulo = ctk.CTkFrame(self._container, fg_color="transparent")
        linha_titulo.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            linha_titulo,
            text="Valor atual dos ativos",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["primaria"],
        ).pack(side="left")

        self._adicionar_campo_taxa_cambio(linha_titulo, taxa_usd_brl, lado="right")

        for cotacao in cotacoes:
            self._adicionar_linha_ativo(cotacao, taxa_usd_brl)

        if aviso_cambio and taxa_usd_brl is None:
            ctk.CTkLabel(
                self._container,
                text=aviso_cambio,
                font=ctk.CTkFont(size=11),
                text_color=CORES["aviso"],
                wraplength=860,
                justify="left",
            ).pack(anchor="w", pady=(6, 0))

    def _adicionar_linha_ativo(
        self,
        cotacao: CotacaoResumo,
        taxa_usd_brl: float | None,
    ) -> None:
        codigo = codigo_exibicao(cotacao.simbolo)
        tipo = rotulo_tipo_ativo(cotacao.simbolo)
        preco_brl, preco_usd = calcular_precos_brl_usd(
            cotacao.preco,
            cotacao.moeda,
            taxa_usd_brl,
        )

        linha = ctk.CTkFrame(self._container, fg_color=CORES["superficie"], corner_radius=8)
        linha.pack(fill="x", pady=4)

        bloco = ctk.CTkFrame(linha, fg_color="transparent")
        bloco.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            bloco,
            text=f"{codigo} ({tipo})",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["texto"],
            width=160,
            anchor="w",
        ).pack(side="left")

        texto_brl = formatar_moeda(preco_brl, "BRL") if preco_brl is not None else "R$ —"
        texto_usd = formatar_moeda(preco_usd, "USD") if preco_usd is not None else "US$ —"

        ctk.CTkLabel(
            bloco,
            text=f"{texto_brl}  |  {texto_usd}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        ).pack(side="left", padx=(8, 12))

        cor_variacao = CORES["sucesso"] if cotacao.variacao_percentual >= 0 else CORES["erro"]
        ctk.CTkLabel(
            bloco,
            text=formatar_variacao(
                cotacao.variacao_valor,
                cotacao.variacao_percentual,
                cotacao.moeda,
            ),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=cor_variacao,
            anchor="w",
        ).pack(side="left")

    def _adicionar_campo_taxa_cambio(
        self,
        pai: ctk.CTkFrame,
        taxa_usd_brl: float | None,
        lado: str = "right",
    ) -> None:
        texto_taxa = _formatar_taxa_cambio(taxa_usd_brl)
        if not texto_taxa:
            return

        campo = ctk.CTkFrame(
            pai,
            fg_color=CORES["superficie"],
            corner_radius=6,
            border_width=1,
            border_color=CORES["borda"],
        )
        campo.pack(side=lado, padx=(12, 0))

        ctk.CTkLabel(
            campo,
            text="Cambio",
            font=ctk.CTkFont(size=9),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=8, pady=(4, 0))

        ctk.CTkLabel(
            campo,
            text=texto_taxa,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=8, pady=(0, 4))

    def _limpar(self) -> None:
        for widget in self._container.winfo_children():
            widget.destroy()


def buscar_cotacao_com_cambio(
    controlador: Any,
    simbolo: str,
) -> tuple[CotacaoResumo | None, float | None, str | None]:
    """Busca cotacao do ativo e taxa USD/BRL para montar o destaque."""
    cotacao, erro_cotacao = controlador.obter_cotacao(simbolo)
    if erro_cotacao or cotacao is None:
        return None, None, erro_cotacao or "Cotacao indisponivel."

    taxa, aviso_cambio = CambioServico().obter_taxa_usd_brl()
    return cotacao, taxa, aviso_cambio


def buscar_cotacoes_com_cambio(
    controlador: Any,
    simbolos: list[str],
) -> tuple[list[CotacaoResumo], float | None, str | None]:
    """Busca cotacoes de varios ativos e a taxa USD/BRL."""
    cotacoes: list[CotacaoResumo] = []
    for simbolo in simbolos:
        cotacao, erro = controlador.obter_cotacao(simbolo)
        if cotacao is not None:
            cotacoes.append(cotacao)

    if not cotacoes:
        return [], None, "Cotacoes indisponiveis para os ativos selecionados."

    taxa, aviso_cambio = CambioServico().obter_taxa_usd_brl()
    return cotacoes, taxa, aviso_cambio


def iniciar_atualizacao_destaque(
    painel: PainelDestaqueCotacao,
    controlador: Any,
    simbolo: str,
    executar_em_thread: Callable,
) -> None:
    """Carrega cotacao em thread e atualiza o painel de destaque."""
    painel.mostrar_carregando()

    def buscar():
        return buscar_cotacao_com_cambio(controlador, simbolo)

    def ao_concluir(resultado, erro):
        if erro:
            painel.mostrar_erro(erro)
            return
        cotacao, taxa, aviso = resultado
        if cotacao is None:
            painel.mostrar_erro(aviso or "Cotacao indisponivel.")
            return
        painel.mostrar_cotacao(cotacao, taxa, aviso)

    executar_em_thread(buscar, ao_concluir)


def iniciar_atualizacao_destaque_multiplo(
    painel: PainelDestaqueCotacao,
    controlador: Any,
    simbolos: list[str],
    executar_em_thread: Callable,
) -> None:
    """Carrega cotacoes de varios ativos para o grafico comparativo."""
    painel.mostrar_carregando("Carregando cotacoes atuais...")

    def buscar():
        return buscar_cotacoes_com_cambio(controlador, simbolos)

    def ao_concluir(resultado, erro):
        if erro:
            painel.mostrar_erro(erro)
            return
        cotacoes, taxa, aviso = resultado
        if not cotacoes:
            painel.mostrar_erro(aviso or "Cotacoes indisponiveis.")
            return
        painel.mostrar_varias(cotacoes, taxa, aviso)

    executar_em_thread(buscar, ao_concluir)
