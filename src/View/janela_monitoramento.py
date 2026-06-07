"""Tela central de monitoramento de precos com alertas visuais."""
from __future__ import annotations

from datetime import datetime

import customtkinter as ctk
from tkinter import ttk

from src.View import mensagem_helper as messagebox

from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Model.monitoramento import MonitoramentoItem, MonitoramentoLinha
from src.Tool.atualizacao_automatica_helper import GerenciadorAtualizacaoAutomatica
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.controlador_ativo_helper import obter_controlador_por_tipo
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.icone_engrenagem_helper import criar_botao_engrenagem
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.janela_adicionar_monitoramento import abrir_adicionar_monitoramento
from src.View.janela_config_atualizacao_monitoramento import abrir_config_atualizacao_monitoramento
from src.View.janela_editar_monitoramento import abrir_editar_monitoramento
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.tabela_monitoramento_helper import (
    criar_grid_monitoramento,
    liberar_grid_monitoramento,
    obter_id_duplo_clique_monitoramento,
    preencher_grid_monitoramento,
)
from src.View.tema import CORES


class JanelaMonitoramento(ctk.CTkToplevel):
    """Lista ativos monitorados com cores de alerta e atualizacao automatica."""

    def __init__(self, pai: ctk.CTk) -> None:
        super().__init__(pai)
        self._controlador = ControladorMonitoramento()
        self._config_painel = ConfigPainelIni()
        self._janela_adicionar = None
        self._janela_editar = None
        self._janela_config_auto = None
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._tabela: ttk.Treeview | None = None
        self._linhas_cache: dict[str, MonitoramentoLinha] = {}
        self._atualizando = False
        self._versao_atualizacao = 0
        self._pausado = self._config_painel.carregar_monitoramento_pausado()

        self.title("Monitoramento de precos")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(980, 620)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

        self._atualizador_auto = GerenciadorAtualizacaoAutomatica(
            self,
            self._config_painel,
            lambda: self._atualizar_lista(automatico=True),
            escopo="monitoramento",
        )
        if self._pausado:
            self._atualizador_auto.pausar()
        else:
            self._atualizador_auto.iniciar()
        self._atualizar_indicador_automatico()
        self._aplicar_visual_pausa()
        self.after(200, lambda: self._atualizar_lista(forcar=True))

    def _ao_fechar(self) -> None:
        self._versao_atualizacao += 1
        self._atualizador_auto.parar()
        liberar_grid_monitoramento(self._tabela)
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        self.destroy()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Monitoramento de precos",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Acompanhe acoes, criptomoedas, FIIs e pagadoras de dividendos. "
                "Linha vermelha = abaixo do valor baixo; verde = acima do valor alto; "
                "cinza claro/apagado = item pausado (nao gera alerta, mas permanece na lista)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        barra_status = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_status.pack(fill="x", padx=16, pady=(0, 6))

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

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))

        grupo_esquerda = ctk.CTkFrame(barra, fg_color="transparent")
        grupo_esquerda.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            grupo_esquerda,
            text="Adicionar monitoramento",
            command=self._abrir_adicionar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=190,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            grupo_esquerda,
            text="Atualizar cotacoes",
            command=lambda: self._atualizar_lista(forcar=True),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=150,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            grupo_esquerda,
            text="Remover selecionados",
            command=self._remover_selecionados,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=160,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            grupo_esquerda,
            text="Editar limites",
            command=self._editar_limites_selecionado,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            grupo_esquerda,
            text="Pausar itens",
            command=lambda: self._alterar_pausa_selecionados(pausado=True),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            grupo_esquerda,
            text="Retomar itens",
            command=lambda: self._alterar_pausa_selecionados(pausado=False),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="left")

        grupo_direita = ctk.CTkFrame(barra, fg_color="transparent")
        grupo_direita.pack(side="right")

        self._botao_pausar = ctk.CTkButton(
            grupo_direita,
            text="Pausar monitoramento",
            command=self._alternar_pausa,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=170,
        )
        self._botao_pausar.pack(side="right", padx=(8, 0))

        criar_botao_engrenagem(
            grupo_direita,
            command=self._abrir_config_atualizacao,
            width=36,
            height=36,
        ).pack(side="right", padx=(8, 0))

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._tabela = criar_grid_monitoramento(
            container,
            "Ativos monitorados",
            altura=18,
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

    def _abrir_adicionar(self) -> None:
        if self._janela_adicionar is not None:
            try:
                if self._janela_adicionar.winfo_exists():
                    self._janela_adicionar.focus_force()
                    self._janela_adicionar.lift()
                    return
            except Exception:
                pass

        self._janela_adicionar = abrir_adicionar_monitoramento(
            self,
            self._controlador,
            ao_salvar=lambda: self._atualizar_lista(forcar=True),
        )

    def _abrir_config_atualizacao(self) -> None:
        if self._janela_config_auto is not None:
            try:
                if self._janela_config_auto.winfo_exists():
                    self._janela_config_auto.focus_force()
                    self._janela_config_auto.lift()
                    return
            except Exception:
                pass

        self._janela_config_auto = abrir_config_atualizacao_monitoramento(
            self,
            self._config_painel,
            ao_salvar=self._ao_salvar_config_atualizacao,
        )

    def _ao_salvar_config_atualizacao(self) -> None:
        self._atualizar_indicador_automatico()
        if not self._pausado:
            self._atualizador_auto.retomar()

    def _atualizar_indicador_automatico(self) -> None:
        if self._pausado:
            self._label_auto.configure(text="Monitoramento pausado", text_color=CORES["aviso"])
            return

        opcoes = self._atualizador_auto.obter_opcoes()
        if opcoes.habilitada:
            texto = f"Auto: a cada {opcoes.intervalo_segundos} s"
            cor = CORES["sucesso"]
        else:
            texto = "Auto: desligado"
            cor = CORES["textoSecundario"]
        self._label_auto.configure(text=texto, text_color=cor)

    def _alternar_pausa(self) -> None:
        self._pausado = not self._pausado
        try:
            self._config_painel.salvar_monitoramento_pausado(self._pausado)
        except OSError:
            messagebox.showerror(
                "Monitoramento",
                "Nao foi possivel gravar o estado de pausa em dados/painel.ini.",
                parent=self,
            )
            self._pausado = not self._pausado
            return

        if self._pausado:
            self._atualizador_auto.pausar()
        else:
            self._atualizador_auto.retomar()
            self._atualizar_lista(forcar=True)

        self._aplicar_visual_pausa()
        self._atualizar_indicador_automatico()
        self._notificar_pai_verificar_alertas()

    def _aplicar_visual_pausa(self) -> None:
        if self._pausado:
            self._botao_pausar.configure(text="Retomar monitoramento")
            if not self._label_status.cget("text"):
                self._label_status.configure(
                    text="Monitoramento pausado — alertas nao serao atualizados automaticamente.",
                    text_color=CORES["aviso"],
                )
        else:
            self._botao_pausar.configure(text="Pausar monitoramento")

    def _obter_ids_selecionados(self) -> list[str]:
        if self._tabela is None:
            return []
        return list(self._tabela.selection())

    def _editar_limites_selecionado(self) -> None:
        selecionados = self._obter_ids_selecionados()
        if len(selecionados) != 1:
            messagebox.showwarning(
                "Editar limites",
                "Selecione exatamente um item na grid.",
                parent=self,
            )
            return

        item_id = selecionados[0]
        linha = self._linhas_cache.get(item_id)
        item = linha.item if linha is not None else self._controlador.obter_item(item_id)
        if item is None:
            messagebox.showwarning(
                "Editar limites",
                "Item de monitoramento nao encontrado.",
                parent=self,
            )
            return

        if self._janela_editar is not None:
            try:
                if self._janela_editar.winfo_exists():
                    self._janela_editar.focus_force()
                    self._janela_editar.lift()
                    return
            except Exception:
                pass

        self._janela_editar = abrir_editar_monitoramento(
            self,
            self._controlador,
            item,
            ao_salvar=lambda: self._atualizar_lista(forcar=True),
        )

    def _alterar_pausa_selecionados(self, pausado: bool) -> None:
        selecionados = self._obter_ids_selecionados()
        if not selecionados:
            acao = "pausar" if pausado else "retomar"
            messagebox.showwarning(
                "Monitoramento",
                f"Selecione um ou mais itens para {acao}.",
                parent=self,
            )
            return

        alterados, erro = self._controlador.definir_pausa_itens(selecionados, pausado)
        if erro:
            messagebox.showwarning("Monitoramento", erro, parent=self)
            return
        if alterados == 0:
            return

        self._atualizar_lista(forcar=True)

    def _remover_selecionados(self) -> None:
        if self._tabela is None:
            return
        selecionados = self._tabela.selection()
        if not selecionados:
            messagebox.showwarning(
                "Remover",
                "Selecione um ou mais itens na grid.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
            "Remover monitoramento",
            f"Remover {len(selecionados)} item(ns) do monitoramento?",
            parent=self,
        ):
            return

        removidos, erro = self._controlador.remover_itens(list(selecionados))
        if erro:
            messagebox.showwarning("Remover", erro, parent=self)
            return
        self._atualizar_lista(forcar=True)

    def _atualizar_lista(self, forcar: bool = False, automatico: bool = False) -> None:
        if not janela_ui_ainda_ativa(self):
            return
        if automatico and self._pausado:
            return
        if self._atualizando and not forcar:
            return

        self._versao_atualizacao += 1
        versao = self._versao_atualizacao
        self._atualizando = True
        if not automatico:
            self._label_status.configure(text="Atualizando cotacoes monitoradas...")

        def tarefa():
            return self._controlador.obter_linhas_monitoramento()

        def ao_concluir(resultado, erro):
            if versao != self._versao_atualizacao:
                return
            self._atualizando = False
            if not janela_ui_ainda_ativa(self) or self._tabela is None:
                return
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                if not automatico:
                    messagebox.showerror("Monitoramento", erro, parent=self)
                return

            linhas, _ = resultado
            self._linhas_cache = {linha.item.id: linha for linha in linhas}
            preencher_grid_monitoramento(self._tabela, linhas)

            hora = datetime.now().strftime("%H:%M:%S")
            alertas_baixo = sum(1 for linha in linhas if linha.status == "abaixo")
            alertas_alto = sum(1 for linha in linhas if linha.status == "acima")
            itens_pausados = sum(1 for linha in linhas if linha.item.pausado)
            if self._pausado:
                texto = (
                    f"Pausado — ultima leitura as {hora} — {len(linhas)} ativo(s) | "
                    f"alertas baixo {alertas_baixo} | alertas alto {alertas_alto}"
                )
                if itens_pausados:
                    texto += f" | itens pausados {itens_pausados}"
                cor = CORES["aviso"]
            else:
                texto = (
                    f"Atualizado as {hora} — {len(linhas)} ativo(s) | "
                    f"alertas baixo {alertas_baixo} | alertas alto {alertas_alto}"
                )
                if itens_pausados:
                    texto += f" | itens pausados {itens_pausados}"
                cor = CORES["sucesso"]
                if alertas_baixo or alertas_alto:
                    cor = CORES.get("aviso", CORES["texto"])
            self._label_status.configure(text=texto, text_color=cor)
            self._notificar_pai_verificar_alertas()

        executar_em_thread(self, tarefa, ao_concluir)

    def _notificar_pai_verificar_alertas(self) -> None:
        """Atualiza icone/botao de alerta na janela principal, se existir."""
        pai = self.master
        if hasattr(pai, "_agendar_verificacao_alertas_monitoramento"):
            pai._agendar_verificacao_alertas_monitoramento(notificar=False)

    def _ao_duplo_clique(self, evento) -> None:
        if self._tabela is None:
            return
        item_id = obter_id_duplo_clique_monitoramento(self._tabela, evento)
        if not item_id:
            return
        linha = self._linhas_cache.get(item_id)
        if linha is None:
            return
        self._abrir_grafico(linha.item)

    def _abrir_grafico(self, item: MonitoramentoItem) -> None:
        controlador = obter_controlador_por_tipo(item.tipo_ativo)

        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass

        self._janela_grafico = JanelaGraficoAcao(self, controlador, item.simbolo)
        codigo = codigo_exibicao(item.simbolo)
        self._janela_grafico.title(f"Grafico — {codigo}")


def abrir_monitoramento(pai: ctk.CTk) -> JanelaMonitoramento | None:
    if not pai.winfo_exists():
        return None
    return JanelaMonitoramento(pai)
