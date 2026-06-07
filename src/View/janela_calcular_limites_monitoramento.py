"""Modal para calcular limites de monitoramento a partir do preco atual."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Tool.calcular_limites_monitoramento_helper import (
    calcular_limites_monitoramento,
    validar_percentual_margem,
)
from src.Tool.janela_helper import configurar_janela_filha_modal, liberar_modal_janela_filha
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.Tool.validadores import validar_valor_monetario_ptbr
from src.View import mensagem_helper as messagebox
from src.View.formatadores import formatar_moeda
from src.View.tema import CORES

_LARGURA = 480
_ALTURA = 420


class JanelaCalcularLimitesMonitoramento(ctk.CTkToplevel):
    """Calcula valor baixo/alto por margem fixa ou percentual sobre o preco atual."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        preco_atual: float,
        moeda: str,
        ao_aplicar: Callable[[float, float], None],
        *,
        titulo_ativo: str | None = None,
    ) -> None:
        super().__init__(pai)
        self._preco_atual = preco_atual
        self._moeda = moeda
        self._ao_aplicar = ao_aplicar
        self._modo_margem = "valor"

        titulo_janela = "Calcular limites"
        if titulo_ativo:
            titulo_janela = f"Calcular limites — {titulo_ativo}"
        self.title(titulo_janela)
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(_LARGURA, _ALTURA)

        self._montar_interface()
        self._centralizar_sobre_pai(pai)
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self._entrada_margem.focus_set()

    def _centralizar_sobre_pai(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            pai.update_idletasks()
            x = int(pai.winfo_rootx() + max(0, (pai.winfo_width() - _LARGURA) / 2))
            y = int(pai.winfo_rooty() + max(0, (pai.winfo_height() - _ALTURA) / 2))
            self.geometry(f"{_LARGURA}x{_ALTURA}+{x}+{y}")
        except Exception:
            pass

    def _ao_fechar(self) -> None:
        liberar_modal_janela_filha(self)
        self.destroy()

    def _montar_interface(self) -> None:
        painel = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            painel,
            text="Calcular limites",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            painel,
            text=(
                "Informe a margem abaixo e acima do preco atual. "
                "Ex.: R$ 0,10 ou 10% gera valor baixo e valor alto automaticamente."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=_LARGURA - 80,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        card = ctk.CTkFrame(
            painel,
            fg_color=CORES["fundo"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        card.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(
            card,
            text=f"Preco atual: {formatar_moeda(self._preco_atual, self._moeda)}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["primaria"],
        ).pack(anchor="w", padx=12, pady=10)

        bloco_tipo = ctk.CTkFrame(painel, fg_color="transparent")
        bloco_tipo.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(
            bloco_tipo,
            text="Tipo de margem",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        self._seletor_tipo = ctk.CTkSegmentedButton(
            bloco_tipo,
            values=["Valor (R$)", "Porcentagem (%)"],
            command=self._ao_mudar_tipo_margem,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_tipo.set("Valor (R$)")
        self._seletor_tipo.pack(anchor="w", pady=(6, 0))

        linha_margem = ctk.CTkFrame(painel, fg_color="transparent")
        linha_margem.pack(fill="x", padx=16, pady=(8, 8))
        self._label_margem = ctk.CTkLabel(
            linha_margem,
            text="Margem em reais",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        )
        self._label_margem.pack(side="left", padx=(0, 12))
        self._entrada_margem_valor = ctk.CTkEntry(
            linha_margem,
            width=140,
            placeholder_text="Ex.: 0,10",
        )
        self._entrada_margem_percentual = ctk.CTkEntry(
            linha_margem,
            width=140,
            placeholder_text="Ex.: 10",
        )
        self._entrada_margem_valor.pack(side="left")
        self._entrada_margem_valor.bind("<KeyRelease>", lambda _e: self._atualizar_previa())
        self._entrada_margem_percentual.bind("<KeyRelease>", lambda _e: self._atualizar_previa())
        aplicar_mascara_moeda_ptbr(self._entrada_margem_valor)
        self._entrada_margem = self._entrada_margem_valor

        self._label_previa = ctk.CTkLabel(
            painel,
            text="Informe a margem para ver a previa.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=_LARGURA - 80,
            justify="left",
        )
        self._label_previa.pack(anchor="w", padx=16, pady=(4, 8))

        barra = ctk.CTkFrame(painel, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=16, pady=(8, 16))

        ctk.CTkButton(
            barra,
            text="Cancelar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        ).pack(side="right")

        ctk.CTkButton(
            barra,
            text="Usar valores",
            command=self._aplicar_valores,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            barra,
            text="Calcular",
            command=self._atualizar_previa,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right", padx=(0, 8))

    def _ao_mudar_tipo_margem(self, valor: str) -> None:
        self._modo_margem = "percentual" if "Porcentagem" in valor else "valor"
        if self._modo_margem == "percentual":
            self._label_margem.configure(text="Margem em %")
            self._entrada_margem_valor.pack_forget()
            self._entrada_margem_percentual.pack(side="left")
            self._entrada_margem = self._entrada_margem_percentual
        else:
            self._label_margem.configure(text="Margem em reais")
            self._entrada_margem_percentual.pack_forget()
            self._entrada_margem_valor.pack(side="left")
            self._entrada_margem = self._entrada_margem_valor
        self._atualizar_previa()

    def _ler_margem(self) -> tuple[float | None, str | None]:
        texto = self._entrada_margem.get().strip()
        if self._modo_margem == "percentual":
            return validar_percentual_margem(texto)
        valor, erro = validar_valor_monetario_ptbr(texto)
        if erro:
            return None, erro
        if valor is None or valor <= 0:
            return None, "Informe a margem em reais."
        return valor, None

    def _calcular(self) -> tuple[float | None, float | None, str | None]:
        margem, erro_margem = self._ler_margem()
        if erro_margem:
            return None, None, erro_margem
        if margem is None:
            return None, None, "Informe a margem."

        if self._modo_margem == "percentual":
            return calcular_limites_monitoramento(
                self._preco_atual,
                margem_percentual=margem,
                moeda=self._moeda,
            )
        return calcular_limites_monitoramento(
            self._preco_atual,
            margem_valor=margem,
            moeda=self._moeda,
        )

    def _atualizar_previa(self) -> None:
        valor_baixo, valor_alto, erro = self._calcular()
        if erro:
            self._label_previa.configure(text=erro, text_color=CORES["erro"])
            return

        assert valor_baixo is not None and valor_alto is not None
        self._label_previa.configure(
            text=(
                f"Valor baixo: {formatar_moeda(valor_baixo, self._moeda)}  |  "
                f"Valor alto: {formatar_moeda(valor_alto, self._moeda)}"
            ),
            text_color=CORES["sucesso"],
        )

    def _aplicar_valores(self) -> None:
        valor_baixo, valor_alto, erro = self._calcular()
        if erro:
            messagebox.showwarning("Calcular limites", erro, parent=self)
            return
        if valor_baixo is None or valor_alto is None:
            messagebox.showwarning(
                "Calcular limites",
                "Nao foi possivel calcular os limites.",
                parent=self,
            )
            return

        self._ao_aplicar(valor_baixo, valor_alto)
        self._ao_fechar()


def abrir_calcular_limites_monitoramento(
    pai: ctk.CTk | ctk.CTkToplevel,
    preco_atual: float,
    moeda: str,
    ao_aplicar: Callable[[float, float], None],
    *,
    titulo_ativo: str | None = None,
) -> JanelaCalcularLimitesMonitoramento | None:
    if not pai.winfo_exists() or preco_atual <= 0:
        return None
    return JanelaCalcularLimitesMonitoramento(
        pai,
        preco_atual,
        moeda,
        ao_aplicar,
        titulo_ativo=titulo_ativo,
    )
