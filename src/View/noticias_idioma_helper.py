"""Listbox e fluxo para exibir noticias no idioma original ou traduzidas."""
from __future__ import annotations

import threading
import tkinter as tk
from typing import Callable

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.noticia_mercado import NoticiaMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.imagem_noticia_helper import precarregar_imagens_noticias
from src.View.noticias_lista_helper import exibir_mensagem_lista, preencher_lista_noticias
from src.View.tema import CORES

IDIOMA_ORIGINAL = "Original"
IDIOMA_PORTUGUES = "Portugues (traduzido)"

# Exportado para checagem de modo na janela principal.
__all__ = [
    "IDIOMA_ORIGINAL",
    "IDIOMA_PORTUGUES",
    "ControladorExibicaoNoticiasIdioma",
    "criar_listbox_idioma",
]


def criar_listbox_idioma(
    pai: ctk.CTkFrame,
    ao_selecionar: Callable[[str], None],
) -> tk.Listbox:
    """Listbox com duas opcoes: original ou traduzido para portugues."""
    bloco = ctk.CTkFrame(pai, fg_color="transparent")
    bloco.pack(side="right", padx=(12, 0))

    ctk.CTkLabel(
        bloco,
        text="Exibir noticias",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w")

    listbox = tk.Listbox(
        bloco,
        height=2,
        width=24,
        exportselection=False,
        activestyle="none",
        selectmode=tk.SINGLE,
        bg=CORES["superficie"],
        fg=CORES["texto"],
        selectbackground=CORES["primaria"],
        selectforeground=CORES["textoInverso"],
        highlightthickness=1,
        highlightbackground=CORES["borda"],
        font=("Segoe UI", 10),
    )
    listbox.pack(anchor="w", pady=(2, 0))
    listbox.insert(tk.END, IDIOMA_ORIGINAL)
    listbox.insert(tk.END, IDIOMA_PORTUGUES)
    listbox.selection_set(0)

    def ao_mudar_selecao(_evento=None) -> None:
        selecao = listbox.curselection()
        if not selecao:
            return
        ao_selecionar(listbox.get(selecao[0]))

    listbox.bind("<<ListboxSelect>>", ao_mudar_selecao)
    return listbox


class ControladorExibicaoNoticiasIdioma:
    """Coordena listbox de idioma, traducao em thread e atualizacao da lista."""

    def __init__(
        self,
        controlador: ControladorMercado,
        container_lista: ctk.CTkScrollableFrame,
        label_status: ctk.CTkLabel,
        janela: ctk.CTk | ctk.CTkToplevel,
        obter_noticias: Callable[[], list[NoticiaMercado]],
        config_painel: ConfigPainelIni,
    ) -> None:
        self._controlador = controlador
        self._container = container_lista
        self._label_status = label_status
        self._janela = janela
        self._obter_noticias = obter_noticias
        self._config = config_painel
        self._modo = IDIOMA_ORIGINAL
        self._traducoes: dict[str, tuple[str, str]] = {}
        self._traduzindo = False

    @property
    def modo_idioma(self) -> str:
        return self._modo

    def ao_mudar_idioma(self, opcao: str) -> None:
        if opcao == self._modo or self._traduzindo:
            return
        self._modo = opcao
        if opcao == IDIOMA_PORTUGUES:
            self._traduzir_e_exibir()
        else:
            self._exibir_original()

    def _exibir_original(self) -> None:
        noticias = self._obter_noticias()
        if not noticias:
            return
        self._montar_lista_com_fotos(noticias, None)

    def _montar_lista_com_fotos(
        self,
        noticias: list[NoticiaMercado],
        traducoes: dict[str, tuple[str, str]] | None,
    ) -> None:
        opcoes = self._config.carregar_opcoes_fotos_noticias()

        def trabalho_precarga() -> None:
            if opcoes.exibir:
                urls = [n.url_imagem for n in noticias if n.url_imagem]
                precarregar_imagens_noticias(urls, opcoes.largura, opcoes.altura)

        def na_interface() -> None:
            preencher_lista_noticias(
                self._container,
                noticias,
                self._janela,
                traducoes,
                opcoes,
            )

        if opcoes.exibir and any(n.url_imagem for n in noticias):
            exibir_mensagem_lista(self._container, "Carregando fotos...", self._janela)

            def thread_fotos() -> None:
                trabalho_precarga()
                self._janela.after(0, na_interface)

            threading.Thread(target=thread_fotos, daemon=True).start()
        else:
            na_interface()

    def _traduzir_e_exibir(self) -> None:
        noticias = self._obter_noticias()
        if not noticias:
            exibir_mensagem_lista(
                self._container,
                "Carregue ou pesquise noticias antes de traduzir.",
                self._janela,
            )
            return

        self._traduzindo = True
        self._label_status.configure(
            text="Traduzindo noticias para portugues...",
            text_color=CORES["textoSecundario"],
        )
        exibir_mensagem_lista(self._container, "Aguarde, traduzindo...", self._janela)

        def trabalho():
            return self._controlador.traduzir_noticias_para_portugues(noticias)

        def ao_concluir(resultado, erro):
            self._traduzindo = False
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                exibir_mensagem_lista(self._container, erro, self._janela)
                return
            mapa, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                exibir_mensagem_lista(self._container, msg_erro, self._janela)
                return
            self._traducoes = mapa
            self._montar_lista_com_fotos(noticias, mapa)
            self._label_status.configure(
                text=f"{len(noticias)} noticia(s) em portugues (traducao automatica).",
                text_color=CORES["sucesso"],
            )

        def thread_trabalho() -> None:
            try:
                resultado = trabalho()
                self._janela.after(0, lambda: ao_concluir(resultado, None))
            except Exception as exc:
                self._janela.after(0, lambda: ao_concluir(None, str(exc)))

        threading.Thread(target=thread_trabalho, daemon=True).start()

    def reexibir_apos_atualizar_lista(self) -> None:
        """Chamar apos carregar ou filtrar noticias, respeitando o modo atual."""
        if self._modo == IDIOMA_PORTUGUES:
            self._traduzir_e_exibir()
        else:
            self._exibir_original()
