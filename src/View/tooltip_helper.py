"""Tooltip flutuante para widgets CustomTkinter (explicacoes ao passar o mouse)."""
from __future__ import annotations

import customtkinter as ctk

from src.View.tema import CORES

_LARGURA_TEXTO = 340
_PADDING_TEXTO_X = 22
_PADDING_TEXTO_Y = 16
_PADDING_MOLDURA = 8
_PADDING_JANELA = 10
_ATRASO_ESCONDER_MS = 80
_TOOLTIPS_ATIVOS: list["_TooltipFlutuante"] = []


def fechar_todos_tooltips_indicadores() -> None:
    """Remove tooltips abertos (troca de aba, fechar janela, rolagem)."""
    for tooltip in list(_TOOLTIPS_ATIVOS):
        tooltip.forcar_esconder()


def _mouse_sobre_widget(widget: ctk.CTkBaseClass, x: int, y: int) -> bool:
    """Verifica se o ponteiro ainda esta dentro da area do widget."""
    try:
        if not widget.winfo_exists():
            return False
        wx = widget.winfo_rootx()
        wy = widget.winfo_rooty()
        ww = widget.winfo_width()
        wh = widget.winfo_height()
        return wx <= x < wx + ww and wy <= y < wy + wh
    except Exception:
        return False


class _TooltipFlutuante:
    """Uma instancia por indicador; fecha ao sair de todos os widgets do grupo."""

    def __init__(self, titulo: str, explicacao: str, widgets: list) -> None:
        self._titulo = titulo.strip()
        self._explicacao = explicacao.strip()
        self._widgets = [w for w in widgets if w is not None]
        _TOOLTIPS_ATIVOS.append(self)
        self._janela: ctk.CTkToplevel | None = None
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

    def _destruir_janela(self) -> None:
        if self._janela is not None:
            try:
                if self._janela.winfo_exists():
                    self._janela.destroy()
            except Exception:
                pass
            self._janela = None

    def _ainda_sobre_grupo(self) -> bool:
        try:
            x = self._widgets[0].winfo_pointerx()
            y = self._widgets[0].winfo_pointery()
        except Exception:
            return False
        return any(_mouse_sobre_widget(widget, x, y) for widget in self._widgets)

    def _posicionar(self, widget: ctk.CTkBaseClass) -> None:
        if self._janela is None:
            return

        try:
            moldura = self._janela.winfo_children()[0]
        except IndexError:
            return

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

        x = widget.winfo_rootx() + 12
        y = widget.winfo_rooty() + widget.winfo_height() + 8

        tela_largura = widget.winfo_screenwidth()
        tela_altura = widget.winfo_screenheight()
        if x + largura > tela_largura - 8:
            x = max(8, tela_largura - largura - 8)
        if y + altura > tela_altura - 8:
            y = max(8, widget.winfo_rooty() - altura - 8)

        self._janela.geometry(f"{largura}x{altura}+{x}+{y}")

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

        if self._janela is not None:
            try:
                if self._janela.winfo_exists():
                    self._posicionar(widget)
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

        self._janela.resizable(False, False)
        self._posicionar(widget)

    def esconder(self, evento=None) -> None:
        widget = evento.widget if evento is not None else None
        if widget is None and self._widgets:
            widget = self._widgets[0]
        if widget is None:
            self._destruir_janela()
            return

        self._cancelar_esconder()

        def fechar() -> None:
            self._id_esconder = None
            self._widget_agenda = None
            if self._ainda_sobre_grupo():
                return
            self._destruir_janela()

        try:
            self._widget_agenda = widget
            self._id_esconder = widget.after(_ATRASO_ESCONDER_MS, fechar)
        except Exception:
            fechar()

    def forcar_esconder(self, _evento=None) -> None:
        """Fecha imediatamente (troca de aba, rolagem, clique)."""
        self._cancelar_esconder()
        self._destruir_janela()

    def __del__(self) -> None:
        if self in _TOOLTIPS_ATIVOS:
            _TOOLTIPS_ATIVOS.remove(self)


def vincular_tooltip_indicador(widgets: list, titulo: str, explicacao: str) -> None:
    """Mostra explicacao didatica ao passar o mouse sobre o card do indicador."""
    if not explicacao.strip() or not widgets:
        return

    tooltip = _TooltipFlutuante(titulo, explicacao, widgets)
    for widget in widgets:
        try:
            widget.configure(cursor="question_arrow")
        except Exception:
            pass
        widget.bind("<Enter>", tooltip.mostrar, add=True)
        widget.bind("<Leave>", tooltip.esconder, add=True)
        widget.bind("<ButtonPress>", tooltip.forcar_esconder, add=True)

    # Ao rolar a lista, remove tooltips que ficariam flutuando na tela.
    try:
        pai = widgets[0].master
        while pai is not None:
            nome_classe = type(pai).__name__
            if nome_classe == "CTkScrollableFrame":
                for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                    pai.bind(evento, tooltip.forcar_esconder, add=True)
                break
            pai = getattr(pai, "master", None)
    except Exception:
        pass
