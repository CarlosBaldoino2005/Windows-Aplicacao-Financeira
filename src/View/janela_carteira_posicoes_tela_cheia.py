"""Janela maximizada com a grid de posicoes da carteira."""
from __future__ import annotations

from datetime import datetime
from tkinter import ttk

import customtkinter as ctk

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import LinhaCarteira, tipo_carteira_para_monitoramento
from src.Model.monitoramento import TipoAtivoMonitoramento
from src.Tool.atualizacao_automatica_helper import GerenciadorAtualizacaoAutomatica
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.controlador_ativo_helper import obter_controlador_por_tipo
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.resumo_carteira_helper import PainelResumoCarteira
from src.View.tabela_carteira_helper import (
    criar_grid_carteira,
    liberar_grid_carteira,
    obter_id_duplo_clique_carteira,
    preencher_grid_carteira,
)
from src.View.tema import CORES


class JanelaCarteiraPosicoesTelaCheia(ctk.CTkToplevel):
    """Grid de posicoes em tela cheia com a mesma atualizacao automatica da carteira."""

    def __init__(self, pai: ctk.CTkToplevel) -> None:
        super().__init__(pai)
        self._janela_pai = pai
        self._controlador = ControladorCarteira()
        self._config_painel = ConfigPainelIni()
        self._tabela: ttk.Treeview | None = None
        self._linhas_cache: dict[str, LinhaCarteira] = {}
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._atualizando = False
        self._versao_atualizacao = 0
        self._painel_resumo: PainelResumoCarteira | None = None

        self.title("Carteira — posicoes em tela cheia")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 600)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

        self._atualizador_auto = GerenciadorAtualizacaoAutomatica(
            self,
            self._config_painel,
            lambda: self._atualizar_lista(automatico=True),
            escopo="carteira",
        )
        self._atualizador_auto.iniciar()
        self._atualizar_indicador_automatico()
        self.after(200, lambda: self._atualizar_lista(forcar=True))

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Posicoes da carteira — tela cheia",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text="Duplo clique abre o grafico do ativo. Atualizacao automatica conforme configuracao da carteira.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._painel_resumo = PainelResumoCarteira(cabecalho)
        self._painel_resumo.montar().pack(fill="x", padx=16, pady=(0, 8))

        barra_status = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_status.pack(fill="x", padx=16, pady=(0, 8))

        self._label_status = ctk.CTkLabel(
            barra_status,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(side="left", anchor="w")

        self._label_auto = ctk.CTkLabel(
            barra_status,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        )
        self._label_auto.pack(side="right", anchor="e")

        barra_acoes = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_acoes.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(
            barra_acoes,
            text="Atualizar cotacoes",
            command=lambda: self._atualizar_lista(forcar=True),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=150,
        ).pack(side="left")

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._tabela = criar_grid_carteira(
            container,
            "Posicoes da carteira",
            altura=22,
            ao_duplo_clique=self._ao_duplo_clique,
        )

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

    def _atualizar_indicador_automatico(self) -> None:
        opcoes = self._atualizador_auto.obter_opcoes()
        if opcoes.habilitada:
            texto = f"Auto: a cada {opcoes.intervalo_segundos} s"
            cor = CORES["sucesso"]
        else:
            texto = "Auto: desligado"
            cor = CORES["textoSecundario"]
        self._label_auto.configure(text=texto, text_color=cor)

    def _atualizar_lista(self, *, forcar: bool = False, automatico: bool = False) -> None:
        if self._atualizando and not forcar:
            return
        if not janela_ui_ainda_ativa(self):
            return

        self._atualizando = True
        versao = self._versao_atualizacao
        if not automatico:
            self._label_status.configure(text="Atualizando cotacoes...", text_color=CORES["textoSecundario"])

        def tarefa():
            return self._controlador.obter_linhas_carteira()

        def ao_concluir(resultado, erro_thread):
            self._atualizando = False
            if not janela_ui_ainda_ativa(self) or versao != self._versao_atualizacao:
                return

            self._atualizar_indicador_automatico()

            if erro_thread:
                self._label_status.configure(text=erro_thread, text_color=CORES["erro"])
                return

            linhas, erro = resultado if resultado is not None else ([], None)
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                return

            self._linhas_cache = {linha.posicao.id: linha for linha in linhas}
            if self._tabela is not None:
                preencher_grid_carteira(self._tabela, linhas)
            if self._painel_resumo is not None:
                self._painel_resumo.atualizar(
                    linhas,
                    texto_rodape=f"{len(linhas)} posicao(oes) na carteira",
                )

            agora = datetime.now().strftime("%H:%M:%S")
            self._label_status.configure(
                text=f"{len(linhas)} posicao(oes) — atualizado as {agora}",
                text_color=CORES["textoSecundario"],
            )

        executar_em_thread(self, tarefa, ao_concluir)

    def _ao_duplo_clique(self, evento) -> None:
        if self._tabela is None:
            return
        item_id = obter_id_duplo_clique_carteira(self._tabela, evento)
        if not item_id:
            return
        linha = self._linhas_cache.get(item_id)
        if linha is None:
            return
        self._abrir_grafico(linha)

    def _abrir_grafico(self, linha: LinhaCarteira) -> None:
        tipo_mon: TipoAtivoMonitoramento = tipo_carteira_para_monitoramento(  # type: ignore[assignment]
            linha.posicao.tipo_ativo
        )
        controlador = obter_controlador_por_tipo(tipo_mon)

        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass

        self._janela_grafico = JanelaGraficoAcao(self, controlador, linha.posicao.simbolo)
        codigo = codigo_exibicao(linha.posicao.simbolo)
        self._janela_grafico.title(f"Grafico — {codigo}")

    def _ao_fechar(self) -> None:
        self._versao_atualizacao += 1
        self._atualizador_auto.parar()
        liberar_grid_carteira(self._tabela)
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        self.destroy()


def abrir_carteira_posicoes_tela_cheia(pai: ctk.CTkToplevel) -> JanelaCarteiraPosicoesTelaCheia:
    return JanelaCarteiraPosicoesTelaCheia(pai)
