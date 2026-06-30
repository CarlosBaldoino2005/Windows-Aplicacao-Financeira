"""Salvar ou imprimir figuras Matplotlib da interface."""
from __future__ import annotations

import os
import tempfile
from tkinter import filedialog

from matplotlib.figure import Figure


def salvar_figura_grafico(
    figura: Figure,
    nome_sugerido: str,
    *,
    janela_pai=None,
) -> bool:
    """Abre dialogo para salvar PNG ou PDF do grafico."""
    caminho = filedialog.asksaveasfilename(
        parent=janela_pai,
        title="Salvar grafico",
        defaultextension=".png",
        initialfile=nome_sugerido,
        filetypes=[
            ("Imagem PNG", "*.png"),
            ("Documento PDF", "*.pdf"),
        ],
    )
    if not caminho:
        return False

    extensao = os.path.splitext(caminho)[1].lower()
    if extensao == ".pdf":
        figura.savefig(caminho, format="pdf", bbox_inches="tight")
    else:
        figura.savefig(caminho, format="png", dpi=160, bbox_inches="tight")
    return True


def imprimir_figura_grafico(figura: Figure, *, janela_pai=None) -> bool:
    """Envia o grafico para a impressora padrao do Windows."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as arquivo:
            caminho = arquivo.name
        figura.savefig(caminho, format="png", dpi=160, bbox_inches="tight")
        os.startfile(caminho, "print")
        return True
    except OSError:
        return False
