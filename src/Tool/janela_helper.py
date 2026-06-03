"""Helper para abrir janelas desktop maximizadas (padrao global do usuario)."""
from __future__ import annotations

from collections.abc import Callable


def maximizar_janela(janela) -> None:
    """
    Maximiza a janela principal no Windows (zoomed).
    Em outros SO tenta alternativas compativeis com Tk.
    """
    try:
        janela.update_idletasks()
    except Exception:
        pass

    try:
        janela.state("zoomed")
        return
    except Exception:
        pass

    try:
        janela.attributes("-zoomed", True)
        return
    except Exception:
        pass

    try:
        largura = janela.winfo_screenwidth()
        altura = janela.winfo_screenheight()
        janela.geometry(f"{largura}x{altura}+0+0")
    except Exception:
        pass


def configurar_janela_maximizada(
    janela,
    ao_apos_layout: Callable[[], None] | None = None,
) -> None:
    """
    Aplica maximizacao em etapas (CTkToplevel precisa de layout apos zoom).
    Opcionalmente executa callback quando a janela ja tem tamanho real.
    """

    def apenas_maximizar() -> None:
        maximizar_janela(janela)
        try:
            janela.update_idletasks()
        except Exception:
            pass

    def maximizar_e_callback_layout() -> None:
        apenas_maximizar()
        if ao_apos_layout is not None:
            ao_apos_layout()

    janela.after(0, apenas_maximizar)
    janela.after(120, apenas_maximizar)
    # Callback de layout uma vez, apos o zoom estabilizar (evita redesenho triplo).
    janela.after(350, maximizar_e_callback_layout)

    def ao_mapear(_evento=None) -> None:
        apenas_maximizar()

    try:
        janela.bind("<Map>", ao_mapear, add="+")
    except Exception:
        pass
