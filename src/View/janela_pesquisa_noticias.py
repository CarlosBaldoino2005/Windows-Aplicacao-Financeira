"""Janela para pesquisar noticias por acao, empresa ou assunto."""
from __future__ import annotations

from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from src.Model.noticia_mercado import NoticiaMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.View.noticias_fotos_helper import criar_combo_fotos_noticias
from src.View.noticias_provedor_helper import (
    criar_combo_provedor_noticias,
    descricao_provedor_atual,
)
from src.View.noticias_idioma_helper import (
    IDIOMA_ORIGINAL,
    ControladorExibicaoNoticiasIdioma,
    criar_listbox_idioma,
)
from src.View.noticias_lista_helper import exibir_mensagem_lista
from src.View.placeholders_ui import (
    PLACEHOLDER_NOTICIAS_BUSCA_ACAO,
    PLACEHOLDER_NOTICIAS_BUSCA_CRIPTO,
)
from src.View.tema import CORES


class JanelaPesquisaNoticias(ctk.CTkToplevel):
    """Busca noticias relacionadas a um termo digitado pelo usuario."""

    def __init__(
        self,
        pai: ctk.CTkToplevel,
        controlador: Any,
        modo_cripto: bool = False,
        termo_inicial: str | None = None,
        titulo_personalizado: str | None = None,
        buscar_ao_abrir: bool = False,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._modo_cripto = modo_cripto
        self._termo_inicial = (termo_inicial or "").strip()
        self._buscar_ao_abrir = buscar_ao_abrir and len(self._termo_inicial) >= 2
        self._noticias: list[NoticiaMercado] = []
        self._termo_atual = ""
        self._idioma: ControladorExibicaoNoticiasIdioma | None = None
        self._config_painel = ConfigPainelIni()

        if titulo_personalizado:
            titulo_janela = titulo_personalizado
        elif self._termo_inicial:
            titulo_janela = f"Noticias — {self._termo_inicial}"
        else:
            titulo_janela = (
                "Pesquisar noticias de cripto" if modo_cripto else "Pesquisar noticias"
            )
        self.title(titulo_janela)
        self.configure(fg_color=CORES["fundo"])
        self.minsize(880, 600)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(pai)
        self.focus_force()
        if self._buscar_ao_abrir:
            self.after(200, lambda: self._executar_pesquisa(self._termo_inicial))

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        titulo_cabecalho = (
            f"Noticias — {self._termo_inicial}"
            if self._termo_inicial
            else "Pesquisar noticias"
        )
        ctk.CTkLabel(
            cabecalho,
            text=titulo_cabecalho,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self._label_provedor = ctk.CTkLabel(
            cabecalho,
            text=descricao_provedor_atual(self._config_painel, self._modo_cripto),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        )
        self._label_provedor.pack(anchor="w", padx=16, pady=(0, 4))

        texto_ajuda = (
            f"Noticias relacionadas a {self._termo_inicial}. "
            "Voce pode alterar o termo e pesquisar de novo. "
            "Use a lista para ver no idioma original ou traduzido para portugues."
            if self._termo_inicial
            else (
                "Digite codigo (PETR4, AAPL), nome da empresa (Vale, Apple) "
                "ou assunto. A busca usa o servidor escolhido (salvo no painel.ini)."
            )
        )
        ctk.CTkLabel(
            cabecalho,
            text=texto_ajuda,
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
            placeholder_text=(
                PLACEHOLDER_NOTICIAS_BUSCA_CRIPTO
                if self._modo_cripto
                else PLACEHOLDER_NOTICIAS_BUSCA_ACAO
            ),
        )
        self._entrada_busca.pack(side="left", padx=(0, 8))
        if self._termo_inicial:
            self._entrada_busca.insert(0, self._termo_inicial)
        self._entrada_busca.bind("<Return>", lambda _e: self._executar_pesquisa())

        ctk.CTkButton(
            linha_busca,
            text="Pesquisar",
            command=lambda: self._executar_pesquisa(),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="left")

        barra_status = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_status.pack(fill="x", padx=16, pady=(0, 12))

        texto_status_inicial = (
            f"Buscando noticias sobre \"{self._termo_inicial}\"..."
            if self._buscar_ao_abrir
            else "Informe o termo e clique em Pesquisar."
        )
        self._label_status = ctk.CTkLabel(
            barra_status,
            text=texto_status_inicial,
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
        criar_combo_provedor_noticias(
            barra_status,
            self._config_painel,
            self._ao_mudar_provedor_noticias,
            modo_cripto=self._modo_cripto,
        )

        if not self._buscar_ao_abrir:
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
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="right")

    def _ao_mudar_provedor_noticias(self, _chave: str) -> None:
        self._label_provedor.configure(
            text=descricao_provedor_atual(self._config_painel, self._modo_cripto)
        )
        if self._termo_atual and len(self._termo_atual) >= 2:
            self._executar_pesquisa(self._termo_atual)
        elif self._entrada_busca.get().strip():
            self._executar_pesquisa()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _executar_pesquisa(self, termo_opcional: str | None = None) -> None:
        termo = (termo_opcional or self._entrada_busca.get()).strip()
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
