"""Helper para abrir janelas desktop maximizadas no monitor da janela pai."""
from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass

_MONITOR_PADRAO_MAIS_PROXIMO = 2
_GA_RAIZ = 2
_SW_MAXIMIZE = 3
_SW_RESTORE = 9
_SWP_SHOWWINDOW = 0x0040
_MONITORINFOF_PRIMARIO = 1


@dataclass(frozen=True)
class InfoMonitor:
    """Area de trabalho de um monitor (Windows: DISPLAY1, DISPLAY2, ...)."""

    dispositivo: str
    x: int
    y: int
    largura: int
    altura: int
    principal: bool = False

    def retangulo_trabalho(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.largura, self.altura


def _eh_windows() -> bool:
    return sys.platform == "win32"


def _user32():
    import ctypes

    return ctypes.windll.user32


def normalizar_dispositivo_monitor(nome: str) -> str:
    """Converte \\\\.\\DISPLAY2 para DISPLAY2 (formato gravado no INI)."""
    texto = (nome or "").strip()
    if not texto:
        return ""
    texto = texto.replace("\\\\.\\", "").replace("\\", "").replace("/", "")
    texto = texto.upper()
    if texto.startswith("DISPLAY") and len(texto) >= 8:
        return texto
    return ""


def _estruturas_monitor_windows():
    import ctypes

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", ctypes.c_ulong),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    return RECT, MONITORINFOEXW


def _info_de_handle_monitor(handle) -> InfoMonitor | None:
    try:
        import ctypes

        _, MONITORINFOEXW = _estruturas_monitor_windows()
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if not _user32().GetMonitorInfoW(handle, ctypes.byref(info)):
            return None

        area = info.rcWork
        largura = int(area.right - area.left)
        altura = int(area.bottom - area.top)
        if largura <= 0 or altura <= 0:
            return None

        dispositivo = normalizar_dispositivo_monitor(info.szDevice)
        if not dispositivo:
            dispositivo = "DISPLAY1"

        return InfoMonitor(
            dispositivo=dispositivo,
            x=int(area.left),
            y=int(area.top),
            largura=largura,
            altura=altura,
            principal=bool(info.dwFlags & _MONITORINFOF_PRIMARIO),
        )
    except Exception:
        return None


def listar_monitores() -> list[InfoMonitor]:
    """Lista monitores conectados; no Windows usa EnumDisplayMonitors."""
    if not _eh_windows():
        return []

    try:
        import ctypes

        RECT, _ = _estruturas_monitor_windows()
        encontrados: list[InfoMonitor] = []

        def _callback(handle, _hdc, _rect, _data):
            info = _info_de_handle_monitor(handle)
            if info is not None:
                encontrados.append(info)
            return True

        tipo_callback = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(RECT),
            ctypes.c_long,
        )
        _user32().EnumDisplayMonitors(None, None, tipo_callback(_callback), 0)
        return encontrados
    except Exception:
        return []


def obter_monitor_principal() -> InfoMonitor | None:
    for monitor in listar_monitores():
        if monitor.principal:
            return monitor
    monitores = listar_monitores()
    return monitores[0] if monitores else None


def resolver_monitor_por_dispositivo(dispositivo_salvo: str | None) -> InfoMonitor | None:
    """
    Busca o monitor salvo no INI; se nao existir mais, retorna o monitor principal.
    """
    monitores = listar_monitores()
    if not monitores:
        return None

    nome = normalizar_dispositivo_monitor(dispositivo_salvo or "")
    if nome:
        for monitor in monitores:
            if monitor.dispositivo == nome:
                return monitor

    principal = obter_monitor_principal()
    return principal or monitores[0]


def obter_dispositivo_monitor_janela(janela) -> str | None:
    """Retorna DISPLAYn do monitor onde a janela esta (Windows)."""
    if not _eh_windows():
        return None
    try:
        hwnd = _hwnd(janela)
        if not hwnd:
            return None
        handle = _user32().MonitorFromWindow(hwnd, _MONITOR_PADRAO_MAIS_PROXIMO)
        if not handle:
            return None
        info = _info_de_handle_monitor(handle)
        return info.dispositivo if info else None
    except Exception:
        return None


def _hwnd(janela) -> int:
    try:
        hwnd = int(janela.winfo_id())
    except Exception:
        return 0
    if not _eh_windows() or not hwnd:
        return hwnd
    try:
        raiz = _user32().GetAncestor(hwnd, _GA_RAIZ)
        return int(raiz) if raiz else hwnd
    except Exception:
        return hwnd


def _monitor_de_janela(janela) -> int | None:
    if not _eh_windows():
        return None
    try:
        hwnd = _hwnd(janela)
        if not hwnd:
            return None
        monitor = _user32().MonitorFromWindow(hwnd, _MONITOR_PADRAO_MAIS_PROXIMO)
        return int(monitor) if monitor else None
    except Exception:
        return None


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
        hwnd = _hwnd(janela)
        if not hwnd:
            return None

        handle = _user32().MonitorFromWindow(hwnd, _MONITOR_PADRAO_MAIS_PROXIMO)
        if not handle:
            return None

        info = _info_de_handle_monitor(handle)
        return info.retangulo_trabalho() if info else None
    except Exception:
        return None


def _janela_esta_maximizada(janela) -> bool:
    if _eh_windows():
        try:
            hwnd = _hwnd(janela)
            if hwnd and bool(_user32().IsZoomed(hwnd)):
                return True
        except Exception:
            pass
    try:
        return str(janela.state()) == "zoomed"
    except Exception:
        return False


def _precisa_remaximizar(janela) -> bool:
    """Detecta janela maximizada com tamanho diferente do monitor atual."""
    if not _janela_esta_maximizada(janela):
        return False
    retangulo = _retangulo_area_trabalho_monitor(janela)
    if not retangulo:
        return False
    x, y, largura, altura = retangulo
    try:
        janela.update_idletasks()
        if abs(int(janela.winfo_rootx()) - x) > 8:
            return True
        if abs(int(janela.winfo_rooty()) - y) > 8:
            return True
        if abs(int(janela.winfo_width()) - largura) > 12:
            return True
        if abs(int(janela.winfo_height()) - altura) > 12:
            return True
    except Exception:
        return False
    return False


def _posicionar_hwnd_na_area(hwnd: int, x: int, y: int, largura: int, altura: int) -> None:
    try:
        _user32().SetWindowPos(
            hwnd,
            0,
            int(x),
            int(y),
            int(max(200, largura)),
            int(max(200, altura)),
            _SWP_SHOWWINDOW,
        )
    except Exception:
        pass


def posicionar_janela_na_area_trabalho(
    janela,
    x: int,
    y: int,
    largura: int,
    altura: int,
) -> None:
    """Posiciona a janela em coordenadas absolutas (area de trabalho do monitor)."""
    try:
        janela.update_idletasks()
        try:
            janela.state("normal")
        except Exception:
            pass

        if _eh_windows():
            hwnd = _hwnd(janela)
            if hwnd:
                _posicionar_hwnd_na_area(hwnd, x, y, largura, altura)
        else:
            janela.geometry(f"{largura}x{altura}+{x}+{y}")

        janela.update_idletasks()
    except Exception:
        pass


def posicionar_janela_no_monitor_info(janela, monitor: InfoMonitor) -> None:
    """Coloca a janela na area de trabalho do monitor informado."""
    x, y, largura, altura = monitor.retangulo_trabalho()
    posicionar_janela_na_area_trabalho(janela, x, y, largura, altura)


def aplicar_monitor_inicial(janela, dispositivo_salvo: str | None) -> str | None:
    """
    Posiciona a janela no monitor salvo no INI antes da maximizacao.
    Retorna o dispositivo efetivamente usado (salvo ou principal).
    """
    monitor = resolver_monitor_por_dispositivo(dispositivo_salvo)
    if monitor is None:
        return None
    posicionar_janela_no_monitor_info(janela, monitor)
    return monitor.dispositivo


def _maximizar_hwnd_windows(
    janela,
    referencia=None,
    area_trabalho: tuple[int, int, int, int] | None = None,
) -> bool:
    try:
        hwnd = _hwnd(janela)
        if not hwnd:
            return False

        ref = referencia or janela
        retangulo = area_trabalho or _retangulo_area_trabalho_monitor(ref)
        user32 = _user32()

        if retangulo:
            x, y, largura, altura = retangulo
            user32.ShowWindow(hwnd, _SW_RESTORE)
            _posicionar_hwnd_na_area(hwnd, x, y, largura, altura)

        user32.ShowWindow(hwnd, _SW_MAXIMIZE)
        return bool(user32.IsZoomed(hwnd))
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

        posicionar_janela_na_area_trabalho(janela, x, y, largura, altura)
        try:
            janela.deiconify()
            janela.lift(referencia)
        except Exception:
            pass
    except Exception:
        pass


def maximizar_janela(
    janela,
    referencia=None,
    area_trabalho: tuple[int, int, int, int] | None = None,
) -> None:
    """
    Maximiza no monitor da janela de referencia (pai) ou no monitor atual.
    Em outros SO tenta alternativas compativeis com Tk.
    """
    ref = referencia or janela
    if referencia is not None and referencia is not janela:
        posicionar_janela_no_monitor_referencia(janela, referencia)

    try:
        janela.update_idletasks()
    except Exception:
        pass

    if _eh_windows():
        if _maximizar_hwnd_windows(janela, ref, area_trabalho=area_trabalho):
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
        retangulo = area_trabalho or _retangulo_area_trabalho_monitor(ref)
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


def _registrar_ajuste_troca_monitor(
    janela,
    ao_apos_layout: Callable[[], None] | None = None,
    ao_salvar_monitor: Callable[[str], None] | None = None,
) -> None:
    """
    Reaplica maximizacao quando a janela muda de monitor ou fica com tamanho errado.
    Opcionalmente grava o monitor atual no INI (janela principal).
    """
    estado = {
        "monitor": _monitor_de_janela(janela),
        "dispositivo": obter_dispositivo_monitor_janela(janela),
        "timer": None,
        "timer_salvar": None,
        "em_ajuste": False,
    }

    def gravar_monitor_atual() -> None:
        if ao_salvar_monitor is None:
            return
        dispositivo = obter_dispositivo_monitor_janela(janela)
        if not dispositivo or dispositivo == estado["dispositivo"]:
            return
        estado["dispositivo"] = dispositivo
        try:
            ao_salvar_monitor(dispositivo)
        except Exception:
            pass

    def executar_ajuste() -> None:
        if estado["em_ajuste"]:
            return
        if not _janela_esta_maximizada(janela) and not _precisa_remaximizar(janela):
            estado["monitor"] = _monitor_de_janela(janela)
            return

        estado["em_ajuste"] = True
        try:
            maximizar_janela(janela, janela)
            janela.update_idletasks()
            estado["monitor"] = _monitor_de_janela(janela)
            gravar_monitor_atual()
            if ao_apos_layout is not None:
                ao_apos_layout()
        except Exception:
            pass
        finally:
            janela.after(180, lambda: estado.update({"em_ajuste": False}))

    def agendar_ajuste(_evento=None) -> None:
        if estado["em_ajuste"]:
            return

        monitor_atual = _monitor_de_janela(janela)
        monitor_mudou = (
            monitor_atual is not None
            and estado["monitor"] is not None
            and monitor_atual != estado["monitor"]
        )

        if monitor_mudou and ao_salvar_monitor is not None:
            if estado["timer_salvar"] is not None:
                try:
                    janela.after_cancel(estado["timer_salvar"])
                except Exception:
                    pass
            estado["timer_salvar"] = janela.after(400, gravar_monitor_atual)

        if not monitor_mudou and not _precisa_remaximizar(janela):
            if monitor_atual is not None:
                estado["monitor"] = monitor_atual
            return

        if estado["timer"] is not None:
            try:
                janela.after_cancel(estado["timer"])
            except Exception:
                pass
        estado["timer"] = janela.after(120, executar_ajuste)

    try:
        janela.bind("<Configure>", agendar_ajuste, add="+")
    except Exception:
        pass

    try:
        janela.bind("<Map>", agendar_ajuste, add="+")
    except Exception:
        pass


def configurar_janela_maximizada(
    janela,
    ao_apos_layout: Callable[[], None] | None = None,
    janela_pai=None,
    monitor_inicial: str | None = None,
    ao_salvar_monitor: Callable[[str], None] | None = None,
) -> None:
    """
    Aplica maximizacao em etapas (CTkToplevel precisa de layout apos zoom).
    Janelas filhas abrem maximizadas no mesmo monitor da janela pai.
    Reajusta automaticamente ao trocar de monitor.
    monitor_inicial + ao_salvar_monitor: persistencia do monitor da janela principal.
    """
    referencia = _resolver_janela_referencia(janela, janela_pai)
    _maximizou_mapa = {"feito": False}
    area_inicial: tuple[int, int, int, int] | None = None
    inicial_aplicado = {"feito": False}

    if monitor_inicial and referencia is janela:
        monitor_resolvido = resolver_monitor_por_dispositivo(monitor_inicial)
        if monitor_resolvido is not None:
            area_inicial = monitor_resolvido.retangulo_trabalho()
            aplicar_monitor_inicial(janela, monitor_inicial)

    def apenas_maximizar() -> None:
        usar_area_salva = (
            area_inicial is not None
            and referencia is janela
            and not inicial_aplicado["feito"]
        )
        if usar_area_salva:
            maximizar_janela(janela, referencia, area_trabalho=area_inicial)
            inicial_aplicado["feito"] = True
        else:
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
    _registrar_ajuste_troca_monitor(janela, ao_apos_layout, ao_salvar_monitor)

    def ao_mapear(_evento=None) -> None:
        if _maximizou_mapa["feito"]:
            return
        _maximizou_mapa["feito"] = True
        janela.after(50, apenas_maximizar)

    try:
        janela.bind("<Map>", ao_mapear, add="+")
    except Exception:
        pass
