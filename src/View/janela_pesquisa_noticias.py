"""Janela para pesquisar noticias por acao, empresa ou assunto."""
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.noticia_mercado import NoticiaMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_maximizada
from src.View.noticias_fotos_helper import criar_combo_fotos_noticias
from src.View.noticias_idioma_helper import (
    IDIOMA_ORIGINAL,
    ControladorExibicaoNoticiasIdioma,
    criar_listbox_idioma,
)
from src.View.noticias_lista_helper import exibir_mensagem_lista
from src.View.tema import CORES


class JanelaPesquisaNoticias(ctk.CTkToplevel):
    """Busca noticias relacionadas a um termo digitado pelo usuario."""

    def __init__(self, pai: ctk.CTkToplevel, controlador: ControladorMercado) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._noticias: list[NoticiaMercado] = []
        self._termo_atual = ""
        self._idioma: ControladorExibicaoNoticiasIdioma | None = None
        self._config_painel = ConfigPainelIni()

        self.title("Pesquisar noticias")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(880, 600)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(pai)
        self.focus_force()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Pesquisar noticias",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Digite codigo (PETR4, AAPL), nome da empresa (Vale, Apple) "
                "ou assunto. Use a lista para ver original ou traduzido para portugues."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        linha_busca = ctk.CTkFrame(cabecalho, fg_color="transparent")
        linha_busca.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(linha_busca, text="Buscar").pack(side="left", padx=(0, 8))
        self._entrada_busca = ctk.CTkEntry(
            linha_busca,
            width=360,
            placeholder_text="Ex.: PETR4, Petrobras, inflacao, Fed, ouro...",
        )
        self._entrada_busca.pack(side="left", padx=(0, 8))
        self._entrada_busca.bind("<Return>", lambda _e: self._executar_pesquisa())

        ctk.CTkButton(
            linha_busca,
            text="Pesquisar",
            command=self._executar_pesquisa,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="left")

        barra_status = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_status.pack(fill="x", padx=16, pady=(0, 12))

        self._label_status = ctk.CTkLabel(
            barra_status,
            text="Informe o termo e clique em Pesquisar.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=500,
            justify="left",
        )
        self._label_status.pack(side="left")

        self._lista = ctk.CTkScrollableFrame(
            self, fg_color=CORES["fundo"], label_text="Resultados"
        )
        self._lista.pack(fill="both", expand=True, padx=16, pady=(8, 8))

        self._idioma = ControladorExibicaoNoticiasIdioma(
            self._controlador,
            self._lista,
            self._label_status,
            self,
            lambda: self._noticias,
            self._config_painel,
        )
        criar_listbox_idioma(barra_status, self._idioma.ao_mudar_idioma)
        criar_combo_fotos_noticias(
            barra_status,
            self._config_painel,
            lambda: self._idioma.reexibir_apos_atualizar_lista() if self._idioma else None,
        )

        exibir_mensagem_lista(
            self._lista,
            "Os resultados aparecerao aqui apos a pesquisa.",
            self,
        )

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self.destroy,
            fg_color=CORES["secundaria"],
            width=120,
        ).pack(side="right")

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        def trabalho() -> None:
            try:
                resultado = funcao()
                self.after(0, lambda: ao_concluir(resultado, None))
            except Exception as exc:
                self.after(0, lambda: ao_concluir(None, str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _executar_pesquisa(self) -> None:
        termo = self._entrada_busca.get().strip()
        if len(termo) < 2:
            messagebox.showwarning(
                "Pesquisar",
                "Digite pelo menos 2 caracteres.",
                parent=self,
            )
            return

        self._termo_atual = termo
        self._label_status.configure(
            text=f"Buscando noticias sobre \"{termo}\"...",
            text_color=CORES["textoSecundario"],
        )
        exibir_mensagem_lista(self._lista, "Aguarde, pesquisando...", self)

        def buscar():
            return self._controlador.pesquisar_noticias(termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                exibir_mensagem_lista(self._lista, erro, self)
                return
            itens, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                exibir_mensagem_lista(self._lista, msg_erro, self)
                return
            self._noticias = itens
            if self._idioma:
                self._idioma.reexibir_apos_atualizar_lista()
            if self._idioma and self._idioma.modo_idioma == IDIOMA_ORIGINAL:
                self._label_status.configure(
                    text=f"{len(itens)} noticia(s) sobre \"{termo}\".",
                    text_color=CORES["sucesso"],
                )

        self._executar_em_thread(buscar, ao_concluir)
