"""Cards de resumo da carteira: investido, valor atual, resultado e dividendos."""
from __future__ import annotations

import customtkinter as ctk

from src.Model.carteira import LinhaCarteira
from src.View.formatadores import formatar_moeda
from src.View.tema import CORES


class PainelResumoCarteira:
    """Quatro cards de metricas agregadas da carteira."""

    def __init__(self, pai: ctk.CTkBaseClass) -> None:
        self._pai = pai
        self._frame_resumo: ctk.CTkFrame | None = None
        self._label_resumo_vazio: ctk.CTkLabel | None = None
        self._frame_cards_resumo: ctk.CTkFrame | None = None
        self._card_resultado: ctk.CTkFrame | None = None
        self._valor_investido: ctk.CTkLabel | None = None
        self._valor_atual: ctk.CTkLabel | None = None
        self._valor_resultado: ctk.CTkLabel | None = None
        self._sub_resultado: ctk.CTkLabel | None = None
        self._valor_dividendos: ctk.CTkLabel | None = None
        self._label_rodape: ctk.CTkLabel | None = None

    def montar(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(
            self._pai,
            fg_color=CORES["fundo"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        self._frame_resumo = frame

        self._label_resumo_vazio = ctk.CTkLabel(
            frame,
            text="Carregando resumo...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            justify="left",
            anchor="w",
        )
        self._label_resumo_vazio.pack(anchor="w", padx=12, pady=10)

        self._frame_cards_resumo = ctk.CTkFrame(frame, fg_color="transparent")
        _, self._valor_investido, _ = self._criar_card_resumo(
            self._frame_cards_resumo, 0, "Investido"
        )
        _, self._valor_atual, _ = self._criar_card_resumo(
            self._frame_cards_resumo, 1, "Valor atual"
        )
        self._card_resultado, self._valor_resultado, self._sub_resultado = self._criar_card_resumo(
            self._frame_cards_resumo, 2, "Resultado", com_subtitulo=True
        )
        _, self._valor_dividendos, _ = self._criar_card_resumo(
            self._frame_cards_resumo, 3, "Dividendos"
        )

        self._label_rodape = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_rodape.pack(anchor="w", padx=12, pady=(0, 10))
        self._frame_cards_resumo.pack_forget()

        return frame

    def _criar_card_resumo(
        self,
        pai: ctk.CTkFrame,
        coluna: int,
        titulo: str,
        *,
        com_subtitulo: bool = False,
    ) -> tuple[ctk.CTkFrame, ctk.CTkLabel, ctk.CTkLabel | None]:
        card = ctk.CTkFrame(
            pai,
            fg_color=CORES["superficie"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        card.grid(row=0, column=coluna, padx=(0 if coluna == 0 else 6, 0), sticky="nsew")
        pai.grid_columnconfigure(coluna, weight=1)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=12, pady=(10, 0))

        valor = ctk.CTkLabel(
            card,
            text="—",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        )
        valor.pack(anchor="w", padx=12, pady=(2, 2 if com_subtitulo else 10))

        subtitulo = None
        if com_subtitulo:
            subtitulo = ctk.CTkLabel(
                card,
                text="",
                font=ctk.CTkFont(size=11),
                text_color=CORES["textoSecundario"],
            )
            subtitulo.pack(anchor="w", padx=12, pady=(0, 10))

        return card, valor, subtitulo

    @staticmethod
    def _formatar_variacao_pct(valor_pct: float) -> str:
        sinal = "+" if valor_pct >= 0 else ""
        return f"{sinal}{valor_pct:.2f}%"

    def _mostrar_vazio(self, mensagem: str) -> None:
        if self._frame_cards_resumo is not None:
            self._frame_cards_resumo.pack_forget()
        if self._label_rodape is not None:
            self._label_rodape.configure(text="")
        if self._label_resumo_vazio is not None:
            self._label_resumo_vazio.configure(text=mensagem)
            self._label_resumo_vazio.pack(anchor="w", padx=12, pady=10)

    def _mostrar_cards(self) -> None:
        if self._label_resumo_vazio is not None:
            self._label_resumo_vazio.pack_forget()
        if self._frame_cards_resumo is not None:
            self._frame_cards_resumo.pack(fill="x", padx=12, pady=(10, 6))

    def _aplicar_estilo_resultado(self, resultado: float) -> None:
        if self._card_resultado is None or self._valor_resultado is None:
            return
        if resultado > 0:
            fundo = CORES.get("sucessoFundo", CORES["superficie"])
            texto = CORES["sucesso"]
        elif resultado < 0:
            fundo = CORES.get("erroFundo", CORES["superficie"])
            texto = CORES["erro"]
        else:
            fundo = CORES["superficie"]
            texto = CORES["texto"]

        self._card_resultado.configure(fg_color=fundo)
        self._valor_resultado.configure(text_color=texto)
        if self._sub_resultado is not None:
            self._sub_resultado.configure(text_color=texto)

    def atualizar(self, linhas: list[LinhaCarteira], *, texto_rodape: str = "") -> None:
        if not linhas:
            self._mostrar_vazio("Nenhuma posicao cadastrada.")
            return

        investido = 0.0
        atual = 0.0
        dividendos = 0.0
        tem_atual = False
        moeda = "BRL"
        if linhas[0].cotacao is not None:
            moeda = linhas[0].cotacao.moeda

        for linha in linhas:
            investido += linha.posicao.valor_investido
            dividendos += linha.dividendos_recebidos
            if linha.valor_atual is not None:
                atual += linha.valor_atual
                tem_atual = True

        self._mostrar_cards()
        if self._valor_investido is not None:
            self._valor_investido.configure(text=formatar_moeda(investido, moeda))
        if self._valor_dividendos is not None:
            self._valor_dividendos.configure(text=formatar_moeda(dividendos, moeda))

        if tem_atual:
            resultado = atual - investido
            pct = (resultado / investido * 100) if investido > 0 else 0.0
            if self._valor_atual is not None:
                self._valor_atual.configure(text=formatar_moeda(atual, moeda))
            if self._valor_resultado is not None:
                self._valor_resultado.configure(text=formatar_moeda(resultado, moeda))
            if self._sub_resultado is not None:
                self._sub_resultado.configure(text=self._formatar_variacao_pct(pct))
            self._aplicar_estilo_resultado(resultado)
        else:
            if self._valor_atual is not None:
                self._valor_atual.configure(text="—")
            if self._valor_resultado is not None:
                self._valor_resultado.configure(text="—")
            if self._sub_resultado is not None:
                self._sub_resultado.configure(text="Cotacao indisponivel")
            if self._card_resultado is not None:
                self._card_resultado.configure(fg_color=CORES["superficie"])
            if self._valor_resultado is not None:
                self._valor_resultado.configure(text_color=CORES["textoSecundario"])
            if self._sub_resultado is not None:
                self._sub_resultado.configure(text_color=CORES["textoSecundario"])

        if self._label_rodape is not None:
            self._label_rodape.configure(text=texto_rodape)
