"""Botao Gerar XLSX e exportacao das grids (ordem atual da tabela)."""
from __future__ import annotations

from collections.abc import Callable
from tkinter import filedialog, ttk

import customtkinter as ctk

from src.Tool.exportar_xlsx_helper import nome_arquivo_xlsx_com_data, salvar_planilha_xlsx
from src.View import mensagem_helper as messagebox
from src.View.botao_helper import criar_botao
from src.View.grid_interacao_treeview_helper import treeview_ainda_ativa
from src.View.grid_ordenacao_helper import SUFIXO_ASCENDENTE, SUFIXO_DESCENDENTE
from src.View.tema import CORES

_TEXTO_BOTAO = "Gerar XLSX"


def limpar_rotulo_coluna_exportacao(texto: str) -> str:
    """Remove setas de ordenacao do cabecalho exportado."""
    limpo = (texto or "").strip()
    if limpo.endswith(SUFIXO_DESCENDENTE):
        return limpo[: -len(SUFIXO_DESCENDENTE)].strip()
    if limpo.endswith(SUFIXO_ASCENDENTE):
        return limpo[: -len(SUFIXO_ASCENDENTE)].strip()
    return limpo


def extrair_cabecalhos_treeview(tabela: ttk.Treeview) -> list[str]:
    """Le titulos das colunas na ordem exibida."""
    return [
        limpar_rotulo_coluna_exportacao(str(tabela.heading(coluna)["text"]))
        for coluna in tabela["columns"]
    ]


def extrair_linhas_treeview(tabela: ttk.Treeview) -> list[list[str]]:
    """Le linhas na ordem atual da grid (apos ordenacao do usuario)."""
    linhas: list[list[str]] = []
    for iid in tabela.get_children(""):
        valores = tabela.item(iid, "values")
        linhas.append([str(valor) for valor in valores])
    return linhas


def exportar_dados_para_xlsx(
    cabecalhos: list[str],
    linhas: list[list[str]],
    nome_arquivo_sugerido: str,
    *,
    janela_pai: ctk.CTkBaseClass | None = None,
    nome_aba: str | None = None,
) -> bool:
    """Abre dialogo Salvar como e grava a planilha."""
    if not linhas:
        messagebox.showwarning(
            "Exportar XLSX",
            "Nao ha dados na tabela para exportar.",
            parent=janela_pai,
        )
        return False

    caminho = filedialog.asksaveasfilename(
        parent=janela_pai,
        title="Salvar planilha",
        defaultextension=".xlsx",
        filetypes=[("Planilha Excel", "*.xlsx")],
        initialfile=nome_arquivo_xlsx_com_data(nome_arquivo_sugerido),
    )
    if not caminho:
        return False

    ok, erro = salvar_planilha_xlsx(
        caminho,
        cabecalhos,
        linhas,
        nome_aba=nome_aba or nome_arquivo_sugerido,
    )
    if not ok:
        messagebox.showerror(
            "Exportar XLSX",
            erro or "Nao foi possivel gerar a planilha.",
            parent=janela_pai,
        )
        return False

    messagebox.showinfo_com_abrir_arquivo(
        "Exportar XLSX",
        f"Planilha salva com sucesso:\n{caminho}",
        caminho,
        parent=janela_pai,
    )
    return True


def exportar_treeview_para_xlsx(
    tabela: ttk.Treeview | None,
    nome_arquivo_sugerido: str,
    *,
    janela_pai: ctk.CTkBaseClass | None = None,
) -> bool:
    """Exporta a treeview com a ordenacao visivel no momento."""
    if not treeview_ainda_ativa(tabela):
        messagebox.showwarning(
            "Exportar XLSX",
            "A tabela nao esta disponivel para exportacao.",
            parent=janela_pai,
        )
        return False

    return exportar_dados_para_xlsx(
        extrair_cabecalhos_treeview(tabela),
        extrair_linhas_treeview(tabela),
        nome_arquivo_sugerido,
        janela_pai=janela_pai or _resolver_janela_pai(tabela),
        nome_aba=nome_arquivo_sugerido,
    )


def _resolver_janela_pai(widget: ctk.CTkBaseClass | ttk.Treeview) -> ctk.CTkBaseClass | None:
    atual = widget
    while atual is not None:
        if isinstance(atual, (ctk.CTk, ctk.CTkToplevel)):
            return atual
        try:
            atual = atual.master  # type: ignore[assignment]
        except Exception:
            return None
    return None


def criar_frame_botoes_titulo_grid(pai: ctk.CTkFrame) -> ctk.CTkFrame:
    """Area no canto direito do titulo do card da grid."""
    frame = ctk.CTkFrame(pai, fg_color="transparent")
    frame.pack(side="right")
    return frame


def adicionar_botao_gerar_xlsx(
    pai_botoes: ctk.CTkFrame,
    comando: Callable[[], None],
    *,
    largura: int = 118,
) -> ctk.CTkButton:
    """Insere o botao padrao de exportacao (mais a direita se pack side=right primeiro)."""
    botao = criar_botao(
        pai_botoes,
        _TEXTO_BOTAO,
        comando,
        width=largura,
        height=28,
        font=ctk.CTkFont(size=12),
        fg_color=CORES["primaria"],
        hover_color=CORES["primariaHover"],
        text_color=CORES.get("textoInverso", "#FFFFFF"),
    )
    botao.pack(side="right", padx=(8, 0))
    return botao


def vincular_botao_exportar_treeview(
    pai_botoes: ctk.CTkFrame,
    tabela: ttk.Treeview,
    nome_arquivo_sugerido: str,
    *,
    janela_pai: ctk.CTkBaseClass | None = None,
) -> ctk.CTkButton:
    """Cria botao Gerar XLSX para uma treeview."""
    pai = janela_pai or _resolver_janela_pai(tabela)
    tabela._nome_exportacao_xlsx = nome_arquivo_sugerido  # type: ignore[attr-defined]

    def _exportar() -> None:
        exportar_treeview_para_xlsx(
            tabela,
            getattr(tabela, "_nome_exportacao_xlsx", nome_arquivo_sugerido),
            janela_pai=pai,
        )

    return adicionar_botao_gerar_xlsx(pai_botoes, _exportar)


def montar_barra_exportacao_zebrada(
    pai: ctk.CTkFrame,
    colunas: list[str],
    linhas_valores: list[list[str]],
    nome_arquivo_sugerido: str,
    *,
    janela_pai: ctk.CTkBaseClass | None = None,
) -> None:
    """Barra superior com botao Gerar XLSX para tabelas zebradas CTk."""
    barra = ctk.CTkFrame(pai, fg_color="transparent")
    barra.pack(fill="x", padx=2, pady=(2, 6))

    frame_botoes = ctk.CTkFrame(barra, fg_color="transparent")
    frame_botoes.pack(side="right")

    def _exportar() -> None:
        exportar_dados_para_xlsx(
            colunas,
            linhas_valores,
            nome_arquivo_sugerido,
            janela_pai=janela_pai or _resolver_janela_pai(pai),
            nome_aba=nome_arquivo_sugerido,
        )

    adicionar_botao_gerar_xlsx(frame_botoes, _exportar)
