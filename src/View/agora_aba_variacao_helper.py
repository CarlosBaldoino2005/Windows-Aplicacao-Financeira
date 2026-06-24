"""Aba dinamica de variacao entre dois pontos nas telas Agora."""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

import customtkinter as ctk

from src.Tool.calcular_quantidade_helper import calcular_quantidade_por_valor
from src.Tool.mascara_moeda_helper import aplicar_mascara_inteiro_ptbr, aplicar_mascara_moeda_ptbr
from src.Tool.validadores import validar_quantidade_cotas, validar_valor_monetario_ptbr
from src.View.formatadores import formatar_moeda
from src.View.painel_comparacao_periodo import PainelComparacaoPeriodo, calcular_comparacao_acao_unica
from src.View.tema import CORES

ABA_VARIACAO_AGORA = "Variacao"
_MODO_QUANTIDADE = "Quantidade de acoes"
_MODO_VALOR = "Valor total do investimento"


class GerenciadorAbaVariacaoAgora:
    """Cria e remove a aba Variacao conforme o usuario seleciona dois pontos no grafico."""

    def __init__(self, tabview: ctk.CTkTabview, aba_grafico: str) -> None:
        self._tabview = tabview
        self._aba_grafico = aba_grafico
        self._ativa = False
        self._frame_barra_simulacao: ctk.CTkFrame | None = None
        self._frame_painel: ctk.CTkScrollableFrame | None = None
        self._combo_modo: ctk.CTkComboBox | None = None
        self._frame_campo_modo: ctk.CTkFrame | None = None
        self._entrada_quantidade: ctk.CTkEntry | None = None
        self._entrada_valor: ctk.CTkEntry | None = None
        self._label_info_simulacao: ctk.CTkLabel | None = None
        self._pontos: list[dict] | None = None
        self._simbolo = ""
        self._moeda = "BRL"
        self._payload_base: dict | None = None
        self._quantidade_resolvida = 1
        self._preferencias_simulacao: dict = {"modo": _MODO_QUANTIDADE, "quantidade": "1", "valor": ""}

    @property
    def ativa(self) -> bool:
        return self._ativa

    def obter_quantidade_para_grafico(self) -> int:
        """Quantidade usada ao concluir a selecao de dois pontos no grafico."""
        return max(1, self._quantidade_resolvida)

    def obter_intervalo_para_restaurar(self) -> tuple[str, str] | None:
        if not self._payload_base:
            return None
        inicio = self._payload_base.get("data_inicio")
        fim = self._payload_base.get("data_fim")
        if not inicio or not fim:
            return None
        return str(inicio), str(fim)

    def atualizar(
        self,
        payload: dict,
        *,
        pontos: list[dict] | None = None,
        simbolo: str = "",
        moeda: str = "BRL",
        ao_mensagem_parcial: Callable[[str], None] | None = None,
    ) -> None:
        tipo = payload.get("tipo", "instrucao")

        if tipo == "reiniciar_selecao":
            if ao_mensagem_parcial is not None:
                ao_mensagem_parcial(
                    "Selecione o novo ponto inicial no grafico (quantidade e valor mantidos)."
                )
            return

        if tipo == "completo":
            self._pontos = list(pontos) if pontos else self._pontos
            self._simbolo = simbolo or self._simbolo
            self._moeda = moeda or self._moeda
            primeira_vez = not self._ativa
            if self._ativa:
                self._salvar_preferencias_simulacao()
            self._payload_base = deepcopy(payload)
            self._garantir_aba()
            if primeira_vez:
                self._quantidade_resolvida = 1
                self._aplicar_modo_entrada()
            else:
                self._restaurar_preferencias_simulacao()
            self._recalcular_variacao()
            self._tabview.set(ABA_VARIACAO_AGORA)
            if ao_mensagem_parcial is not None:
                ao_mensagem_parcial("")
            return

        if tipo == "parcial":
            if ao_mensagem_parcial is not None:
                ao_mensagem_parcial(
                    "1º ponto selecionado. Clique no 2º ponto no grafico para atualizar a aba Variacao."
                )
            return

        if tipo == "instrucao" and not self._ativa:
            if ao_mensagem_parcial is not None:
                ao_mensagem_parcial("")
            return

        if tipo == "instrucao":
            return

        self._limpar_contexto()
        self._ocultar_aba()
        if ao_mensagem_parcial is not None:
            ao_mensagem_parcial("")

    def _limpar_contexto(self) -> None:
        self._pontos = None
        self._payload_base = None
        self._quantidade_resolvida = 1
        self._preferencias_simulacao = {"modo": _MODO_QUANTIDADE, "quantidade": "1", "valor": ""}

    def _salvar_preferencias_simulacao(self) -> None:
        if self._combo_modo is None:
            return
        self._preferencias_simulacao = {
            "modo": self._combo_modo.get(),
            "quantidade": self._entrada_quantidade.get() if self._entrada_quantidade is not None else "1",
            "valor": self._entrada_valor.get() if self._entrada_valor is not None else "",
        }

    def _restaurar_preferencias_simulacao(self) -> None:
        if self._combo_modo is None:
            return
        pref = self._preferencias_simulacao
        self._combo_modo.set(pref.get("modo", _MODO_QUANTIDADE))
        self._aplicar_modo_entrada(
            quantidade_inicial=pref.get("quantidade", "1"),
            valor_inicial=pref.get("valor", ""),
        )

    def _garantir_aba(self) -> None:
        if self._ativa:
            return

        self._tabview.add(ABA_VARIACAO_AGORA)
        aba = self._tabview.tab(ABA_VARIACAO_AGORA)
        aba.grid_columnconfigure(0, weight=1)
        aba.grid_rowconfigure(1, weight=1)

        self._frame_barra_simulacao = ctk.CTkFrame(aba, fg_color=CORES["superficie"], corner_radius=10)
        self._frame_barra_simulacao.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 6))
        self._montar_barra_simulacao(self._frame_barra_simulacao)

        self._frame_painel = ctk.CTkScrollableFrame(
            aba,
            fg_color=CORES["fundo"],
            label_text="Resumo da variacao no intervalo",
        )
        self._frame_painel.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._ativa = True

    def _montar_barra_simulacao(self, pai: ctk.CTkFrame) -> None:
        conteudo = ctk.CTkFrame(pai, fg_color="transparent")
        conteudo.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            conteudo,
            text="Simular com",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left", padx=(0, 8))

        self._combo_modo = ctk.CTkComboBox(
            conteudo,
            values=[_MODO_QUANTIDADE, _MODO_VALOR],
            width=240,
            command=self._ao_mudar_modo_simulacao,
        )
        self._combo_modo.set(_MODO_QUANTIDADE)
        self._combo_modo.pack(side="left", padx=(0, 12))

        self._frame_campo_modo = ctk.CTkFrame(conteudo, fg_color="transparent")
        self._frame_campo_modo.pack(side="left")

        self._label_info_simulacao = ctk.CTkLabel(
            pai,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
            wraplength=1000,
            justify="left",
        )
        self._label_info_simulacao.pack(fill="x", padx=12, pady=(0, 8))

        self._aplicar_modo_entrada()

    def _prefixo_moeda(self) -> str:
        return "R$" if self._moeda == "BRL" else "US$"

    def _ao_mudar_modo_simulacao(self, _valor: str | None = None) -> None:
        self._salvar_preferencias_simulacao()
        if self._combo_modo is not None:
            self._preferencias_simulacao["modo"] = self._combo_modo.get()
        pref = self._preferencias_simulacao
        self._aplicar_modo_entrada(
            quantidade_inicial=pref.get("quantidade", "1"),
            valor_inicial=pref.get("valor", ""),
        )
        if self._label_info_simulacao is not None:
            modo = self._combo_modo.get() if self._combo_modo is not None else _MODO_QUANTIDADE
            if modo == _MODO_VALOR:
                texto = "Informe o valor total e clique em Recalcular para ver quantas acoes da para comprar."
            else:
                texto = "Informe a quantidade de acoes (padrao: 1) e clique em Recalcular."
            self._label_info_simulacao.configure(text=texto, text_color=CORES["textoSecundario"])

    def _aplicar_modo_entrada(
        self,
        *,
        quantidade_inicial: str = "1",
        valor_inicial: str = "",
    ) -> None:
        if self._frame_campo_modo is None or self._combo_modo is None:
            return

        for widget in self._frame_campo_modo.winfo_children():
            widget.destroy()

        modo = self._combo_modo.get()
        if modo == _MODO_VALOR:
            ctk.CTkLabel(
                self._frame_campo_modo,
                text="Valor disponivel",
                font=ctk.CTkFont(size=12),
                text_color=CORES["textoSecundario"],
            ).pack(side="left", padx=(0, 6))
            self._entrada_quantidade = None
            self._entrada_valor = ctk.CTkEntry(
                self._frame_campo_modo,
                width=160,
                placeholder_text=f"{self._prefixo_moeda()} 1.000,00",
            )
            if valor_inicial:
                self._entrada_valor.insert(0, valor_inicial)
            self._entrada_valor.pack(side="left")
            aplicar_mascara_moeda_ptbr(self._entrada_valor, prefixo=self._prefixo_moeda())
            self._entrada_valor.bind("<Return>", lambda _e: self._recalcular_variacao())
            self._montar_botao_recalcular()
            return

        ctk.CTkLabel(
            self._frame_campo_modo,
            text="Quantidade",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(side="left", padx=(0, 6))
        self._entrada_valor = None
        self._entrada_quantidade = ctk.CTkEntry(self._frame_campo_modo, width=100, justify="center")
        self._entrada_quantidade.insert(0, quantidade_inicial or "1")
        self._entrada_quantidade.pack(side="left")
        aplicar_mascara_inteiro_ptbr(self._entrada_quantidade)
        self._entrada_quantidade.bind("<Return>", lambda _e: self._recalcular_variacao())
        self._montar_botao_recalcular()

    def _montar_botao_recalcular(self) -> None:
        if self._frame_campo_modo is None:
            return
        ctk.CTkButton(
            self._frame_campo_modo,
            text="Recalcular",
            width=110,
            command=self._recalcular_variacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="left", padx=(8, 0))

    def _resolver_quantidade(self) -> tuple[int | None, str | None, dict | None]:
        if self._payload_base is None or not self._pontos:
            return None, "Selecione dois pontos no grafico.", None

        indice_inicio = int(self._payload_base.get("indice_inicio", 0))
        indice_fim = int(self._payload_base.get("indice_fim", 0))
        preco_inicio = float(self._pontos[indice_inicio]["fechamento"])

        extras: dict = {}
        modo = self._combo_modo.get() if self._combo_modo is not None else _MODO_QUANTIDADE

        if modo == _MODO_VALOR:
            if self._entrada_valor is None:
                return None, "Informe o valor total do investimento.", None
            valor, erro = validar_valor_monetario_ptbr(self._entrada_valor.get())
            if erro or valor is None or valor <= 0:
                return None, erro or "Informe um valor valido para investir.", None

            resultado = calcular_quantidade_por_valor(valor, preco_inicio)
            if resultado.quantidade < 1:
                return (
                    None,
                    (
                        f"Valor insuficiente para comprar 1 acao ao preco de "
                        f"{formatar_moeda(preco_inicio, self._moeda)}."
                    ),
                    None,
                )

            extras = {
                "modo_simulacao": "valor",
                "valor_investimento_informado": valor,
                "valor_sobra_compra": resultado.valor_sobra,
            }
            return resultado.quantidade, None, extras

        if self._entrada_quantidade is None:
            return 1, None, None
        quantidade, erro = validar_quantidade_cotas(self._entrada_quantidade.get(), padrao=1)
        if erro or quantidade is None:
            return None, erro or "Quantidade invalida.", None
        return quantidade, None, None

    def _recalcular_variacao(self) -> None:
        if self._frame_painel is None or self._payload_base is None or not self._pontos:
            return

        quantidade, erro, extras = self._resolver_quantidade()
        if erro or quantidade is None:
            if self._label_info_simulacao is not None:
                self._label_info_simulacao.configure(
                    text=erro or "Nao foi possivel recalcular.",
                    text_color=CORES["erro"],
                )
            return

        self._quantidade_resolvida = quantidade
        indice_inicio = int(self._payload_base["indice_inicio"])
        indice_fim = int(self._payload_base["indice_fim"])

        payload = calcular_comparacao_acao_unica(
            self._pontos,
            self._simbolo,
            self._moeda,
            indice_inicio,
            indice_fim,
            quantidade,
            intraday=True,
        )

        if extras and payload.get("acoes"):
            acao = dict(payload["acoes"][0])
            acao.update(extras)
            payload = {**payload, "acoes": [acao]}

        PainelComparacaoPeriodo.exibir(self._frame_painel, payload)
        self._salvar_preferencias_simulacao()

        if self._label_info_simulacao is not None:
            modo = self._combo_modo.get() if self._combo_modo is not None else _MODO_QUANTIDADE
            if modo == _MODO_VALOR and extras:
                preco = float(self._pontos[indice_inicio]["fechamento"])
                texto = (
                    f"Com {formatar_moeda(float(extras['valor_investimento_informado']), self._moeda)} "
                    f"ao preco de {formatar_moeda(preco, self._moeda)}, "
                    f"da para comprar {quantidade:,} acao(oes).".replace(",", ".")
                )
                if float(extras.get("valor_sobra_compra") or 0) > 0:
                    texto += (
                        f" Sobra: {formatar_moeda(float(extras['valor_sobra_compra']), self._moeda)}."
                    )
            else:
                texto = f"Simulacao com {quantidade:,} acao(oes).".replace(",", ".")
            self._label_info_simulacao.configure(text=texto, text_color=CORES["textoSecundario"])

    def _ocultar_aba(self) -> None:
        if not self._ativa:
            return

        try:
            if self._tabview.get() == ABA_VARIACAO_AGORA:
                self._tabview.set(self._aba_grafico)
        except Exception:
            pass

        try:
            self._tabview.delete(ABA_VARIACAO_AGORA)
        except Exception:
            pass

        self._ativa = False
        self._frame_barra_simulacao = None
        self._frame_painel = None
        self._combo_modo = None
        self._frame_campo_modo = None
        self._entrada_quantidade = None
        self._entrada_valor = None
        self._label_info_simulacao = None
