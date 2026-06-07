"""Componentes reutilizaveis para listar noticias nas janelas."""
from __future__ import annotations

import webbrowser

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Model.noticia_mercado import NoticiaMercado
from src.Model.opcoes_fotos_noticias import OpcoesFotosNoticias
from src.Tool.imagem_noticia_helper import obter_imagem_noticia
from src.View.tema import CORES

# Tamanhos de fonte dos cards de noticia (titulo, meta, resumo, mensagens).
_FONTE_TITULO = 17
_FONTE_META = 13
_FONTE_RESUMO = 15
_FONTE_MENSAGEM = 14
_WRAP_TITULO = 560
_WRAP_RESUMO = 620


def limpar_container(container: ctk.CTkScrollableFrame) -> None:
    for widget in container.winfo_children():
        widget.destroy()


def exibir_mensagem_lista(
    container: ctk.CTkScrollableFrame,
    texto: str,
    pai_janela: ctk.CTk | ctk.CTkToplevel | None = None,
) -> None:
    limpar_container(container)
    ctk.CTkLabel(
        container,
        text=texto,
        font=ctk.CTkFont(size=_FONTE_MENSAGEM),
        text_color=CORES["textoSecundario"],
        wraplength=800,
        justify="left",
    ).pack(anchor="w", padx=8, pady=12)


def preencher_lista_noticias(
    container: ctk.CTkScrollableFrame,
    noticias: list[NoticiaMercado],
    pai_janela: ctk.CTk | ctk.CTkToplevel | None = None,
    traducoes: dict[str, tuple[str, str]] | None = None,
    opcoes_fotos: OpcoesFotosNoticias | None = None,
) -> None:
    limpar_container(container)
    if not noticias:
        exibir_mensagem_lista(container, "Nenhuma noticia para exibir.", pai_janela)
        return

    fotos = opcoes_fotos or OpcoesFotosNoticias.a_partir_modo("nenhum")

    for noticia in noticias:
        titulo = noticia.titulo
        resumo = noticia.resumo
        if traducoes and noticia.id in traducoes:
            titulo_pt, resumo_pt = traducoes[noticia.id]
            titulo = titulo_pt or titulo
            resumo = resumo_pt or resumo
        _criar_card(container, noticia, pai_janela, titulo, resumo, fotos)


def _criar_card(
    container: ctk.CTkScrollableFrame,
    noticia: NoticiaMercado,
    pai_janela: ctk.CTk | ctk.CTkToplevel | None,
    titulo_exibicao: str | None = None,
    resumo_exibicao: str | None = None,
    opcoes_fotos: OpcoesFotosNoticias | None = None,
) -> None:
    titulo = titulo_exibicao if titulo_exibicao is not None else noticia.titulo
    resumo = resumo_exibicao if resumo_exibicao is not None else noticia.resumo
    fotos = opcoes_fotos or OpcoesFotosNoticias.a_partir_modo("nenhum")

    card = ctk.CTkFrame(container, fg_color=CORES["superficie"], corner_radius=10)
    card.pack(fill="x", padx=4, pady=6)

    corpo = ctk.CTkFrame(card, fg_color="transparent")
    corpo.pack(fill="x", padx=12, pady=(10, 12))

    coluna_texto = ctk.CTkFrame(corpo, fg_color="transparent")
    coluna_texto.pack(side="left", fill="both", expand=True)

    if fotos.exibir and noticia.url_imagem:
        imagem = obter_imagem_noticia(
            noticia.url_imagem,
            fotos.largura,
            fotos.altura,
        )
        if imagem is not None:
            ctk.CTkLabel(corpo, text="", image=imagem).pack(
                side="left", padx=(0, 12), anchor="n"
            )

    linha_topo = ctk.CTkFrame(coluna_texto, fg_color="transparent")
    linha_topo.pack(fill="x")

    ctk.CTkLabel(
        linha_topo,
        text=titulo,
        font=ctk.CTkFont(size=_FONTE_TITULO, weight="bold"),
        text_color=CORES["texto"],
        anchor="w",
        justify="left",
        wraplength=_WRAP_TITULO,
    ).pack(side="left", fill="x", expand=True)

    if noticia.url:
        ctk.CTkButton(
            linha_topo,
            text="Abrir link",
            width=110,
            height=32,
            font=ctk.CTkFont(size=13),
            command=lambda u=noticia.url: abrir_link_noticia(u, pai_janela),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="right", padx=(8, 0))

    partes_meta = []
    if noticia.referencia:
        partes_meta.append(noticia.referencia)
    partes_meta.append(noticia.data_exibicao)
    partes_meta.append(noticia.fonte)
    partes_meta.append(noticia.regiao)
    meta = "  |  ".join(partes_meta)

    ctk.CTkLabel(
        coluna_texto,
        text=meta,
        font=ctk.CTkFont(size=_FONTE_META),
        text_color=CORES["textoSecundario"],
        anchor="w",
    ).pack(anchor="w", pady=(4, 6))

    if resumo:
        ctk.CTkLabel(
            coluna_texto,
            text=resumo,
            font=ctk.CTkFont(size=_FONTE_RESUMO),
            text_color=CORES["texto"],
            anchor="w",
            justify="left",
            wraplength=_WRAP_RESUMO,
        ).pack(anchor="w")


def abrir_link_noticia(
    url: str,
    pai_janela: ctk.CTk | ctk.CTkToplevel | None = None,
) -> None:
    if not url:
        messagebox.showinfo("Noticias", "Link indisponivel para esta noticia.", parent=pai_janela)
        return
    try:
        webbrowser.open(url)
    except OSError:
        messagebox.showwarning(
            "Noticias",
            "Nao foi possivel abrir o navegador. Copie o link manualmente se necessario.",
            parent=pai_janela,
        )
