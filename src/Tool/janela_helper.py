"""Helper para abrir janelas desktop maximizadas (padrao global do usuario)."""


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
