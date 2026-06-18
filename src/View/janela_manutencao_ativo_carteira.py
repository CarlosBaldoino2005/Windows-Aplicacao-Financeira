"""Tela de manutencao de ativos da carteira (compras, vendas e edicao)."""
from __future__ import annotations

from datetime import datetime
from tkinter import ttk

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import (
    LinhaCarteira,
    PosicaoCarteira,
    TipoAtivoCarteira,
    tipo_carteira_para_monitoramento,
)
from src.Model.monitoramento import TipoAtivoMonitoramento
from src.Tool.atualizacao_automatica_helper import GerenciadorAtualizacaoAutomatica
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.controlador_ativo_helper import obter_controlador_por_tipo
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import (
    centralizar_janela_sobre_referencia,
    configurar_janela_filha_modal,
    configurar_janela_maximizada,
    executar_em_thread,
    janela_ui_ainda_ativa,
    liberar_modal_janela_filha,
)
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.View.formatadores import formatar_moeda
from src.View.janela_adicionar_carteira import abrir_adicionar_carteira
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.janela_vendas_carteira import abrir_vendas_carteira
from src.View.tabela_carteira_helper import (
    aplicar_ajuste_altura_grid_carteira,
    criar_grid_carteira,
    liberar_grid_carteira,
    obter_id_duplo_clique_carteira,
    preencher_grid_carteira,
)
from src.View.tema import CORES


class JanelaManutencaoAtivoCarteira(ctk.CTkToplevel):
    """Grid da carteira com acoes de compra, venda, edicao e remocao."""

    def __init__(self, carteira) -> None:
        super().__init__(carteira)
        self._carteira = carteira
        self._controlador = ControladorCarteira()
        self._config_painel = ConfigPainelIni()
        self._janela_form = None
        self._janela_vendas = None
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._tabela: ttk.Treeview | None = None
        self._linhas_cache: dict[str, LinhaCarteira] = {}
        self._atualizando = False
        self._versao_atualizacao = 0
        self._atualizador_auto = None

        self.title("Manutencao de ativo")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(1020, 680)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=carteira)
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
        self.after(400, lambda: aplicar_ajuste_altura_grid_carteira(self._tabela))

    def _montar_interface(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            cabecalho,
            text="Manutencao de ativo",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Registre compras e vendas, edite posicoes ou remova ativos da carteira. "
                "Duplo clique na grid abre o grafico do ativo."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=920,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        barra_status = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_status.pack(fill="x", padx=16, pady=(0, 6))

        self._label_status = ctk.CTkLabel(
            barra_status,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_status.pack(side="left", anchor="w")

        self._label_auto = ctk.CTkLabel(
            barra_status,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="e",
        )
        self._label_auto.pack(side="right", anchor="e")

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))

        botoes = (
            ("Registrar compra", self._abrir_formulario),
            ("Editar selecionado", self._editar_selecionado),
            ("Nova compra do ativo", self._nova_compra_mesmo_ativo),
            ("Registrar venda", self._vender_selecionado),
            ("Remover selecionados", self._remover_selecionados),
            ("Vendas realizadas", self._abrir_vendas_realizadas),
            ("Atualizar cotacoes", lambda: self._atualizar_lista(forcar=True)),
        )
        for texto, comando in botoes:
            ctk.CTkButton(
                barra,
                text=texto,
                command=comando,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=160,
                height=36,
            ).pack(side="left", padx=(0, 8))

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._tabela = criar_grid_carteira(
            container,
            "Posicoes da carteira",
            altura=6,
            ao_duplo_clique=self._ao_duplo_clique,
            modo_tela_cheia=True,
        )

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
            height=36,
        ).pack(side="right")

    def _atualizar_indicador_automatico(self) -> None:
        if self._atualizador_auto is None:
            return
        opcoes = self._atualizador_auto.obter_opcoes()
        if opcoes.habilitada:
            texto = f"Auto: a cada {opcoes.intervalo_segundos} s"
            cor = CORES["sucesso"]
        else:
            texto = "Auto: desligado"
            cor = CORES["textoSecundario"]
        self._label_auto.configure(text=texto, text_color=cor)

    def _notificar_carteira_pai(self) -> None:
        try:
            if self._carteira is not None and self._carteira.winfo_exists():
                self._carteira._atualizar_lista(forcar=True)
        except Exception:
            pass

    def _abrir_formulario(
        self,
        posicao: PosicaoCarteira | None = None,
        *,
        preencher_ativo: tuple[str, TipoAtivoCarteira] | None = None,
    ) -> None:
        if self._janela_form is not None:
            try:
                if self._janela_form.winfo_exists():
                    self._janela_form.focus_force()
                    self._janela_form.lift()
                    return
            except Exception:
                pass

        def ao_salvar() -> None:
            self._atualizar_lista(forcar=True)
            self._notificar_carteira_pai()

        self._janela_form = abrir_adicionar_carteira(
            self,
            self._controlador,
            ao_salvar=ao_salvar,
            posicao=posicao,
            preencher_ativo=preencher_ativo,
        )

    def _obter_ids_selecionados(self) -> list[str]:
        if self._tabela is None:
            return []
        return list(self._tabela.selection())

    def _nova_compra_mesmo_ativo(self) -> None:
        selecionados = self._obter_ids_selecionados()
        if len(selecionados) != 1:
            messagebox.showwarning(
                "Nova compra",
                "Selecione exatamente uma posicao na grid para registrar outra compra do mesmo ativo.",
                parent=self,
            )
            return

        posicao = self._controlador.obter_posicao(selecionados[0])
        if posicao is None:
            messagebox.showwarning("Nova compra", "Posicao nao encontrada.", parent=self)
            return

        self._abrir_formulario(preencher_ativo=(posicao.simbolo, posicao.tipo_ativo))

    def _editar_selecionado(self) -> None:
        selecionados = self._obter_ids_selecionados()
        if len(selecionados) != 1:
            messagebox.showwarning(
                "Editar",
                "Selecione exatamente uma posicao na grid.",
                parent=self,
            )
            return

        posicao = self._controlador.obter_posicao(selecionados[0])
        if posicao is None:
            messagebox.showwarning("Editar", "Posicao nao encontrada.", parent=self)
            return

        self._abrir_formulario(posicao)

    def _vender_selecionado(self) -> None:
        selecionados = self._obter_ids_selecionados()
        if len(selecionados) != 1:
            messagebox.showwarning(
                "Venda",
                "Selecione exatamente uma posicao para registrar venda.",
                parent=self,
            )
            return

        posicao = self._controlador.obter_posicao(selecionados[0])
        if posicao is None:
            messagebox.showwarning("Venda", "Posicao nao encontrada.", parent=self)
            return

        self._abrir_dialogo_venda(posicao)

    def _abrir_vendas_realizadas(self) -> None:
        if self._janela_vendas is not None and self._janela_vendas.winfo_exists():
            self._janela_vendas.lift()
            self._janela_vendas.focus_force()
            return
        try:
            self._janela_vendas = abrir_vendas_carteira(self)
        except Exception as exc:
            messagebox.showerror(
                "Vendas realizadas",
                f"Nao foi possivel abrir a tela de vendas:\n{exc}",
                parent=self,
            )
            self._janela_vendas = None

    def _centralizar_dialogo_sobre_pai(
        self,
        dialogo: ctk.CTkToplevel,
        largura: int,
        altura: int,
    ) -> None:
        try:
            dialogo.update_idletasks()
            centralizar_janela_sobre_referencia(dialogo, self, largura, altura)
        except Exception:
            pass

    def _abrir_dialogo_venda(self, posicao: PosicaoCarteira) -> None:
        dialogo = ctk.CTkToplevel(self)
        dialogo.title(f"Vender {codigo_exibicao(posicao.simbolo)}")
        dialogo.configure(fg_color=CORES["fundo"])
        dialogo.resizable(False, False)

        painel = ctk.CTkFrame(dialogo, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            painel,
            text=f"Quantidade a vender (max. {posicao.quantidade})",
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        entrada_qtd = ctk.CTkEntry(painel, width=220, placeholder_text="Ex.: 50")
        entrada_qtd.pack(anchor="w", padx=16, pady=(0, 10))
        entrada_qtd.focus_set()

        ctk.CTkLabel(
            painel,
            text="Preco de venda (por cota)",
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(0, 4))

        entrada_preco = ctk.CTkEntry(painel, width=220, placeholder_text="Ex.: 32,50")
        entrada_preco.pack(anchor="w", padx=16, pady=(0, 10))
        aplicar_mascara_moeda_ptbr(entrada_preco)

        ctk.CTkLabel(
            painel,
            text="Data da venda (dd/mm/aaaa)",
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(0, 4))

        entrada_data = ctk.CTkEntry(painel, width=220)
        entrada_data.pack(anchor="w", padx=16, pady=(0, 10))
        entrada_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        ctk.CTkLabel(
            painel,
            text=f"Preco medio de compra: {formatar_moeda(posicao.preco_compra)}",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        def fechar_dialogo() -> None:
            liberar_modal_janela_filha(dialogo)
            dialogo.destroy()

        def confirmar() -> None:
            ok, erro = self._controlador.registrar_venda(
                posicao.id,
                entrada_qtd.get(),
                entrada_preco.get(),
                entrada_data.get(),
            )
            if erro:
                messagebox.showwarning("Venda", erro, parent=dialogo)
                return
            fechar_dialogo()
            self._atualizar_lista(forcar=True)
            self._notificar_carteira_pai()

        barra = ctk.CTkFrame(painel, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(
            barra,
            text="Cancelar",
            command=fechar_dialogo,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right")
        ctk.CTkButton(
            barra,
            text="Confirmar",
            command=confirmar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right", padx=(0, 8))

        entrada_qtd.bind("<Return>", lambda _e: confirmar())
        entrada_preco.bind("<Return>", lambda _e: confirmar())
        entrada_data.bind("<Return>", lambda _e: confirmar())

        largura, altura = 380, 360
        self._centralizar_dialogo_sobre_pai(dialogo, largura, altura)
        configurar_janela_filha_modal(dialogo, self)
        dialogo.protocol("WM_DELETE_WINDOW", fechar_dialogo)
        dialogo.focus_force()

    def _remover_selecionados(self) -> None:
        selecionados = self._obter_ids_selecionados()
        if not selecionados:
            messagebox.showwarning(
                "Remover",
                "Selecione uma ou mais posicoes na grid.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
            "Remover posicao",
            f"Remover {len(selecionados)} posicao(oes) da carteira e do monitoramento?",
            parent=self,
        ):
            return

        for posicao_id in selecionados:
            self._controlador.remover_posicao(posicao_id)

        self._atualizar_lista(forcar=True)
        self._notificar_carteira_pai()

    def _atualizar_lista(self, *, forcar: bool = False, automatico: bool = False) -> None:
        if self._atualizando and not forcar:
            return
        if not janela_ui_ainda_ativa(self):
            return

        self._atualizando = True
        versao = self._versao_atualizacao
        if not automatico:
            self._label_status.configure(
                text="Atualizando cotacoes...",
                text_color=CORES["textoSecundario"],
            )

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
        if self._atualizador_auto is not None:
            self._atualizador_auto.parar()
        liberar_grid_carteira(self._tabela)
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        if self._janela_vendas is not None:
            try:
                if self._janela_vendas.winfo_exists():
                    self._janela_vendas.destroy()
            except Exception:
                pass
        try:
            if self._carteira is not None:
                self._carteira._janela_manutencao = None
        except Exception:
            pass
        self.destroy()


def abrir_manutencao_ativo_carteira(carteira) -> JanelaManutencaoAtivoCarteira:
    return JanelaManutencaoAtivoCarteira(carteira)
