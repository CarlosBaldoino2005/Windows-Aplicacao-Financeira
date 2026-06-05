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
_MS_FINALIZAR_ABERTURA = 500
_MS_ENTRE_TENTATIVAS_MAX = 120
_MAX_TENTATIVAS_ABERTURA = 6
_LARGURA_INICIAL_FILHA = 960
_ALTURA_INICIAL_FILHA = 640
_TOLERANCIA_COBRE_MONITOR_PX = 24


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


def _area_trabalho_referencia(referencia) -> tuple[int, int, int, int] | None:
    """Area de trabalho do monitor onde a janela de referencia (pai) esta."""
    return _retangulo_area_trabalho_monitor(referencia)


def _janela_cobre_area(
    janela,
    area: tuple[int, int, int, int],
    tolerancia: int = _TOLERANCIA_COBRE_MONITOR_PX,
) -> bool:
    """Verifica se a janela ja ocupa praticamente toda a area informada."""
    x, y, largura, altura = area
    try:
        janela.update_idletasks()
        return (
            abs(int(janela.winfo_rootx()) - x) <= 8
            and abs(int(janela.winfo_rooty()) - y) <= 8
            and abs(int(janela.winfo_width()) - largura) <= tolerancia
            and abs(int(janela.winfo_height()) - altura) <= tolerancia
        )
    except Exception:
        return False


def _janela_abertura_ok(janela, referencia) -> bool:
    """Sucesso quando a janela preenche a area de trabalho do monitor de referencia."""
    area = _area_trabalho_referencia(referencia)
    if area:
        return _janela_cobre_area(janela, area)
    return _janela_esta_maximizada(janela)


def _garantir_tamanho_monitor_final(
    janela,
    referencia,
    area_trabalho: tuple[int, int, int, int] | None = None,
) -> None:
    """
    Passo final da abertura: forca a janela a ocupar toda a area util do monitor.
    Restaurar -> tamanho do monitor -> maximizar; se preciso, geometry exata.
    """
    ref = referencia or janela
    area = area_trabalho or _area_trabalho_referencia(ref)
    if area is None:
        return

    if _janela_cobre_area(janela, area):
        return

    x, y, largura, altura = area
    _preparar_janela_visivel(janela, ref)
    _restaurar_janela(janela)
    posicionar_janela_na_area_trabalho(janela, x, y, largura, altura)
    _maximizar_janela_tk(janela)

    if not _janela_cobre_area(janela, area):
        posicionar_janela_na_area_trabalho(janela, x, y, largura, altura)

    try:
        janela.update_idletasks()
    except Exception:
        pass


def _restaurar_janela(janela) -> None:
    """Passo 1 da abertura: volta ao estado normal (equivalente ao botao Restaurar)."""
    if _eh_windows():
        hwnd = _hwnd(janela)
        if hwnd:
            try:
                _user32().ShowWindow(hwnd, _SW_RESTORE)
            except Exception:
                pass
    try:
        janela.state("normal")
    except Exception:
        pass
    try:
        janela.update_idletasks()
    except Exception:
        pass


def _maximizar_janela_tk(janela) -> None:
    """Passo 3 da abertura: maximiza (equivalente ao botao Maximizar)."""
    if _eh_windows():
        hwnd = _hwnd(janela)
        if hwnd:
            try:
                _user32().ShowWindow(hwnd, _SW_MAXIMIZE)
            except Exception:
                pass
    try:
        janela.state("zoomed")
    except Exception:
        pass
    try:
        janela.attributes("-zoomed", True)
    except Exception:
        pass
    try:
        janela.update_idletasks()
    except Exception:
        pass


def _posicionar_no_monitor_antes_maximizar(
    janela,
    area: tuple[int, int, int, int],
) -> None:
    """Passo 2: coloca a janela no monitor certo em tamanho normal antes do zoom."""
    x, y, _, _ = area
    posicionar_janela_na_area_trabalho(
        janela,
        x,
        y,
        _LARGURA_INICIAL_FILHA,
        _ALTURA_INICIAL_FILHA,
    )


def restaurar_e_maximizar_janela(
    janela,
    referencia=None,
    area_trabalho: tuple[int, int, int, int] | None = None,
) -> bool:
    """
    Sequencia usada na abertura: Restaurar -> posicionar no monitor -> Maximizar.
    Replica o gesto manual que adapta a tela ao monitor.
    """
    ref = referencia or janela
    area = area_trabalho or _area_trabalho_referencia(ref)
    _preparar_janela_visivel(janela, ref)

    _restaurar_janela(janela)

    if area is not None:
        _posicionar_no_monitor_antes_maximizar(janela, area)

    _maximizar_janela_tk(janela)
    _garantir_tamanho_monitor_final(janela, ref, area)
    return _janela_abertura_ok(janela, ref)


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


def _preparar_janela_visivel(janela, referencia=None) -> None:
    """Garante que a janela esteja visivel antes do SW_MAXIMIZE no Windows."""
    try:
        janela.deiconify()
        janela.update_idletasks()
        if referencia is not None and referencia is not janela:
            janela.lift(referencia)
    except Exception:
        pass


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
    """Coloca a janela filha no monitor da referencia (pai) em tamanho normal."""
    if referencia is janela:
        return
    area = _area_trabalho_referencia(referencia)
    if area is None:
        return
    _posicionar_no_monitor_antes_maximizar(janela, area)
    _preparar_janela_visivel(janela, referencia)


def maximizar_janela(
    janela,
    referencia=None,
    area_trabalho: tuple[int, int, int, int] | None = None,
) -> None:
    """Restaura e maximiza no monitor da janela de referencia (pai)."""
    ref = referencia or janela
    area = area_trabalho or _area_trabalho_referencia(ref)
    restaurar_e_maximizar_janela(janela, ref, area_trabalho=area)


def configurar_janela_maximizada(
    janela,
    ao_apos_layout: Callable[[], None] | None = None,
    janela_pai=None,
    monitor_inicial: str | None = None,
    ao_salvar_monitor: Callable[[str], None] | None = None,
) -> None:
    """
    Na abertura: Restaurar, Maximizar e ao final garante o tamanho do monitor.
    Executa uma vez; nao reajusta depois de carregada.
    monitor_inicial + ao_salvar_monitor: monitor salvo no INI e gravacao ao fechar.
    """
    referencia = _resolver_janela_referencia(janela, janela_pai)
    _maximizou_mapa = {"feito": False}
    _abertura_concluida = {"feito": False}
    area_inicial: tuple[int, int, int, int] | None = None
    inicial_aplicado = {"feito": False}

    if monitor_inicial and referencia is janela:
        monitor_resolvido = resolver_monitor_por_dispositivo(monitor_inicial)
        if monitor_resolvido is not None:
            area_inicial = monitor_resolvido.retangulo_trabalho()
            aplicar_monitor_inicial(janela, monitor_inicial)

    area_referencia = _area_trabalho_referencia(referencia)

    def restaurar_e_maximizar() -> None:
        usar_area_salva = (
            area_inicial is not None
            and referencia is janela
            and not inicial_aplicado["feito"]
        )
        area_alvo = area_inicial if usar_area_salva else area_referencia
        restaurar_e_maximizar_janela(janela, referencia, area_trabalho=area_alvo)
        if usar_area_salva:
            inicial_aplicado["feito"] = True

    def _concluir_abertura() -> None:
        if _abertura_concluida["feito"]:
            return

        area_final = area_inicial if area_inicial and referencia is janela else area_referencia
        _garantir_tamanho_monitor_final(janela, referencia, area_final)

        _abertura_concluida["feito"] = True
        if ao_apos_layout is not None:
            ao_apos_layout()
        if ao_salvar_monitor is not None:
            dispositivo = obter_dispositivo_monitor_janela(janela)
            if dispositivo:
                try:
                    ao_salvar_monitor(dispositivo)
                except Exception:
                    pass

    def finalizar_abertura(tentativa: int = 0) -> None:
        """Repete maximizacao na abertura; depois nao reajusta mais."""
        if _abertura_concluida["feito"]:
            return

        restaurar_e_maximizar()

        if not _janela_abertura_ok(janela, referencia) and tentativa < _MAX_TENTATIVAS_ABERTURA:
            atraso = _MS_ENTRE_TENTATIVAS_MAX + (tentativa * 60)
            janela.after(atraso, lambda t=tentativa + 1: finalizar_abertura(t))
            return

        _concluir_abertura()

    _preparar_janela_visivel(janela, referencia)
    janela.after(0, restaurar_e_maximizar)
    janela.after(80, restaurar_e_maximizar)
    janela.after(200, restaurar_e_maximizar)
    janela.after(_MS_FINALIZAR_ABERTURA, finalizar_abertura)

    def ao_mapear(_evento=None) -> None:
        if _maximizou_mapa["feito"] or _abertura_concluida["feito"]:
            return
        _maximizou_mapa["feito"] = True
        janela.after(50, lambda: finalizar_abertura(0))

    try:
        janela.bind("<Map>", ao_mapear, add="+")
    except Exception:
        pass
