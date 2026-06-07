"""Janela com principais noticias do mercado financeiro."""
from __future__ import annotations


import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.noticia_mercado import NoticiaMercado
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.View.janela_pesquisa_noticias import JanelaPesquisaNoticias
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
from src.View.tema import CORES

_FILTROS = ("Todas", "Brasil", "EUA")


class JanelaNoticiasMercado(ctk.CTkToplevel):
    """Lista noticias agregadas de referencias Brasil e EUA."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorMercado,
        modo_cripto: bool = False,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._modo_cripto = modo_cripto
        self._noticias: list[NoticiaMercado] = []
        self._filtro_atual = "Todas"
        self._janela_pesquisa: JanelaPesquisaNoticias | None = None
        self._idioma: ControladorExibicaoNoticiasIdioma | None = None
        self._config_painel = ConfigPainelIni()

        self.title(
            "Noticias de criptomoedas" if modo_cripto else "Noticias do mercado"
        )
        self.configure(fg_color=CORES["fundo"])
        self.minsize(880, 600)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._carregar_noticias)

    def _ao_fechar(self) -> None:
        if self._janela_pesquisa is not None:
            try:
                if self._janela_pesquisa.winfo_exists():
                    self._janela_pesquisa.destroy()
            except Exception:
                pass
        self.destroy()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Noticias do mercado",
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

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Escolha o servidor de noticias (Brasil, EUA, Europa, cripto, etc.). "
                "A preferencia e salva no painel.ini. Use a lista ao lado para "
                "ver no idioma original ou traduzido para portugues."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))

        self._label_status = ctk.CTkLabel(
            barra,
            text="Carregando noticias...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Atualizar",
            command=self._carregar_noticias,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=110,
        ).pack(side="right")

        ctk.CTkButton(
            barra,
            text="Pesquisar",
            command=self._abrir_pesquisa_noticias,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=110,
        ).pack(side="right", padx=(0, 8))

        self._lista = ctk.CTkScrollableFrame(self, fg_color=CORES["fundo"], label_text="Manchetes")
        self._lista.pack(fill="both", expand=True, padx=16, pady=(8, 8))

        self._idioma = ControladorExibicaoNoticiasIdioma(
            self._controlador,
            self._lista,
            self._label_status,
            self,
            self._noticias_filtradas,
            self._config_painel,
        )
        criar_listbox_idioma(barra, self._idioma.ao_mudar_idioma)
        criar_combo_fotos_noticias(
            barra,
            self._config_painel,
            lambda: self._idioma.reexibir_apos_atualizar_lista() if self._idioma else None,
        )
        criar_combo_provedor_noticias(
            barra,
            self._config_painel,
            self._ao_mudar_provedor_noticias,
            modo_cripto=self._modo_cripto,
        )

        ctk.CTkLabel(barra, text="Filtrar").pack(side="right", padx=(12, 6))
        self._combo_filtro = ctk.CTkComboBox(
            barra,
            values=list(_FILTROS),
            width=120,
            command=self._ao_mudar_filtro,
        )
        self._combo_filtro.set("Todas")
        self._combo_filtro.pack(side="right")

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="right")

    def _abrir_pesquisa_noticias(self) -> None:
        if self._janela_pesquisa is not None:
            try:
                if self._janela_pesquisa.winfo_exists():
                    self._janela_pesquisa.focus_force()
                    self._janela_pesquisa.lift()
                    return
            except Exception:
                pass

        self._janela_pesquisa = JanelaPesquisaNoticias(
            self, self._controlador, modo_cripto=self._modo_cripto
        )

    def _ao_mudar_filtro(self, valor: str) -> None:
        self._filtro_atual = valor
        self._renderizar_lista()

    def _ao_mudar_provedor_noticias(self, _chave: str) -> None:
        self._label_provedor.configure(
            text=descricao_provedor_atual(self._config_painel, self._modo_cripto)
        )
        self._carregar_noticias()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _carregar_noticias(self) -> None:
        self._label_status.configure(
            text="Buscando noticias...",
            text_color=CORES["textoSecundario"],
        )
        exibir_mensagem_lista(self._lista, "Aguarde, carregando...", self)

        def buscar():
            return self._controlador.obter_noticias_mercado()

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
            self._renderizar_lista()
            if self._idioma and self._idioma.modo_idioma == IDIOMA_ORIGINAL:
                self._label_status.configure(
                    text=f"{len(itens)} noticia(s) carregada(s).",
                    text_color=CORES["sucesso"],
                )

        self._executar_em_thread(buscar, ao_concluir)

    def _noticias_filtradas(self) -> list[NoticiaMercado]:
        if self._filtro_atual == "Brasil":
            return [n for n in self._noticias if n.regiao == "Brasil"]
        if self._filtro_atual == "EUA":
            return [n for n in self._noticias if n.regiao == "EUA"]
        return list(self._noticias)

    def _renderizar_lista(self) -> None:
        itens = self._noticias_filtradas()
        if not itens:
            exibir_mensagem_lista(self._lista, "Nenhuma noticia para o filtro selecionado.", self)
            return
        if self._idioma:
            self._idioma.reexibir_apos_atualizar_lista()
