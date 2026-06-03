"""
Interface desktop 100% Python (CustomTkinter + Matplotlib).
Painel, graficos e comparacao de acoes.
"""
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.cotacao import CotacaoResumo
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.janela_grafico_comparacao import JanelaGraficoComparacao
from src.View.janela_favoritas import JanelaFavoritas
from src.View.janela_pesquisa_acao import JanelaPesquisaAcao
from src.View.tabela_mercado_helper import (
    criar_card_tabela,
    preencher_tabela as preencher_tabela_mercado,
)
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import maximizar_janela
from src.Tool.validadores import validar_quantidade_acoes
from src.View.tema import CORES

PERIODOS = [
    ("dia", "Dia"),
    ("semana", "Semana"),
    ("mes", "Mes"),
    ("trimestre", "Trimestre"),
    ("semestre", "Semestre"),
    ("ano", "Ano"),
    ("personalizado", "Personalizado"),
]

class InterfaceApp(ctk.CTk):
    """Janela principal da aplicacao Financeiro."""

    def __init__(self) -> None:
        super().__init__()
        self._controlador = ControladorMercado()
        self._config_painel = ConfigPainelIni()
        self._simbolos_comparacao: list[str] = []
        self._janela_comparacao: JanelaGraficoComparacao | None = None
        self._janela_pesquisa: JanelaPesquisaAcao | None = None
        self._janela_favoritas: JanelaFavoritas | None = None
        self._janela_grafico_acao: JanelaGraficoAcao | None = None
        self._carga_inicial_painel_feita = False

        self._configurar_aparencia()
        self._montar_layout()
        # Abre maximizado (padrao do projeto e regra global do usuario).
        self.after(0, lambda: maximizar_janela(self))
        self._agendar_carga_inicial_painel()

    def _configurar_aparencia(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("Financeiro - Painel de Mercado")
        self.minsize(900, 600)
        self.configure(fg_color=CORES["fundo"])

    def _montar_layout(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            cabecalho,
            text="Financeiro",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=20, pady=(12, 0))

        ctk.CTkLabel(
            cabecalho,
            text="Cotacoes, acoes em alta, graficos e comparacao para analise de investimentos",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._montar_area_consultas()

        self._abas = ctk.CTkTabview(self, fg_color=CORES["fundo"])
        self._abas.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._aba_alta = self._abas.add("Em alta")
        self._aba_queda = self._abas.add("Em queda")
        self._aba_todas = self._abas.add("Todas")
        self._aba_comparar = self._abas.add("Comparar acoes")

        self._montar_abas_cotacoes()
        self._montar_aba_comparar()

        aviso = ctk.CTkLabel(
            self,
            text="Dados publicos (Yahoo Finance). Uso educacional — nao e recomendacao de investimento.",
            font=ctk.CTkFont(size=11),
            text_color="#92400E",
            fg_color="#FFFBEB",
            corner_radius=8,
        )
        aviso.pack(fill="x", padx=16, pady=(0, 12))

    def _montar_area_consultas(self) -> None:
        """Botoes de pesquisa e favoritos acima das abas de cotacoes."""
        card_acao = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        card_acao.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            card_acao,
            text="Consultas e favoritos",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            card_acao,
            text="Pesquise uma acao ou gerencie sua lista de favoritas com cotacoes salvas no computador.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=12, pady=(0, 8))

        linha_botoes = ctk.CTkFrame(card_acao, fg_color="transparent")
        linha_botoes.pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            linha_botoes,
            text="Pesquisar acao",
            command=self._abrir_janela_pesquisa_acao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=200,
            height=36,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            linha_botoes,
            text="Acoes favoritas",
            command=self._abrir_janela_favoritas,
            fg_color=CORES["secundaria"],
            width=200,
            height=36,
        ).pack(side="left")

        barra = ctk.CTkFrame(card_acao, fg_color="transparent")
        barra.pack(fill="x", padx=12, pady=(0, 12))

        qtd_ini = self._config_painel.carregar()
        self._label_status_painel = ctk.CTkLabel(
            barra,
            text=f"Carregando ate {qtd_ini} acoes em cada aba...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status_painel.pack(side="left")

        ctk.CTkButton(
            barra,
            text="Atualizar cotacoes",
            command=self._carregar_painel,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="right")

        ctk.CTkLabel(barra, text="Qtd. acoes").pack(side="right", padx=(8, 4))
        self._entrada_quantidade_acoes = ctk.CTkEntry(barra, width=50, justify="center")
        self._entrada_quantidade_acoes.insert(0, str(qtd_ini))
        self._entrada_quantidade_acoes.pack(side="right", padx=(0, 12))

    def _montar_conteudo_aba_cotacoes(
        self, aba: ctk.CTkFrame, titulo: str
    ) -> ttk.Treeview:
        """Container fixo na aba evita grid sumir no CTkTabview."""
        container = ctk.CTkFrame(aba, fg_color=CORES["fundo"])
        container.pack(fill="both", expand=True, padx=4, pady=4)

        scroll = ctk.CTkScrollableFrame(container, fg_color=CORES["fundo"])
        scroll.pack(fill="both", expand=True)

        return criar_card_tabela(
            scroll,
            titulo,
            altura=18,
            ao_duplo_clique=self._ao_duplo_clique_tabela,
            expandir=False,
        )

    def _montar_abas_cotacoes(self) -> None:
        """Uma aba para cada lista: alta, queda e todas."""
        self._tabela_alta = self._montar_conteudo_aba_cotacoes(
            self._aba_alta,
            "Acoes em alta no dia (duplo clique abre o grafico)",
        )
        self._tabela_queda = self._montar_conteudo_aba_cotacoes(
            self._aba_queda,
            "Acoes em queda no dia (duplo clique abre o grafico)",
        )
        self._tabela_todas = self._montar_conteudo_aba_cotacoes(
            self._aba_todas,
            "Todas as acoes monitoradas (duplo clique abre o grafico)",
        )
        self._abas.set("Em alta")

    def _agendar_carga_inicial_painel(self) -> None:
        """Carrega alta, queda e todas automaticamente ao abrir o sistema."""
        self.after(150, self._executar_carga_inicial_painel)
        self.bind("<Map>", self._ao_janela_exibida, add="+")

    def _ao_janela_exibida(self, _evento=None) -> None:
        self._executar_carga_inicial_painel()

    def _executar_carga_inicial_painel(self) -> None:
        if self._carga_inicial_painel_feita:
            return
        if not self.winfo_exists():
            return
        self._carga_inicial_painel_feita = True
        self._carregar_painel()

    def _preencher_tabela(self, tabela: ttk.Treeview, itens: list[CotacaoResumo]) -> None:
        preencher_tabela_mercado(tabela, itens)

    def _ao_duplo_clique_tabela(self, evento) -> None:
        widget = evento.widget
        selecao = widget.selection()
        if not selecao:
            return
        self._abrir_grafico_por_simbolo(selecao[0])

    def _abrir_grafico_por_simbolo(self, simbolo: str) -> None:
        """Abre janela dedicada com grafico da acao (duplo clique no painel)."""
        if self._janela_grafico_acao is not None:
            try:
                if self._janela_grafico_acao.winfo_exists():
                    self._janela_grafico_acao._ao_fechar()
            except Exception:
                pass

        self._janela_grafico_acao = JanelaGraficoAcao(self, self._controlador, simbolo)

    def _abrir_janela_pesquisa_acao(self) -> None:
        """Abre (ou foca) a tela dedicada de pesquisa de acao."""
        if self._janela_pesquisa is not None:
            try:
                if self._janela_pesquisa.winfo_exists():
                    self._janela_pesquisa.focus_force()
                    self._janela_pesquisa.lift()
                    return
            except Exception:
                pass

        self._janela_pesquisa = JanelaPesquisaAcao(self, self._controlador)

    def _abrir_janela_favoritas(self) -> None:
        """Abre (ou foca) a tela de acoes favoritas."""
        if self._janela_favoritas is not None:
            try:
                if self._janela_favoritas.winfo_exists():
                    self._janela_favoritas.focus_force()
                    self._janela_favoritas.lift()
                    self._janela_favoritas._atualizar_grid()
                    return
            except Exception:
                pass

        self._janela_favoritas = JanelaFavoritas(self, self._controlador)

    def _montar_aba_comparar(self) -> None:
        form = ctk.CTkFrame(self._aba_comparar, fg_color=CORES["superficie"], corner_radius=12)
        form.pack(fill="x", pady=(0, 8))

        linha_busca = ctk.CTkFrame(form, fg_color="transparent")
        linha_busca.pack(fill="x", padx=12, pady=(12, 4))

        ctk.CTkLabel(linha_busca, text="Pesquisar acao").pack(side="left", padx=(0, 8))
        self._entrada_busca_comparar = ctk.CTkEntry(
            linha_busca, width=280, placeholder_text="Nome ou codigo: Vale, PETR4, Apple..."
        )
        self._entrada_busca_comparar.pack(side="left", padx=(0, 8))
        self._entrada_busca_comparar.bind("<Return>", lambda _e: self._pesquisar_acoes_comparacao())

        ctk.CTkButton(
            linha_busca,
            text="Buscar",
            command=self._pesquisar_acoes_comparacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left")

        self._frame_resultados_busca = ctk.CTkScrollableFrame(
            form, height=120, fg_color=CORES["fundo"], label_text="Resultados da busca"
        )
        self._frame_resultados_busca.pack(fill="x", padx=12, pady=(4, 8))

        linha1 = ctk.CTkFrame(form, fg_color="transparent")
        linha1.pack(fill="x", padx=12, pady=(4, 12))

        ctk.CTkLabel(linha1, text="Ou digite o codigo").pack(side="left", padx=(0, 8))
        self._entrada_comparar = ctk.CTkEntry(linha1, width=120, placeholder_text="VALE3")
        self._entrada_comparar.pack(side="left", padx=(0, 8))
        self._entrada_comparar.bind("<Return>", lambda _e: self._adicionar_simbolo_comparacao())

        ctk.CTkButton(
            linha1,
            text="Adicionar",
            command=self._adicionar_simbolo_comparacao,
            fg_color=CORES["secundaria"],
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(linha1, text="Periodo").pack(side="left", padx=(0, 8))
        self._combo_periodo_comparar = ctk.CTkComboBox(
            linha1, values=[p[1] for p in PERIODOS], width=140, command=self._alternar_datas_comparar
        )
        self._combo_periodo_comparar.set("Mes")
        self._combo_periodo_comparar.pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            linha1,
            text="Comparar",
            command=self._carregar_comparacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left")

        self._label_chips = ctk.CTkLabel(
            form,
            text="Acoes selecionadas: (nenhuma)",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        )
        self._label_chips.pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(
            form,
            text="Limpar lista",
            width=100,
            command=self._limpar_comparacao,
            fg_color="transparent",
            border_width=1,
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(0, 12))

        self._frame_datas_comparar = ctk.CTkFrame(form, fg_color="transparent")
        ctk.CTkLabel(self._frame_datas_comparar, text="Inicio").pack(side="left", padx=8)
        self._entrada_inicio_comparar = ctk.CTkEntry(self._frame_datas_comparar, width=110)
        self._entrada_inicio_comparar.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(self._frame_datas_comparar, text="Fim").pack(side="left")
        self._entrada_fim_comparar = ctk.CTkEntry(self._frame_datas_comparar, width=110)
        self._entrada_fim_comparar.pack(side="left", padx=8)

        self._label_status_comparar = ctk.CTkLabel(
            self._aba_comparar,
            text="Selecione as acoes e clique em Comparar para abrir o grafico em tela cheia.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        )
        self._label_status_comparar.pack(anchor="w", padx=12, pady=8)

    def _periodo_selecionado(self, combo: ctk.CTkComboBox) -> str:
        rotulo = combo.get()
        for chave, nome in PERIODOS:
            if nome == rotulo:
                return chave
        return "mes"

    def _alternar_datas_comparar(self, _valor=None) -> None:
        if self._periodo_selecionado(self._combo_periodo_comparar) == "personalizado":
            self._frame_datas_comparar.pack(fill="x", padx=12, pady=(0, 12))
        else:
            self._frame_datas_comparar.pack_forget()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        def trabalho():
            try:
                resultado = funcao()
                self.after(0, lambda: ao_concluir(resultado, None))
            except Exception as exc:
                self.after(0, lambda: ao_concluir(None, str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _ler_quantidade_painel(self) -> tuple[int | None, str | None]:
        return validar_quantidade_acoes(self._entrada_quantidade_acoes.get())

    def _carregar_painel(self) -> None:
        quantidade, erro_qtd = self._ler_quantidade_painel()
        if erro_qtd:
            messagebox.showwarning("Quantidade", erro_qtd)
            return

        try:
            self._config_painel.salvar(quantidade)
        except OSError:
            messagebox.showwarning(
                "Configuracao",
                "Nao foi possivel salvar dados/painel.ini. As cotacoes serao atualizadas mesmo assim.",
            )

        self._label_status_painel.configure(
            text=f"Carregando ate {quantidade} acoes em cada aba..."
        )

        def buscar():
            return self._controlador.obter_painel(quantidade)

        def ao_concluir(dados, erro):
            if erro:
                self._label_status_painel.configure(text=f"Erro: {erro}", text_color=CORES["erro"])
                messagebox.showerror("Erro", erro)
                return
            self._preencher_tabela(self._tabela_alta, dados["em_alta"])
            self._preencher_tabela(self._tabela_queda, dados["em_queda"])
            self._preencher_tabela(self._tabela_todas, dados["todas"])
            self._abas.set("Em alta")
            self.update_idletasks()
            qtd = dados.get("quantidade", quantidade)
            self._label_status_painel.configure(
                text=(
                    f"Atualizado em {self._hora_agora()} — limite {qtd} | "
                    f"alta {len(dados['em_alta'])} | "
                    f"baixa {len(dados['em_queda'])} | "
                    f"todas {len(dados['todas'])}"
                ),
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _incluir_simbolo_na_comparacao(self, simbolo: str) -> bool:
        """Adiciona ticker na lista se ainda couber (maximo 6)."""
        if not simbolo:
            return False
        if simbolo in self._simbolos_comparacao:
            messagebox.showinfo("Comparar", f"{simbolo.replace('.SA', '')} ja esta na lista.")
            return False
        if len(self._simbolos_comparacao) >= 6:
            messagebox.showwarning("Comparar", "Maximo de 6 acoes por comparacao.")
            return False
        self._simbolos_comparacao.append(simbolo)
        self._atualizar_label_chips()
        return True

    def _pesquisar_acoes_comparacao(self) -> None:
        termo = self._entrada_busca_comparar.get().strip()
        if not termo:
            messagebox.showwarning("Buscar", "Digite o nome ou codigo da acao.")
            return

        self._label_status_comparar.configure(text="Buscando acoes...")

        def buscar():
            return self._controlador.pesquisar_acoes(termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status_comparar.configure(text=erro, text_color=CORES["erro"])
                self._limpar_resultados_busca()
                return
            itens, msg_erro = resultado
            if msg_erro:
                self._label_status_comparar.configure(text=msg_erro, text_color=CORES["erro"])
                self._limpar_resultados_busca()
                return
            self._exibir_resultados_busca(itens)
            self._label_status_comparar.configure(
                text=f"{len(itens)} resultado(s). Clique em Adicionar na linha desejada.",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _limpar_resultados_busca(self) -> None:
        for widget in self._frame_resultados_busca.winfo_children():
            widget.destroy()

    def _exibir_resultados_busca(self, itens) -> None:
        self._limpar_resultados_busca()
        if not itens:
            ctk.CTkLabel(
                self._frame_resultados_busca,
                text="Nenhum resultado.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for item in itens:
            linha = ctk.CTkFrame(self._frame_resultados_busca, fg_color=CORES["superficie"], corner_radius=8)
            linha.pack(fill="x", padx=4, pady=3)

            codigo = item.simbolo.replace(".SA", "")
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
                command=lambda s=item.simbolo: self._adicionar_da_busca(s),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            ).pack(side="right", padx=8, pady=4)

    def _adicionar_da_busca(self, simbolo: str) -> None:
        if self._incluir_simbolo_na_comparacao(simbolo):
            self._label_status_comparar.configure(
                text=f"{simbolo.replace('.SA', '')} adicionada a comparacao.",
                text_color=CORES["sucesso"],
            )

    def _adicionar_simbolo_comparacao(self) -> None:
        from src.Tool.validadores import normalizar_simbolo

        texto = self._entrada_comparar.get().strip()
        simbolo, erro = normalizar_simbolo(texto)
        if erro:
            messagebox.showwarning("Comparar", erro)
            return
        if self._incluir_simbolo_na_comparacao(simbolo):
            self._entrada_comparar.delete(0, "end")

    def _limpar_comparacao(self) -> None:
        self._simbolos_comparacao.clear()
        self._atualizar_label_chips()

    def _atualizar_label_chips(self) -> None:
        if not self._simbolos_comparacao:
            self._label_chips.configure(text="Acoes selecionadas: (nenhuma)")
        else:
            texto = ", ".join(s.replace(".SA", "") for s in self._simbolos_comparacao)
            self._label_chips.configure(text=f"Acoes selecionadas: {texto}")

    def _carregar_comparacao(self) -> None:
        if len(self._simbolos_comparacao) < 2:
            messagebox.showwarning("Comparar", "Adicione pelo menos duas acoes.")
            return

        periodo = self._periodo_selecionado(self._combo_periodo_comparar)
        self._label_status_comparar.configure(text="Comparando...")

        def buscar():
            return self._controlador.comparar(
                self._simbolos_comparacao,
                periodo,
                self._entrada_inicio_comparar.get(),
                self._entrada_fim_comparar.get(),
            )

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status_comparar.configure(text=erro, text_color=CORES["erro"])
                messagebox.showwarning("Comparar", erro)
                return
            dados, msg_erro = resultado
            if msg_erro:
                self._label_status_comparar.configure(text=msg_erro, text_color=CORES["erro"])
                messagebox.showwarning("Comparar", msg_erro)
                return
            self._abrir_janela_comparacao(dados, periodo)
            self._label_status_comparar.configure(
                text="Grafico aberto em nova janela. Feche-a ou clique em Comparar novamente para atualizar.",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _abrir_janela_comparacao(self, dados: dict, periodo_chave: str) -> None:
        """Abre (ou atualiza) janela dedicada com o grafico de comparacao."""
        rotulos = {chave: nome for chave, nome in PERIODOS}
        rotulo = rotulos.get(periodo_chave, periodo_chave)

        if self._janela_comparacao is not None:
            try:
                if self._janela_comparacao.winfo_exists():
                    self._janela_comparacao._ao_fechar()
            except Exception:
                pass

        self._janela_comparacao = JanelaGraficoComparacao(self, dados, rotulo)

    @staticmethod
    def _hora_agora() -> str:
        from datetime import datetime

        return datetime.now().strftime("%H:%M:%S")


def iniciar_interface() -> None:
    """Abre a janela principal."""
    app = InterfaceApp()
    app.mainloop()
