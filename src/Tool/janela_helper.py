"""Helper para abrir janelas desktop maximizadas no monitor da janela pai."""
from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

_MONITOR_PADRAO_MAIS_PROXIMO = 2
_GA_RAIZ = 2
_SW_MAXIMIZE = 3
_SW_RESTORE = 9
_SWP_SHOWWINDOW = 0x0040
_GWL_STYLE = -16
_WS_MINIMIZEBOX = 0x00020000
_WS_MAXIMIZEBOX = 0x00010000
_WS_SYSMENU = 0x00080000
_WS_CAPTION = 0x00C00000
_SWP_FRAMECHANGED = 0x0020
_SWP_NOMOVE = 0x0002
_SWP_NOSIZE = 0x0001
_SWP_NOZORDER = 0x0004
_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
_MONITORINFOF_PRIMARIO = 1
_MS_FINALIZAR_ABERTURA = 500
_MS_ENTRE_TENTATIVAS_MAX = 120
_MAX_TENTATIVAS_ABERTURA = 6
_LARGURA_INICIAL_FILHA = 960
_ALTURA_INICIAL_FILHA = 640
_TOLERANCIA_COBRE_MONITOR_PX = 12
_MARGEM_INFERIOR_AREA_TRABALHO_PX = 8


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


def _dwmapi():
    import ctypes

    return ctypes.windll.dwmapi


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


def _retangulo_area_trabalho_ponto(x: int, y: int) -> tuple[int, int, int, int] | None:
    """Area de trabalho do monitor que contem o ponto (coordenadas de tela)."""
    if not _eh_windows():
        return None
    try:
        import ctypes
        from ctypes import wintypes

        ponto = wintypes.POINT(int(x), int(y))
        handle = _user32().MonitorFromPoint(ponto, _MONITOR_PADRAO_MAIS_PROXIMO)
        if not handle:
            return None
        info = _info_de_handle_monitor(handle)
        return info.retangulo_trabalho() if info else None
    except Exception:
        return None


def _obter_area_trabalho_referencia(referencia) -> tuple[int, int, int, int] | None:
    """Resolve a area util do monitor da janela de referencia (sem barra de tarefas)."""
    area = _retangulo_monitor_windows_api(referencia)
    if area is not None:
        return area

    try:
        referencia.update_idletasks()
        cx = int(referencia.winfo_rootx() + referencia.winfo_width() // 2)
        cy = int(referencia.winfo_rooty() + referencia.winfo_height() // 2)
        area = _retangulo_area_trabalho_ponto(cx, cy)
        if area is not None:
            return area
    except Exception:
        pass

    monitor = obter_monitor_principal()
    if monitor is not None:
        return monitor.retangulo_trabalho()
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
            cx = int(janela.winfo_rootx() + janela.winfo_width() // 2)
            cy = int(janela.winfo_rooty() + janela.winfo_height() // 2)
            retorno = _retangulo_area_trabalho_ponto(cx, cy)
            if retorno:
                return retorno
        except Exception:
            pass

    monitor = obter_monitor_principal()
    if monitor is not None:
        return monitor.retangulo_trabalho()

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


def _retangulo_janela_externo(janela) -> tuple[int, int, int, int] | None:
    """Retorna (x, y, largura, altura) do retangulo externo da janela (inclui bordas)."""
    if _eh_windows():
        hwnd = _hwnd(janela)
        if hwnd:
            try:
                import ctypes
                from ctypes import wintypes

                rect = wintypes.RECT()
                if _user32().GetWindowRect(hwnd, ctypes.byref(rect)):
                    return (
                        int(rect.left),
                        int(rect.top),
                        int(rect.right - rect.left),
                        int(rect.bottom - rect.top),
                    )
            except Exception:
                pass
    try:
        janela.update_idletasks()
        return (
            int(janela.winfo_rootx()),
            int(janela.winfo_rooty()),
            int(janela.winfo_width()),
            int(janela.winfo_height()),
        )
    except Exception:
        return None


def _area_trabalho_referencia(referencia) -> tuple[int, int, int, int] | None:
    """Area de trabalho do monitor onde a janela de referencia (pai) esta."""
    return _retangulo_area_trabalho_monitor(referencia)


def _janela_cobre_area(
    janela,
    area: tuple[int, int, int, int],
    tolerancia: int = _TOLERANCIA_COBRE_MONITOR_PX,
) -> bool:
    """Verifica se a janela ocupa a area de trabalho sem cobrir a barra de tarefas."""
    x, y, largura, altura = area
    retangulo = _retangulo_janela_externo(janela)
    if retangulo is None:
        return False
    try:
        jx, jy, jw, jh = retangulo
        limite_inferior = y + altura - _MARGEM_INFERIOR_AREA_TRABALHO_PX
        if jx + jw > x + largura + tolerancia:
            return False
        if jy + jh > limite_inferior + tolerancia:
            return False
        return (
            abs(jx - x) <= tolerancia
            and abs(jy - y) <= tolerancia
            and abs(jw - largura) <= tolerancia + 24
            and abs(jh - altura) <= tolerancia + 24
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
    Preenche a area util do monitor (rcWork) sem cobrir a barra de tarefas.
    Usa geometry exata em vez de state('zoomed'), que no Windows costuma invadir a taskbar.
    """
    ref = referencia or janela
    area = area_trabalho or _area_trabalho_referencia(ref)
    if area is not None and not _janela_cobre_area(janela, area):
        x, y, largura, altura = area
        _preparar_janela_visivel(janela, ref)
        _restaurar_janela(janela)
        altura_util = max(200, altura - _MARGEM_INFERIOR_AREA_TRABALHO_PX)
        posicionar_janela_na_area_trabalho(janela, x, y, largura, altura_util)

    try:
        janela.update_idletasks()
    except Exception:
        pass

    _reaplicar_controles_barra_titulo_apos_layout(janela)


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


def _maximizar_na_abertura_unica(
    janela,
    referencia,
    area_trabalho: tuple[int, int, int, int] | None = None,
) -> None:
    """
    Posiciona no monitor correto e maximiza uma unica vez.
    Nao restaura nem redimensiona de novo — evita flicker na abertura.
    """
    ref = referencia or janela
    _preparar_janela_visivel(janela, ref)
    area = area_trabalho or _area_trabalho_referencia(ref)

    if area is not None:
        _posicionar_no_monitor_antes_maximizar(janela, area)

    _garantir_tamanho_monitor_final(janela, ref, area)


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


_MARGEM_CENTRALIZAR_MODAL = 12


def _aplicar_posicao_modal_centralizado(
    janela,
    referencia,
    largura: int,
    altura: int,
    *,
    margem: int = _MARGEM_CENTRALIZAR_MODAL,
) -> tuple[int, int, int, int]:
    """Calcula e aplica posicao central na area de trabalho; retorna (largura, altura, x, y)."""
    janela.update_idletasks()
    largura = max(200, int(largura))
    altura = max(120, int(altura))

    area = _obter_area_trabalho_referencia(referencia)
    if area is None:
        referencia.update_idletasks()
        px = int(referencia.winfo_rootx())
        py = int(referencia.winfo_rooty())
        plarg = int(referencia.winfo_width())
        palt = int(referencia.winfo_height())
        x = px + max(0, (plarg - largura) // 2)
        y = py + max(0, (palt - altura) // 2)
        janela.geometry(f"{largura}x{altura}+{x}+{y}")
        posicionar_janela_na_area_trabalho(janela, x, y, largura, altura)
        return largura, altura, x, y

    ax, ay, alarg, aalt = area
    largura = min(largura, alarg - 2 * margem)
    altura = min(altura, aalt - 2 * margem)
    x = ax + max(margem, (alarg - largura) // 2)
    y = ay + max(margem, (aalt - altura) // 2)
    x = max(ax + margem, min(x, ax + alarg - largura - margem))
    y = max(ay + margem, min(y, ay + aalt - altura - margem))

    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    posicionar_janela_na_area_trabalho(janela, x, y, largura, altura)
    return largura, altura, x, y


def centralizar_janela_sobre_referencia(
    janela,
    referencia,
    largura: int,
    altura: int,
    *,
    margem: int = _MARGEM_CENTRALIZAR_MODAL,
    reagendar: bool = True,
) -> None:
    """
    Centraliza janela modal na area de trabalho do monitor (acima da barra de tarefas).
    Reaplica a posicao ao exibir a janela para o Windows nao sobrescrever o geometry.
    """
    try:
        _aplicar_posicao_modal_centralizado(
            janela,
            referencia,
            largura,
            altura,
            margem=margem,
        )
        if not reagendar:
            return

        estado = {"largura": largura, "altura": altura}

        def reaplicar() -> None:
            if not janela_ui_ainda_ativa(janela):
                return
            try:
                janela.update_idletasks()
                largura_atual = max(estado["largura"], int(janela.winfo_reqwidth()))
                altura_atual = max(estado["altura"], int(janela.winfo_reqheight()))
                estado["largura"] = largura_atual
                estado["altura"] = altura_atual
                _aplicar_posicao_modal_centralizado(
                    janela,
                    referencia,
                    largura_atual,
                    altura_atual,
                    margem=margem,
                )
            except Exception:
                pass

        def ao_exibir(_evento=None) -> None:
            agendar_na_ui(janela, reaplicar)

        if not getattr(janela, "_financeiro_reagendar_centralizar", False):
            janela._financeiro_reagendar_centralizar = True
            try:
                janela.bind("<Map>", ao_exibir, add=True)
            except Exception:
                pass

        agendar_na_ui(janela, reaplicar)
        try:
            janela.after(80, reaplicar)
            janela.after(250, reaplicar)
        except Exception:
            pass
    except Exception:
        pass


def centralizar_janela_na_tela(
    janela,
    largura: int,
    altura: int,
    *,
    margem: int = _MARGEM_CENTRALIZAR_MODAL,
) -> None:
    """Centraliza na area de trabalho do monitor principal."""
    try:
        monitor = obter_monitor_principal()
        if monitor is None:
            janela.update_idletasks()
            largura = max(200, int(largura))
            altura = max(120, int(altura))
            x = int((janela.winfo_screenwidth() - largura) / 2)
            y = int((janela.winfo_screenheight() - altura) / 2)
            janela.geometry(f"{largura}x{altura}+{x}+{y}")
            return

        class _ReferenciaMonitor:
            def winfo_rootx(self) -> int:
                return monitor.x

            def winfo_rooty(self) -> int:
                return monitor.y

            def winfo_width(self) -> int:
                return monitor.largura

            def winfo_height(self) -> int:
                return monitor.altura

            def update_idletasks(self) -> None:
                pass

        centralizar_janela_sobre_referencia(
            janela,
            _ReferenciaMonitor(),
            largura,
            altura,
            margem=margem,
            reagendar=True,
        )
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


def ajustar_janela_area_trabalho(
    janela,
    referencia=None,
    area_trabalho: tuple[int, int, int, int] | None = None,
) -> None:
    """Recoloca a janela na area util do monitor, sem cobrir a barra de tarefas."""
    ref = referencia or janela
    area = area_trabalho or _area_trabalho_referencia(ref)
    _garantir_tamanho_monitor_final(janela, ref, area)


def garantir_controles_barra_titulo_janela(janela) -> None:
    """
    Restaura botoes minimizar, maximizar/restaurar e fechar no Windows.
    Aplicacao unica e sem alterar tamanho/estado — evita loop com geometry/maximizar.
    """
    if getattr(janela, "_financeiro_controles_titulo_ok", False):
        return

    if not _eh_windows():
        janela._financeiro_controles_titulo_ok = True
        return

    try:
        janela.update_idletasks()
    except Exception:
        pass

    hwnd = _hwnd(janela)
    if not hwnd:
        return

    try:
        flags = _WS_MINIMIZEBOX | _WS_MAXIMIZEBOX | _WS_SYSMENU | _WS_CAPTION
        estilo = _user32().GetWindowLongW(hwnd, _GWL_STYLE)
        if (estilo & flags) == flags:
            janela._financeiro_controles_titulo_ok = True
            return
        _user32().SetWindowLongW(hwnd, _GWL_STYLE, estilo | flags)
        _user32().SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOZORDER | _SWP_FRAMECHANGED,
        )
        janela._financeiro_controles_titulo_ok = True
    except Exception:
        pass


def _reaplicar_controles_barra_titulo_apos_layout(janela) -> None:
    """Revalida botoes da barra apos geometry/maximizar (sem loop no Map)."""
    if not janela_ui_ainda_ativa(janela):
        return
    janela._financeiro_controles_titulo_ok = False
    garantir_controles_barra_titulo_janela(janela)


def reaplicar_controles_barra_titulo_janela(janela) -> None:
    """Restaura botoes min/max/fechar apos o layout da janela (telas e popups)."""
    _reaplicar_controles_barra_titulo_apos_layout(janela)


def aplicar_tema_barra_titulo_janela(janela, escuro: bool | None = None) -> None:
    """Aplica barra de titulo escura ou clara no Windows conforme o tema do programa."""
    if not _eh_windows():
        return
    try:
        janela.update_idletasks()
    except Exception:
        pass

    hwnd = _hwnd(janela)
    if not hwnd:
        return

    if escuro is None:
        from src.View.tema import obter_modo_aparencia

        escuro = obter_modo_aparencia() == "escuro"

    try:
        import ctypes

        valor = ctypes.c_int(1 if escuro else 0)
        for atributo in (_DWMWA_USE_IMMERSIVE_DARK_MODE, _DWMWA_USE_IMMERSIVE_DARK_MODE_OLD):
            try:
                if _dwmapi().DwmSetWindowAttribute(
                    hwnd,
                    atributo,
                    ctypes.byref(valor),
                    ctypes.sizeof(valor),
                ) == 0:
                    break
            except Exception:
                continue
    except Exception:
        pass


def _vincular_tema_barra_titulo_janela(janela) -> None:
    if getattr(janela, "_financeiro_tema_titulo_vinculado", False):
        return
    janela._financeiro_tema_titulo_vinculado = True

    def reaplicar(_evento=None) -> None:
        if not janela_ui_ainda_ativa(janela):
            return
        aplicar_tema_barra_titulo_janela(janela)

    try:
        janela.bind("<Map>", reaplicar, add=True)
    except Exception:
        pass
    agendar_na_ui(janela, reaplicar)


def configurar_aparencia_janela(janela) -> None:
    """Aplica barra de titulo escura/clara alinhada ao tema global."""
    _vincular_tema_barra_titulo_janela(janela)
    aplicar_tema_barra_titulo_janela(janela)


def aplicar_tema_barra_titulo_janelas_abertas() -> None:
    """Reaplica o tema da barra de titulo em todas as janelas CustomTkinter abertas."""
    try:
        import customtkinter as ctk

        raiz = tk._default_root
        if raiz is None:
            return

        pilha = [raiz]
        visitados: set[str] = set()
        while pilha:
            widget = pilha.pop()
            wid = str(widget)
            if wid in visitados:
                continue
            visitados.add(wid)
            if isinstance(widget, (ctk.CTk, ctk.CTkToplevel)):
                aplicar_tema_barra_titulo_janela(widget)
            try:
                pilha.extend(widget.winfo_children())
            except Exception:
                continue
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
    Maximiza a janela uma unica vez na abertura (monitor do pai ou do INI).
    Nao reajusta depois — evita flicker ao minimizar/restaurar ou carregar dados.
    """
    if getattr(janela, "_financeiro_abertura_maximizada", False):
        if ao_apos_layout is not None:
            agendar_na_ui(janela, ao_apos_layout)
        return

    referencia = _resolver_janela_referencia(janela, janela_pai)
    area_salva: tuple[int, int, int, int] | None = None
    if monitor_inicial and referencia is janela:
        monitor = resolver_monitor_por_dispositivo(monitor_inicial)
        if monitor is not None:
            area_salva = monitor.retangulo_trabalho()

    estado = {"executado": False}

    def executar_abertura() -> None:
        if estado["executado"]:
            return
        if not janela_ui_ainda_ativa(janela):
            return

        estado["executado"] = True
        janela._financeiro_abertura_maximizada = True

        area_alvo = (
            area_salva
            if area_salva and referencia is janela
            else _area_trabalho_referencia(referencia)
        )
        _maximizar_na_abertura_unica(janela, referencia, area_alvo)
        configurar_aparencia_janela(janela)

        if ao_apos_layout is not None:
            try:
                janela.update_idletasks()
            except Exception:
                pass
            ao_apos_layout()

        if ao_salvar_monitor is not None:
            dispositivo = obter_dispositivo_monitor_janela(janela)
            if dispositivo:
                try:
                    ao_salvar_monitor(dispositivo)
                except Exception:
                    pass

    # Um unico agendamento apos o layout inicial (sem retries nem <Map>).
    try:
        janela.after(50, executar_abertura)
    except (RuntimeError, Exception):
        pass

    referencia_modal = _resolver_janela_referencia(janela, janela_pai)
    if referencia_modal is not janela:
        configurar_janela_filha_modal(janela, referencia_modal)


def _aplicar_grab_modal(janela, janela_pai) -> None:
    if not janela_ui_ainda_ativa(janela):
        return
    try:
        janela.grab_set()
        janela.focus_force()
        if janela_pai is not None and janela_ui_ainda_ativa(janela_pai):
            janela.lift(janela_pai)
    except Exception:
        pass


def _tem_filhas_modais_ativas(pai) -> bool:
    filhas = getattr(pai, "_financeiro_filhas_modais", None)
    if not filhas:
        return False
    ativas = [item for item in filhas if janela_ui_ainda_ativa(item)]
    pai._financeiro_filhas_modais = ativas
    return len(ativas) > 0


def _focar_ultima_filha_modal(pai) -> None:
    filhas = getattr(pai, "_financeiro_filhas_modais", []) or []
    for filha in reversed(filhas):
        if janela_ui_ainda_ativa(filha):
            try:
                filha.lift(pai)
                filha.focus_force()
            except Exception:
                pass
            return


def _registrar_filha_modal_no_pai(pai, filha) -> None:
    filhas = getattr(pai, "_financeiro_filhas_modais", None)
    if filhas is None:
        filhas = []
        pai._financeiro_filhas_modais = filhas
    if filha not in filhas:
        filhas.append(filha)

    if not getattr(pai, "_financeiro_guardiao_fechar", False):
        pai._financeiro_guardiao_fechar = True
        comando_anterior = pai.protocol("WM_DELETE_WINDOW") or ""

        def _fechar_pai_com_filhas_abertas() -> None:
            if _tem_filhas_modais_ativas(pai):
                _focar_ultima_filha_modal(pai)
                return
            if comando_anterior:
                pai.tk.call(comando_anterior)
            else:
                pai.destroy()

        pai.protocol("WM_DELETE_WINDOW", _fechar_pai_com_filhas_abertas)

    def _remover_filha(_evento=None) -> None:
        lista = getattr(pai, "_financeiro_filhas_modais", []) or []
        if filha in lista:
            lista.remove(filha)

    filha.bind("<Destroy>", _remover_filha, add=True)


def _redirecionar_foco_para_filha(filha, pai) -> None:
    if not janela_ui_ainda_ativa(filha):
        return

    def _ao_focar_pai(_evento=None) -> None:
        if not janela_ui_ainda_ativa(filha):
            return
        agendar_na_ui(filha, lambda: _aplicar_grab_modal(filha, pai))

    try:
        pai.bind("<FocusIn>", _ao_focar_pai, add=True)
    except Exception:
        pass


def configurar_janela_filha_modal(janela, janela_pai=None) -> None:
    """
    Impede interacao com a janela pai enquanto a filha estiver aberta.
    Use automaticamente via configurar_janela_maximizada ou chame apos criar CTkToplevel.
    """
    pai = janela_pai or _resolver_janela_referencia(janela, None)
    if pai is None or pai is janela:
        return
    if getattr(janela, "_financeiro_modal_configurada", False):
        return

    janela._financeiro_modal_configurada = True
    janela._financeiro_janela_pai_modal = pai
    configurar_aparencia_janela(janela)

    def _controles_apos_exibir() -> None:
        _reaplicar_controles_barra_titulo_apos_layout(janela)

    agendar_na_ui(janela, _controles_apos_exibir)
    try:
        janela.after(150, _controles_apos_exibir)
    except Exception:
        pass

    try:
        janela.transient(pai)
    except Exception:
        pass

    _registrar_filha_modal_no_pai(pai, janela)
    _redirecionar_foco_para_filha(janela, pai)

    def _aplicar_ao_exibir(_evento=None) -> None:
        _aplicar_grab_modal(janela, pai)

    try:
        janela.bind("<Map>", _aplicar_ao_exibir, add=True)
    except Exception:
        pass
    agendar_na_ui(janela, _aplicar_ao_exibir)


def liberar_modal_janela_filha(janela) -> None:
    """Libera o bloqueio modal e devolve o foco ao pai, se ainda existir."""
    try:
        janela.grab_release()
    except Exception:
        pass

    pai = getattr(janela, "_financeiro_janela_pai_modal", None)
    if pai is not None and janela_ui_ainda_ativa(pai):
        if getattr(pai, "_financeiro_modal_configurada", False):
            agendar_na_ui(pai, lambda: _aplicar_grab_modal(pai, getattr(pai, "_financeiro_janela_pai_modal", None)))
        else:
            try:
                pai.focus_force()
            except Exception:
                pass


def reaplicar_grab_janela_filha(janela) -> None:
    """Reaplica grab apos fechar um dialogo modal aberto por esta janela."""
    if not getattr(janela, "_financeiro_modal_configurada", False):
        return
    pai = getattr(janela, "_financeiro_janela_pai_modal", None)
    agendar_na_ui(janela, lambda: _aplicar_grab_modal(janela, pai))


def janela_ui_ainda_ativa(janela) -> bool:
    """Verifica se a janela Tk ainda existe e pode receber callbacks."""
    try:
        return bool(janela.winfo_exists())
    except (RuntimeError, AttributeError):
        return False
    except Exception:
        return False


def agendar_na_ui(janela, callback) -> None:
    """Agenda callback na thread principal, ignorando se a janela ja foi fechada."""
    if not janela_ui_ainda_ativa(janela):
        return

    def executar_com_seguranca() -> None:
        if not janela_ui_ainda_ativa(janela):
            return
        try:
            callback()
        except tk.TclError:
            pass
        except RuntimeError:
            pass

    try:
        janela.after(0, executar_com_seguranca)
    except RuntimeError:
        pass
    except Exception:
        pass


def executar_em_thread(janela, funcao, ao_concluir) -> None:
    """
    Executa funcao em thread de fundo e chama ao_concluir(resultado, erro) na UI.
    Evita RuntimeError quando a janela e fechada antes do trabalho terminar.
    """
    import threading

    def trabalho() -> None:
        try:
            resultado = funcao()
            agendar_na_ui(janela, lambda r=resultado: ao_concluir(r, None))
        except Exception as exc:
            agendar_na_ui(janela, lambda e=exc: ao_concluir(None, str(e)))

    threading.Thread(target=trabalho, daemon=True).start()
