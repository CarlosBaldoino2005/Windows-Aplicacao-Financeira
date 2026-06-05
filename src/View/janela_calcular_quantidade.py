"""Tela para calcular quantas acoes comprar com um valor em dinheiro."""
from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from src.Tool.calcular_quantidade_helper import calcular_quantidade_por_valor
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.Tool.validadores import validar_valor_monetario_ptbr
from src.View.formatadores import formatar_moeda
from src.View.tema import CORES

_LARGURA_JANELA = 520
_ALTURA_JANELA = 420


def _centralizar_sobre_pai(janela: ctk.CTkToplevel, pai: ctk.CTk, largura: int, altura: int) -> None:
    """Posiciona a janela auxiliar no centro da tela pai."""
    try:
        janela.update_idletasks()
        pai.update_idletasks()
        x = int(pai.winfo_rootx() + max(0, (pai.winfo_width() - largura) / 2))
        y = int(pai.winfo_rooty() + max(0, (pai.winfo_height() - altura) / 2))
        janela.geometry(f"{largura}x{altura}+{x}+{y}")
    except Exception:
        pass


class JanelaCalcularQuantidade(ctk.CTkToplevel):
    """Informa o valor disponivel e calcula a quantidade de acoes pelo preco atual."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: Any,
        simbolo: str,
        ao_aplicar_quantidade: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._ao_aplicar_quantidade = ao_aplicar_quantidade
        self._preco_atual: float | None = None
        self._moeda = "BRL" if simbolo.endswith(".SA") else "USD"
        self._quantidade_calculada: int | None = None

        codigo = simbolo.replace(".SA", "").replace("-USD", "")
        self.title(f"Calcular quantidade — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)

        self._montar_interface()
        _centralizar_sobre_pai(self, pai, _LARGURA_JANELA, _ALTURA_JANELA)
        self.transient(pai)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(100, self._carregar_preco_atual)

    def _ao_fechar(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _montar_interface(self) -> None:
        painel = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        codigo = self._simbolo.replace(".SA", "").replace("-USD", "")
        ctk.CTkLabel(
            painel,
            text=f"Quantas acoes de {codigo} da para comprar?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
            wraplength=460,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(16, 6))

        ctk.CTkLabel(
            painel,
            text=(
                "Informe quanto voce tem para investir. O calculo usa o preco atual "
                "da acao e considera apenas quantidade inteira (sem fracao)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=460,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self._label_preco = ctk.CTkLabel(
            painel,
            text="Buscando preco atual...",
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
        )
        self._label_preco.pack(anchor="w", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            painel,
            text="Valor disponivel",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(0, 4))

        prefixo_moeda = "R$" if self._moeda == "BRL" else "US$"
        self._entrada_valor = ctk.CTkEntry(
            painel,
            width=280,
            placeholder_text=f"{prefixo_moeda} 10.000,00",
        )
        self._entrada_valor.pack(anchor="w", padx=16, pady=(0, 12))
        aplicar_mascara_moeda_ptbr(self._entrada_valor, prefixo=prefixo_moeda)
        self._entrada_valor.bind("<Return>", lambda _e: self._calcular())

        ctk.CTkButton(
            painel,
            text="Calcular quantidade",
            command=self._calcular,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=180,
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self._label_resultado = ctk.CTkLabel(
            painel,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
            wraplength=460,
            justify="left",
        )
        self._label_resultado.pack(anchor="w", padx=16, pady=(0, 8))

        self._label_status = ctk.CTkLabel(
            painel,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=460,
            justify="left",
        )
        self._label_status.pack(anchor="w", padx=16, pady=(0, 12))

        rodape = ctk.CTkFrame(painel, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(8, 16))

        self._botao_usar = ctk.CTkButton(
            rodape,
            text="Usar no grafico",
            command=self._usar_no_grafico,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=140,
            state="disabled",
        )
        self._botao_usar.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="right")

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        def trabalho():
            try:
                resultado = funcao()
                self.after(0, lambda: ao_concluir(resultado, None))
            except Exception as exc:
                self.after(0, lambda: ao_concluir(None, str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _carregar_preco_atual(self) -> None:
        self._label_preco.configure(text="Buscando preco atual...")
        self._label_status.configure(text="")

        def buscar():
            return self._controlador.obter_cotacao(self._simbolo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_preco.configure(text="Preco atual: indisponivel", text_color=CORES["erro"])
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                return

            cotacao, msg_erro = resultado
            if msg_erro or cotacao is None:
                self._label_preco.configure(text="Preco atual: indisponivel", text_color=CORES["erro"])
                self._label_status.configure(
                    text=msg_erro or "Nao foi possivel obter a cotacao.",
                    text_color=CORES["erro"],
                )
                return

            self._preco_atual = float(cotacao.preco)
            self._moeda = str(getattr(cotacao, "moeda", None) or self._moeda)
            self._label_preco.configure(
                text=f"Preco atual: {formatar_moeda(self._preco_atual, self._moeda)}",
                text_color=CORES["texto"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _calcular(self) -> None:
        self._quantidade_calculada = None
        self._botao_usar.configure(state="disabled")

        if self._preco_atual is None or self._preco_atual <= 0:
            self._label_resultado.configure(text="", text_color=CORES["texto"])
            self._label_status.configure(
                text="Aguarde o preco atual ou tente novamente em instantes.",
                text_color=CORES["erro"],
            )
            return

        valor, erro_valor = validar_valor_monetario_ptbr(self._entrada_valor.get())
        if erro_valor:
            self._label_resultado.configure(text="", text_color=CORES["texto"])
            self._label_status.configure(text=erro_valor, text_color=CORES["erro"])
            return

        resultado = calcular_quantidade_por_valor(valor, self._preco_atual)
        self._quantidade_calculada = resultado.quantidade

        if resultado.quantidade <= 0:
            self._label_resultado.configure(
                text=(
                    f"Com {formatar_moeda(valor, self._moeda)} nao e possivel comprar "
                    f"nenhuma acao inteira ao preco de "
                    f"{formatar_moeda(self._preco_atual, self._moeda)}."
                ),
                text_color=CORES["aviso"],
            )
            self._label_status.configure(
                text="Informe um valor maior ou aguarde uma cotacao menor.",
                text_color=CORES["textoSecundario"],
            )
            return

        texto_resultado = (
            f"Com {formatar_moeda(valor, self._moeda)} voce compra "
            f"{resultado.quantidade:,} acoes".replace(",", ".")
            + f" a {formatar_moeda(self._preco_atual, self._moeda)} cada.\n"
            f"Total investido: {formatar_moeda(resultado.valor_investido, self._moeda)}."
        )
        if resultado.valor_sobra > 0.009:
            texto_resultado += f"\nSobra: {formatar_moeda(resultado.valor_sobra, self._moeda)}."

        self._label_resultado.configure(text=texto_resultado, text_color=CORES["sucesso"])
        self._label_status.configure(
            text="Clique em Usar no grafico para preencher a quantidade na tela do grafico.",
            text_color=CORES["textoSecundario"],
        )
        self._botao_usar.configure(state="normal")

    def _usar_no_grafico(self) -> None:
        if self._quantidade_calculada is None or self._quantidade_calculada <= 0:
            return
        if self._ao_aplicar_quantidade is not None:
            self._ao_aplicar_quantidade(self._quantidade_calculada)
        self._ao_fechar()
