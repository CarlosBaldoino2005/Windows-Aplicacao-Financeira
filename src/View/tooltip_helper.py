"""Tooltip flutuante para widgets CustomTkinter (explicacoes ao passar o mouse)."""
from __future__ import annotations

import customtkinter as ctk

from src.View.tema import CORES

_LARGURA_TEXTO = 340
_PADDING_TEXTO_X = 22
_PADDING_TEXTO_Y = 16
_PADDING_MOLDURA = 8
_PADDING_JANELA = 10
_ATRASO_ESCONDER_MS = 120


class _TooltipFlutuante:
    """Uma instancia por grupo de widgets (evita piscar ao mover entre filhos)."""

    def __init__(self, titulo: str, explicacao: str) -> None:
        self._titulo = titulo.strip()
        self._explicacao = explicacao.strip()
        self._janela: ctk.CTkToplevel | None = None
        self._referencias = 0
        self._id_esconder: str | None = None
        self._widget_agenda: ctk.CTkBaseClass | None = None

    def _texto_completo(self) -> str:
        if self._titulo and self._explicacao:
            return f"{self._titulo}\n\n{self._explicacao}"
        return self._explicacao or self._titulo

    def _cancelar_esconder(self) -> None:
        if self._id_esconder is not None and self._widget_agenda is not None:
            try:
                self._widget_agenda.after_cancel(self._id_esconder)
            except Exception:
                pass
        self._id_esconder = None
        self._widget_agenda = None

    def mostrar(self, evento=None) -> None:
        if evento is None:
            return

        widget = evento.widget
        try:
            if not widget.winfo_exists():
                return
        except Exception:
            return

        self._cancelar_esconder()
        self._referencias += 1

        if self._janela is not None:
            try:
                if self._janela.winfo_exists():
                    return
            except Exception:
                self._janela = None

        raiz = widget.winfo_toplevel()
        self._janela = ctk.CTkToplevel(raiz)
        self._janela.wm_overrideredirect(True)
        self._janela.wm_attributes("-topmost", True)
        self._janela.configure(fg_color=CORES.get("graficoTooltipFundo", CORES["infoFundo"]))

        moldura = ctk.CTkFrame(
            self._janela,
            fg_color=CORES.get("graficoTooltipFundo", CORES["infoFundo"]),
            corner_radius=10,
            border_width=1,
            border_color=CORES["borda"],
        )
        moldura.pack(
            padx=_PADDING_JANELA,
            pady=_PADDING_JANELA,
            fill="both",
            expand=True,
        )

        rotulo = ctk.CTkLabel(
            moldura,
            text=self._texto_completo(),
            font=ctk.CTkFont(size=12),
            text_color=CORES["texto"],
            justify="left",
            anchor="w",
            wraplength=_LARGURA_TEXTO,
            width=_LARGURA_TEXTO,
        )
        rotulo.pack(
            padx=_PADDING_TEXTO_X,
            pady=_PADDING_TEXTO_Y,
            anchor="nw",
            fill="x",
        )

        moldura.update_idletasks()
        self._janela.update_idletasks()
        largura = (
            moldura.winfo_reqwidth()
            + (_PADDING_JANELA * 2)
            + (_PADDING_MOLDURA * 2)
        )
        altura = (
            moldura.winfo_reqheight()
            + (_PADDING_JANELA * 2)
            + (_PADDING_MOLDURA * 2)
        )
        self._janela.resizable(False, False)

        x = widget.winfo_rootx() + 12
        y = widget.winfo_rooty() + widget.winfo_height() + 8

        tela_largura = widget.winfo_screenwidth()
        tela_altura = widget.winfo_screenheight()
        if x + largura > tela_largura - 8:
            x = max(8, tela_largura - largura - 8)
        if y + altura > tela_altura - 8:
            y = max(8, widget.winfo_rooty() - altura - 8)

        self._janela.geometry(f"{largura}x{altura}+{x}+{y}")

    def esconder(self, evento=None) -> None:
        self._referencias = max(0, self._referencias - 1)
        if self._referencias > 0:
            return

        widget = evento.widget if evento is not None else None

        def fechar() -> None:
            self._id_esconder = None
            self._widget_agenda = None
            if self._janela is not None:
                try:
                    if self._janela.winfo_exists():
                        self._janela.destroy()
                except Exception:
                    pass
                self._janela = None

        if widget is not None:
            try:
                self._widget_agenda = widget
                self._id_esconder = widget.after(_ATRASO_ESCONDER_MS, fechar)
                return
            except Exception:
                pass
        fechar()


def vincular_tooltip_indicador(widgets: list, titulo: str, explicacao: str) -> None:
    """Mostra explicacao didatica ao passar o mouse sobre o card do indicador."""
    if not explicacao.strip():
        return

    tooltip = _TooltipFlutuante(titulo, explicacao)
    for widget in widgets:
        try:
            widget.configure(cursor="question_arrow")
        except Exception:
            pass
        widget.bind("<Enter>", tooltip.mostrar, add="+")
        widget.bind("<Leave>", tooltip.esconder, add="+")
        widget.bind("<ButtonPress>", tooltip.esconder, add="+")
