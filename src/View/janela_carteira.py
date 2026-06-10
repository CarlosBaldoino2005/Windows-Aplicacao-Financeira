"""Tela da carteira de investimentos do usuario."""
from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import LinhaCarteira, PosicaoCarteira, tipo_carteira_para_monitoramento
from src.Model.monitoramento import TipoAtivoMonitoramento
from src.Tool.controlador_ativo_helper import obter_controlador_por_tipo
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.icone_engrenagem_helper import criar_botao_engrenagem
from src.Tool.janela_helper import (
    configurar_janela_filha_modal,
    configurar_janela_maximizada,
    executar_em_thread,
    janela_ui_ainda_ativa,
    liberar_modal_janela_filha,
)
from src.View.formatadores import formatar_moeda
from src.View.janela_adicionar_carteira import abrir_adicionar_carteira
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.tabela_carteira_helper import (
    criar_grid_carteira,
    liberar_grid_carteira,
    obter_id_duplo_clique_carteira,
    preencher_grid_carteira,
)
from src.View.tema import CORES


class JanelaCarteira(ctk.CTkToplevel):
    """Lista posicoes da carteira com resumo e sincronizacao ao monitoramento."""

    def __init__(self, pai: ctk.CTk) -> None:
        super().__init__(pai)
        self._janela_pai = pai
        self._controlador = ControladorCarteira()
        self._janela_form = None
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._tabela: ttk.Treeview | None = None
        self._linhas_cache: dict[str, LinhaCarteira] = {}
        self._atualizando = False
        self._versao_atualizacao = 0
        self._variacao_pct = self._controlador.carregar_variacao_monitoramento_pct()

        self.title("Carteira de investimentos")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(1020, 640)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, lambda: self._atualizar_lista(forcar=True))

    def _ao_fechar(self) -> None:
        self._versao_atualizacao += 1
        liberar_grid_carteira(self._tabela)
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
            text="Carteira de investimentos",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Registre compras e vendas de acoes, criptomoedas, FIIs e indices. "
                "Cada ativo entra no monitoramento com limites de ±"
                f"{self._variacao_pct:.0f}% sobre o preco medio de compra."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=920,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._frame_resumo = ctk.CTkFrame(
            cabecalho,
            fg_color=CORES["fundo"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        self._frame_resumo.pack(fill="x", padx=16, pady=(0, 8))

        self._label_resumo_vazio = ctk.CTkLabel(
            self._frame_resumo,
            text="Carregando resumo...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            justify="left",
            anchor="w",
        )
        self._label_resumo_vazio.pack(anchor="w", padx=12, pady=10)

        self._frame_cards_resumo = ctk.CTkFrame(self._frame_resumo, fg_color="transparent")
        self._card_investido, self._valor_investido, _ = self._criar_card_resumo(
            self._frame_cards_resumo, 0, "Investido"
        )
        self._card_atual, self._valor_atual, _ = self._criar_card_resumo(
            self._frame_cards_resumo, 1, "Valor atual"
        )
        self._card_resultado, self._valor_resultado, self._sub_resultado = self._criar_card_resumo(
            self._frame_cards_resumo, 2, "Resultado", com_subtitulo=True
        )
        self._card_dividendos, self._valor_dividendos, _ = self._criar_card_resumo(
            self._frame_cards_resumo, 3, "Dividendos"
        )

        self._label_monitoramento_resumo = ctk.CTkLabel(
            self._frame_resumo,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_monitoramento_resumo.pack(anchor="w", padx=12, pady=(0, 10))
        self._frame_cards_resumo.pack_forget()

        barra_status = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra_status.pack(fill="x", padx=16, pady=(0, 6))

        self._label_status = ctk.CTkLabel(
            barra_status,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(side="left", anchor="w")

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 12))

        grupo_esquerda = ctk.CTkFrame(barra, fg_color="transparent")
        grupo_esquerda.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            grupo_esquerda,
            text="Registrar compra",
            command=self._abrir_formulario,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=150,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            grupo_esquerda,
            text="Editar selecionado",
            command=self._editar_selecionado,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=140,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            grupo_esquerda,
            text="Registrar venda",
            command=self._vender_selecionado,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=130,
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
            text="Atualizar cotacoes",
            command=lambda: self._atualizar_lista(forcar=True),
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=150,
        ).pack(side="left")

        grupo_direita = ctk.CTkFrame(barra, fg_color="transparent")
        grupo_direita.pack(side="right")

        criar_botao_engrenagem(
            grupo_direita,
            command=self._configurar_variacao,
            width=36,
            height=36,
        ).pack(side="right")

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._tabela = criar_grid_carteira(
            container,
            "Posicoes da carteira",
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

    def _abrir_formulario(self, posicao: PosicaoCarteira | None = None) -> None:
        if self._janela_form is not None:
            try:
                if self._janela_form.winfo_exists():
                    self._janela_form.focus_force()
                    self._janela_form.lift()
                    return
            except Exception:
                pass

        self._janela_form = abrir_adicionar_carteira(
            self,
            self._controlador,
            ao_salvar=lambda: self._atualizar_lista(forcar=True),
            posicao=posicao,
        )

    def _obter_ids_selecionados(self) -> list[str]:
        if self._tabela is None:
            return []
        return list(self._tabela.selection())

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

    def _centralizar_dialogo_sobre_pai(
        self,
        dialogo: ctk.CTkToplevel,
        largura: int,
        altura: int,
    ) -> None:
        """Centraliza dialogo no monitor da janela carteira (pai imediato)."""
        try:
            dialogo.update_idletasks()
            self.update_idletasks()
            x = int(self.winfo_rootx() + max(0, (self.winfo_width() - largura) / 2))
            y = int(self.winfo_rooty() + max(0, (self.winfo_height() - altura) / 2))
            dialogo.geometry(f"{largura}x{altura}+{x}+{y}")
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
        ).pack(anchor="w", padx=16, pady=(16, 8))

        entrada = ctk.CTkEntry(painel, width=200, placeholder_text="Ex.: 50")
        entrada.pack(anchor="w", padx=16, pady=(0, 12))
        entrada.focus_set()

        def fechar_dialogo() -> None:
            liberar_modal_janela_filha(dialogo)
            dialogo.destroy()

        def confirmar() -> None:
            ok, erro = self._controlador.registrar_venda(posicao.id, entrada.get())
            if erro:
                messagebox.showwarning("Venda", erro, parent=dialogo)
                return
            fechar_dialogo()
            self._atualizar_lista(forcar=True)

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

        entrada.bind("<Return>", lambda _e: confirmar())

        largura, altura = 360, 200
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

    def _configurar_variacao(self) -> None:
        dialogo = ctk.CTkToplevel(self)
        dialogo.title("Variacao do monitoramento")
        dialogo.configure(fg_color=CORES["fundo"])
        dialogo.resizable(False, False)

        painel = ctk.CTkFrame(dialogo, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            painel,
            text="Percentual (%) sobre o preco de compra",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            painel,
            text="Limites de monitoramento: preco medio ± este valor (1 a 50).",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        entrada = ctk.CTkEntry(painel, width=120)
        entrada.insert(0, f"{self._variacao_pct:.0f}")
        entrada.pack(anchor="w", padx=16, pady=(0, 12))

        def fechar_dialogo() -> None:
            liberar_modal_janela_filha(dialogo)
            dialogo.destroy()

        def salvar() -> None:
            from src.Tool.validadores import validar_percentual_carteira

            pct, erro = validar_percentual_carteira(entrada.get())
            if erro or pct is None:
                messagebox.showwarning("Configuracao", erro or "Valor invalido.", parent=dialogo)
                return
            self._controlador.salvar_variacao_monitoramento_pct(pct)
            self._variacao_pct = pct
            fechar_dialogo()
            self._atualizar_lista(forcar=True)

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
            text="Salvar",
            command=salvar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right", padx=(0, 8))

        largura, altura = 400, 220
        self._centralizar_dialogo_sobre_pai(dialogo, largura, altura)
        configurar_janela_filha_modal(dialogo, self)
        dialogo.protocol("WM_DELETE_WINDOW", fechar_dialogo)
        dialogo.focus_force()

    def _criar_card_resumo(
        self,
        pai: ctk.CTkFrame,
        coluna: int,
        titulo: str,
        *,
        com_subtitulo: bool = False,
    ) -> tuple[ctk.CTkFrame, ctk.CTkLabel, ctk.CTkLabel | None]:
        """Monta um card de metrica do resumo (titulo, valor e subtitulo opcional)."""
        card = ctk.CTkFrame(
            pai,
            fg_color=CORES["superficie"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        card.grid(row=0, column=coluna, padx=(0 if coluna == 0 else 6, 0), sticky="nsew")
        pai.grid_columnconfigure(coluna, weight=1)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=12, pady=(10, 0))

        valor = ctk.CTkLabel(
            card,
            text="—",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        )
        valor.pack(anchor="w", padx=12, pady=(2, 2 if com_subtitulo else 10))

        subtitulo = None
        if com_subtitulo:
            subtitulo = ctk.CTkLabel(
                card,
                text="",
                font=ctk.CTkFont(size=11),
                text_color=CORES["textoSecundario"],
            )
            subtitulo.pack(anchor="w", padx=12, pady=(0, 10))

        return card, valor, subtitulo

    def _aplicar_estilo_card_resultado(self, resultado: float) -> None:
        """Destaca o card de resultado com cores de lucro ou prejuizo."""
        if resultado > 0:
            fundo = CORES.get("sucessoFundo", CORES["superficie"])
            texto = CORES["sucesso"]
        elif resultado < 0:
            fundo = CORES.get("erroFundo", CORES["superficie"])
            texto = CORES["erro"]
        else:
            fundo = CORES["superficie"]
            texto = CORES["texto"]

        self._card_resultado.configure(fg_color=fundo)
        self._valor_resultado.configure(text_color=texto)
        if self._sub_resultado is not None:
            self._sub_resultado.configure(text_color=texto)

    def _mostrar_resumo_vazio(self, mensagem: str) -> None:
        self._frame_cards_resumo.pack_forget()
        self._label_monitoramento_resumo.configure(text="")
        self._label_resumo_vazio.configure(text=mensagem)
        self._label_resumo_vazio.pack(anchor="w", padx=12, pady=10)

    def _mostrar_resumo_cards(self) -> None:
        self._label_resumo_vazio.pack_forget()
        self._frame_cards_resumo.pack(fill="x", padx=12, pady=(10, 6))

    @staticmethod
    def _formatar_variacao_pct(valor_pct: float) -> str:
        sinal = "+" if valor_pct >= 0 else ""
        return f"{sinal}{valor_pct:.2f}%"

    def _atualizar_resumo(self, linhas: list[LinhaCarteira]) -> None:
        if not linhas:
            self._mostrar_resumo_vazio("Nenhuma posicao cadastrada.")
            return

        investido = 0.0
        atual = 0.0
        dividendos = 0.0
        tem_atual = False
        moeda = "BRL"
        if linhas[0].cotacao is not None:
            moeda = linhas[0].cotacao.moeda

        for linha in linhas:
            investido += linha.posicao.valor_investido
            dividendos += linha.dividendos_recebidos
            if linha.valor_atual is not None:
                atual += linha.valor_atual
                tem_atual = True

        self._mostrar_resumo_cards()
        self._valor_investido.configure(text=formatar_moeda(investido, moeda))
        self._valor_dividendos.configure(text=formatar_moeda(dividendos, moeda))

        if tem_atual:
            resultado = atual - investido
            pct = (resultado / investido * 100) if investido > 0 else 0.0
            self._valor_atual.configure(text=formatar_moeda(atual, moeda))
            self._valor_resultado.configure(text=formatar_moeda(resultado, moeda))
            if self._sub_resultado is not None:
                self._sub_resultado.configure(text=self._formatar_variacao_pct(pct))
            self._aplicar_estilo_card_resultado(resultado)
        else:
            self._valor_atual.configure(text="—")
            self._valor_resultado.configure(text="—")
            if self._sub_resultado is not None:
                self._sub_resultado.configure(text="Cotacao indisponivel")
            self._card_resultado.configure(fg_color=CORES["superficie"])
            self._valor_resultado.configure(text_color=CORES["textoSecundario"])
            if self._sub_resultado is not None:
                self._sub_resultado.configure(text_color=CORES["textoSecundario"])

        self._label_monitoramento_resumo.configure(
            text=(
                f"Monitoramento: ±{self._variacao_pct:.0f}% sobre o preco medio de compra"
                f"  ·  {len(linhas)} posicao(oes) na carteira"
            ),
        )

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
            self._atualizar_resumo(linhas)

            from datetime import datetime

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


def abrir_carteira(pai: ctk.CTk) -> JanelaCarteira | None:
    if not pai.winfo_exists():
        return None
    return JanelaCarteira(pai)
