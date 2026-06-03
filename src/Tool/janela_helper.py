"""Helper para abrir janelas desktop maximizadas (padrao global do usuario)."""


def maximizar_janela(janela) -> None:
    """
    Maximiza a janela principal no Windows (zoomed).
    Em outros SO tenta alternativas compativeis com Tk.
    """
    try:
        janela.state("zoomed")
        return
    except Exception:
        pass
    try:
        janela.attributes("-zoomed", True)
    except Exception:
        pass
