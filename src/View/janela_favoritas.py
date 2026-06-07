"""Janela de acoes favoritas com grid de cotacoes e persistencia local."""
from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Literal

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Service.favoritos_fiis_servico import FavoritosFiisServico
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.atualizacao_automatica_helper import GerenciadorAtualizacaoAutomatica
from src.Tool.janela_helper import (
    executar_em_thread,
    configurar_janela_maximizada,
    janela_ui_ainda_ativa,
)
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto
from src.View.placeholders_ui import (
    PLACEHOLDER_BUSCA_ACAO,
    PLACEHOLDER_BUSCA_CRIPTO,
    PLACEHOLDER_CODIGO_ACAO,
    PLACEHOLDER_CODIGO_CRIPTO,
)
from src.View.grid_fonte_helper import criar_combo_fonte_grid
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.grid_interacao_treeview_helper import liberar_interacao_treeview
from src.View.tabela_mercado_helper import (
    criar_card_tabela,
    definir_rotulo_coluna_simbolo,
    obter_simbolo_duplo_clique_treeview,
    preencher_tabela,
    reaplicar_fonte_em_tabelas,
    treeview_ainda_ativa,
)
from src.View.tema import CORES

TipoPainelFavoritos = Literal["acoes", "cripto", "fiis", "dividendos"]

_TITULOS_PAINEL: dict[TipoPainelFavoritos, str] = {
    "acoes": "Acoes favoritas",
    "cripto": "Criptos favoritas",
    "fiis": "FIIs favoritos",
    "dividendos": "Empresas favoritas (dividendos)",
}

_DESCRICOES_PAINEL: dict[TipoPainelFavoritos, str] = {
    "acoes": "Adicione acoes que deseja acompanhar. A lista fica salva neste computador.",
    "cripto": "Adicione criptomoedas que deseja acompanhar. A lista fica salva neste computador.",
    "fiis": (
        "Adicione fundos imobiliarios (FIIs) que deseja acompanhar. "
        "A lista fica salva em dados/favoritos_fiis.json neste computador."
    ),
    "dividendos": (
        "Adicione empresas pagadoras de dividendos que deseja acompanhar. "
        "FIIs ficam no painel Fundos imobiliarios (lista separada)."
    ),
}

_TITULOS_GRID: dict[TipoPainelFavoritos, str] = {
    "acoes": "Suas acoes favoritas (duplo clique abre o grafico)",
    "cripto": "Suas criptos favoritas (duplo clique abre o grafico)",
    "fiis": "Seus FIIs favoritos (duplo clique abre o grafico)",
    "dividendos": "Suas empresas favoritas (duplo clique abre o grafico)",
}


class JanelaFavoritas(ctk.CTkToplevel):
    """Lista favoritas salvas em disco com cotacoes atualizadas."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorMercado,
        modo_cripto: bool = False,
        tipo_painel: TipoPainelFavoritos | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        if tipo_painel is not None:
            self._tipo_painel = tipo_painel
        elif modo_cripto:
            self._tipo_painel = "cripto"
        else:
            self._tipo_painel = "acoes"
        self._modo_cripto = self._tipo_painel == "cripto"
        self._config_painel = ConfigPainelIni()
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._tabela: ttk.Treeview | None = None
        self._grid_buscando = False
        self._grid_versao = 0

        self.title(_TITULOS_PAINEL[self._tipo_painel])
        self.configure(fg_color=CORES["fundo"])
        self.minsize(820, 560)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(250, lambda: self._atualizar_grid(forcar=False))
        self._atualizador_auto = GerenciadorAtualizacaoAutomatica(
            self,
            self._config_painel,
            lambda: self._atualizar_grid(forcar=False),
        )
        self._atualizador_auto.iniciar()

    def _ao_fechar(self) -> None:
        self._atualizador_auto.parar()
        self._grid_versao += 1
        self._grid_buscando = False
        liberar_interacao_treeview(self._tabela)
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        self._tabela = None
        self.destroy()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text=_TITULOS_PAINEL[self._tipo_painel],
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=_DESCRICOES_PAINEL[self._tipo_painel],
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=860,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        linha_add = ctk.CTkFrame(cabecalho, fg_color="transparent")
        linha_add.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(linha_add, text="Codigo ou nome").pack(side="left", padx=(0, 8))
        self._entrada_busca = ctk.CTkEntry(
            linha_add,
            width=260,
            placeholder_text=(
                PLACEHOLDER_BUSCA_CRIPTO if self._modo_cripto else PLACEHOLDER_BUSCA_ACAO
            ),
        )
        self._entrada_busca.pack(side="left", padx=(0, 8))
        self._entrada_busca.bind("<Return>", lambda _e: self._pesquisar())

        ctk.CTkButton(
            linha_add,
            text="Buscar",
            command=self._pesquisar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(linha_add, text="ou codigo").pack(side="left", padx=(8, 8))
        self._entrada_codigo = ctk.CTkEntry(
            linha_add,
            width=100,
            placeholder_text=(
                PLACEHOLDER_CODIGO_CRIPTO if self._modo_cripto else PLACEHOLDER_CODIGO_ACAO
            ),
        )
        self._entrada_codigo.pack(side="left", padx=(0, 8))
        self._entrada_codigo.bind("<Return>", lambda _e: self._adicionar_codigo())

        ctk.CTkButton(
            linha_add,
            text="Adicionar",
            command=self._adicionar_codigo,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left")

        self._frame_resultados = ctk.CTkScrollableFrame(
            cabecalho, height=90, fg_color=CORES["fundo"], label_text="Resultados da busca"
        )
        self._frame_resultados.pack(fill="x", padx=16, pady=(4, 8))

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))

        self._label_status = ctk.CTkLabel(
            barra, text="", font=ctk.CTkFont(size=12), text_color=CORES["textoSecundario"]
        )
        self._label_status.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Remover selecionadas",
            command=self._remover_selecionadas,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=150,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            barra,
            text="Atualizar cotacoes",
            command=lambda: self._atualizar_grid(forcar=True),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="right")

        criar_combo_fonte_grid(barra, self._config_painel, self._ao_mudar_fonte_grid)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._tabela = criar_card_tabela(
            container,
            _TITULOS_GRID[self._tipo_painel],
            altura=14,
            ao_duplo_clique=self._ao_duplo_clique,
            expandir=True,
        )
        if self._tipo_painel == "fiis":
            definir_rotulo_coluna_simbolo(self._tabela, "FII")

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

    def _limpar_resultados(self) -> None:
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _pesquisar(self) -> None:
        termo = self._entrada_busca.get().strip()
        if not termo:
            aviso = (
                "Digite o nome ou codigo da criptomoeda (ex.: Bitcoin ou SOL)."
                if self._modo_cripto
                else "Digite o nome ou codigo da acao."
            )
            messagebox.showwarning("Buscar", aviso, parent=self)
            return

        status = (
            "Buscando criptomoedas..."
            if self._modo_cripto
            else "Buscando acoes..."
        )
        self._label_status.configure(text=status)

        def buscar():
            return self._controlador.pesquisar_acoes(termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                self._limpar_resultados()
                return
            itens, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                self._limpar_resultados()
                return
            self._exibir_resultados(itens)
            self._label_status.configure(
                text=f"{len(itens)} resultado(s). Clique em Adicionar na linha desejada.",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _exibir_resultados(self, itens) -> None:
        self._limpar_resultados()
        if not itens:
            ctk.CTkLabel(
                self._frame_resultados,
                text="Nenhum resultado.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for item in itens:
            linha = ctk.CTkFrame(self._frame_resultados, fg_color=CORES["superficie"], corner_radius=8)
            linha.pack(fill="x", padx=4, pady=3)

            codigo = self._codigo_exibicao(item.simbolo)
            texto = f"{codigo}  —  {item.nome}  ({item.bolsa})"
            ctk.CTkLabel(
                linha,
                text=texto,
                anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=CORES["texto"],
            ).pack(side="left", fill="x", expand=True, padx=8, pady=6)

            ctk.CTkButton(
                linha,
                text="Adicionar",
                width=90,
                command=lambda s=item.simbolo: self._adicionar_favorito(s),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            ).pack(side="right", padx=8, pady=4)

    def _normalizar_entrada(self, termo: str):
        if self._modo_cripto:
            return normalizar_simbolo_cripto(termo)
        return normalizar_simbolo(termo)

    def _codigo_exibicao(self, simbolo: str) -> str:
        if self._modo_cripto:
            return simbolo.replace("-USD", "")
        return simbolo.replace(".SA", "")

    def _adicionar_codigo(self) -> None:
        termo = self._entrada_codigo.get().strip() or self._entrada_busca.get().strip()
        if not termo:
            aviso = (
                "Informe o codigo da criptomoeda (ex.: BTC ou Bitcoin)."
                if self._modo_cripto
                else "Informe o codigo da acao."
            )
            messagebox.showwarning("Adicionar", aviso, parent=self)
            return
        simbolo, erro = self._normalizar_entrada(termo)
        if erro:
            messagebox.showwarning("Adicionar", erro, parent=self)
            return
        self._adicionar_favorito(simbolo)

    def _adicionar_favorito(self, simbolo: str) -> None:
        ok, msg = self._controlador.adicionar_favorito(simbolo)
        if not ok:
            messagebox.showwarning("Favoritos", msg or "Nao foi possivel adicionar.", parent=self)
            return

        codigo = self._codigo_exibicao(simbolo)
        self._entrada_codigo.delete(0, "end")
        self._label_status.configure(
            text=f"{codigo} adicionada aos favoritos.",
            text_color=CORES["sucesso"],
        )
        self._atualizar_grid()

    def _remover_selecionadas(self) -> None:
        if not self._tabela:
            return
        selecao = self._tabela.selection()
        if not selecao:
            aviso = (
                "Selecione uma ou mais criptomoedas na lista."
                if self._modo_cripto
                else "Selecione uma ou mais acoes na lista."
            )
            messagebox.showinfo("Remover", aviso, parent=self)
            return

        removidas: list[str] = []
        erros: list[str] = []
        for simbolo in selecao:
            ok, msg = self._controlador.remover_favorito(simbolo)
            if ok:
                removidas.append(self._codigo_exibicao(simbolo))
            elif msg:
                erros.append(msg)

        if erros and not removidas:
            messagebox.showwarning("Favoritos", erros[0], parent=self)
            return

        if removidas:
            if len(removidas) == 1:
                texto = f"{removidas[0]} removida dos favoritos."
            else:
                texto = f"{len(removidas)} favoritas removidas."
            self._label_status.configure(text=texto, text_color=CORES["sucesso"])

        if erros:
            messagebox.showwarning(
                "Favoritos",
                "Algumas nao puderam ser removidas:\n" + "\n".join(erros[:3]),
                parent=self,
            )

        self._atualizar_grid()

    def _ao_mudar_fonte_grid(self) -> None:
        if self._tabela is not None:
            reaplicar_fonte_em_tabelas([self._tabela])

    def _mensagem_lista_vazia(self) -> str:
        if self._tipo_painel == "cripto":
            return "Nenhuma cripto favorita. Use Buscar ou Adicionar acima."
        if self._tipo_painel == "fiis":
            return "Nenhum FII favorito. Use Buscar ou Adicionar acima."
        if self._tipo_painel == "dividendos":
            qtd_fiis = len(FavoritosFiisServico().listar())
            if qtd_fiis > 0:
                return (
                    "Nenhuma empresa favorita neste painel. "
                    f"Voce tem {qtd_fiis} FII(s) favorito(s) no painel "
                    "Fundos imobiliarios — abra Favoritos por la."
                )
            return "Nenhuma empresa favorita. Use Buscar ou Adicionar acima."
        return "Nenhuma acao favorita. Use Buscar ou Adicionar acima."

    def _atualizar_grid(self, forcar: bool = False) -> None:
        if not janela_ui_ainda_ativa(self) or not treeview_ainda_ativa(self._tabela):
            return

        if self._grid_buscando and not forcar:
            return

        self._grid_versao += 1
        versao = self._grid_versao

        simbolos = self._controlador.listar_simbolos_favoritos()
        if not simbolos:
            self._grid_buscando = False
            preencher_tabela(self._tabela, [])
            if janela_ui_ainda_ativa(self):
                self._label_status.configure(
                    text=self._mensagem_lista_vazia(),
                    text_color=CORES["textoSecundario"],
                )
            return

        self._grid_buscando = True
        if janela_ui_ainda_ativa(self):
            self._label_status.configure(
                text="Atualizando cotacoes...",
                text_color=CORES["textoSecundario"],
            )

        def buscar():
            return self._controlador.obter_cotacoes_favoritas()

        def ao_concluir(resultado, erro):
            if versao != self._grid_versao:
                return
            self._grid_buscando = False
            if not janela_ui_ainda_ativa(self) or not treeview_ainda_ativa(self._tabela):
                return
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                return
            cotacoes, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                return
            preencher_tabela(self._tabela, cotacoes)
            if self._tipo_painel == "fiis":
                definir_rotulo_coluna_simbolo(self._tabela, "FII")
            hora = datetime.now().strftime("%H:%M:%S")
            self._label_status.configure(
                text=f"{len(cotacoes)} favorita(s) — atualizado as {hora}",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _ao_duplo_clique(self, evento) -> None:
        simbolo = obter_simbolo_duplo_clique_treeview(evento.widget, evento)
        if not simbolo:
            return
        self._abrir_grafico(simbolo)

    def _abrir_grafico(self, simbolo: str) -> None:
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass

        self._janela_grafico = JanelaGraficoAcao(self, self._controlador, simbolo)
