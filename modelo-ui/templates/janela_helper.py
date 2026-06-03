"""Helper canonico: janelas maximizadas no monitor da janela pai (copiar para src/Tool/)."""
from __future__ import annotations

from collections.abc import Callable


def _resolver_janela_referencia(janela, janela_pai=None):
    """Retorna a janela de referencia (pai) para posicionar filhas no mesmo monitor."""
    if janela_pai is not None:
        return janela_pai
    try:
        mestre = janela.master
        if mestre is None:
            return janela
        topo_mestre = mestre.winfo_toplevel()
        topo_janela = janela.winfo_toplevel()
        if topo_mestre.winfo_id() != topo_janela.winfo_id():
            return topo_mestre
    except Exception:
        pass
    return janela


def posicionar_janela_no_monitor_referencia(janela, referencia) -> None:
    """
    Coloca a janela sobre a referencia antes de maximizar.
    No Windows, o zoom usa o monitor onde a janela esta; sem isso abre no monitor principal.
    """
    if referencia is janela:
        return
    try:
        referencia.update_idletasks()
        janela.update_idletasks()
        x = int(referencia.winfo_rootx())
        y = int(referencia.winfo_rooty())
        largura = max(480, int(referencia.winfo_width() or 800))
        altura = max(360, int(referencia.winfo_height() or 600))
        largura = min(largura, int(referencia.winfo_screenwidth()))
        altura = min(altura, int(referencia.winfo_screenheight()))
        janela.geometry(f"{largura}x{altura}+{x}+{y}")
        janela.update_idletasks()
    except Exception:
        pass


def _vincular_janela_filha(janela, referencia) -> None:
    if referencia is janela:
        return
    try:
        janela.transient(referencia)
    except Exception:
        pass
    try:
        janela.lift(referencia)
    except Exception:
        pass


def maximizar_janela(janela, referencia=None) -> None:
    """
    Maximiza no monitor da janela de referencia (pai).
    Em outros SO tenta alternativas compativeis com Tk.
    """
    ref = referencia or janela
    if referencia is not None and referencia is not janela:
        posicionar_janela_no_monitor_referencia(janela, referencia)

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
        ref.update_idletasks()
        x = int(ref.winfo_rootx())
        y = int(ref.winfo_rooty())
        largura = int(ref.winfo_screenwidth())
        altura = int(ref.winfo_screenheight())
        janela.geometry(f"{largura}x{altura}+{x}+{y}")
    except Exception:
        pass


def configurar_janela_maximizada(
    janela,
    ao_apos_layout: Callable[[], None] | None = None,
    janela_pai=None,
) -> None:
    """
    Aplica maximizacao em etapas (CTkToplevel precisa de layout apos zoom).
    Janelas filhas abrem maximizadas no mesmo monitor da janela pai.
    """
    referencia = _resolver_janela_referencia(janela, janela_pai)
    _vincular_janela_filha(janela, referencia)

    def apenas_maximizar() -> None:
        maximizar_janela(janela, referencia)
        try:
            janela.update_idletasks()
        except Exception:
            pass

    def maximizar_e_callback_layout() -> None:
        apenas_maximizar()
        if ao_apos_layout is not None:
            ao_apos_layout()

    posicionar_janela_no_monitor_referencia(janela, referencia)
    janela.after(0, apenas_maximizar)
    janela.after(120, apenas_maximizar)
    janela.after(350, maximizar_e_callback_layout)

    def ao_mapear(_evento=None) -> None:
        apenas_maximizar()

    try:
        janela.bind("<Map>", ao_mapear, add="+")
    except Exception:
        pass
