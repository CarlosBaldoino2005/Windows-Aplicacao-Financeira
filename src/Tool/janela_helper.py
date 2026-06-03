"""Helper para abrir janelas desktop maximizadas no monitor da janela pai."""
from __future__ import annotations

import sys
from collections.abc import Callable


def _eh_windows() -> bool:
    return sys.platform == "win32"


def _hwnd(janela) -> int:
    try:
        hwnd = int(janela.winfo_id())
    except Exception:
        return 0
    if not _eh_windows() or not hwnd:
        return hwnd
    try:
        import ctypes

        raiz = ctypes.windll.user32.GetAncestor(hwnd, 2)
        return int(raiz) if raiz else hwnd
    except Exception:
        return hwnd


def _retangulo_area_trabalho_monitor(janela) -> tuple[int, int, int, int] | None:
    """
    Retorna (x, y, largura, altura) da area de trabalho do monitor onde a janela esta.
    No Windows usa MonitorFromWindow; em outros SO usa metricas do Tk.
    """
    if _eh_windows():
        retorno = _retangulo_monitor_windows_api(janela)
        if retorno:
            return retorno

    try:
        janela.update_idletasks()
        x = int(janela.winfo_rootx())
        y = int(janela.winfo_rooty())
        largura = int(janela.winfo_screenwidth())
        altura = int(janela.winfo_screenheight())
        return x, y, largura, altura
    except Exception:
        return None


def _retangulo_monitor_windows_api(janela) -> tuple[int, int, int, int] | None:
    try:
        import ctypes

        hwnd = _hwnd(janela)
        if not hwnd:
            return None

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", ctypes.c_ulong),
            ]

        user32 = ctypes.windll.user32
        monitor = user32.MonitorFromWindow(hwnd, 2)
        if not monitor:
            return None

        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return None

        area = info.rcWork
        largura = int(area.right - area.left)
        altura = int(area.bottom - area.top)
        if largura <= 0 or altura <= 0:
            return None
        return int(area.left), int(area.top), largura, altura
    except Exception:
        return None


def _maximizar_hwnd_windows(janela) -> bool:
    try:
        import ctypes

        hwnd = _hwnd(janela)
        if not hwnd:
            return False
        ctypes.windll.user32.ShowWindow(hwnd, 3)
        return True
    except Exception:
        return False


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
    Coloca a janela na area de trabalho do monitor da referencia (pai).
    Necessario antes do zoom no Windows com varios monitores.
    """
    if referencia is janela:
        return
    try:
        referencia.update_idletasks()
        janela.update_idletasks()

        retangulo = _retangulo_area_trabalho_monitor(referencia)
        if retangulo:
            x, y, largura, altura = retangulo
        else:
            x = int(referencia.winfo_rootx())
            y = int(referencia.winfo_rooty())
            largura = max(800, int(referencia.winfo_screenwidth()))
            altura = max(600, int(referencia.winfo_screenheight()))

        try:
            janela.state("normal")
        except Exception:
            pass

        janela.geometry(f"{largura}x{altura}+{x}+{y}")
        janela.update_idletasks()
        try:
            janela.deiconify()
            janela.lift(referencia)
        except Exception:
            pass
    except Exception:
        pass


def _vincular_janela_filha(janela, referencia) -> None:
    if referencia is janela:
        return
    try:
        janela.lift(referencia)
        janela.focus_force()
    except Exception:
        pass
    if not _eh_windows():
        try:
            janela.transient(referencia)
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

    if _eh_windows() and referencia is not janela:
        if _maximizar_hwnd_windows(janela):
            try:
                janela.update_idletasks()
            except Exception:
                pass
            return

    try:
        janela.state("normal")
        janela.update_idletasks()
        janela.state("zoomed")
        if str(janela.state()) == "zoomed":
            return
    except Exception:
        pass

    try:
        janela.attributes("-zoomed", True)
        return
    except Exception:
        pass

    try:
        retangulo = _retangulo_area_trabalho_monitor(ref)
        if retangulo:
            x, y, largura, altura = retangulo
            janela.geometry(f"{largura}x{altura}+{x}+{y}")
        else:
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
    _maximizou_mapa = {"feito": False}

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
    janela.after(80, apenas_maximizar)
    janela.after(200, apenas_maximizar)
    janela.after(450, maximizar_e_callback_layout)

    def ao_mapear(_evento=None) -> None:
        if _maximizou_mapa["feito"]:
            return
        _maximizou_mapa["feito"] = True
        janela.after(50, apenas_maximizar)

    try:
        janela.bind("<Map>", ao_mapear, add="+")
    except Exception:
        pass
