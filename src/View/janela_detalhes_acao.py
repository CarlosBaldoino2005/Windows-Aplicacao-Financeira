"""Janela com informacoes fundamentais e financeiras da acao."""
from __future__ import annotations

import threading
import webbrowser

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.detalhes_acao import DetalhesAcao, LinhaDemonstrativo, PeriodoResultado
from src.Tool.janela_helper import maximizar_janela
from src.View.formatadores import (
    formatar_moeda,
    formatar_numero_grande,
    formatar_percentual,
    formatar_texto_opcional,
    formatar_variacao,
)
from src.View.tabela_detalhes_helper import adicionar_cabecalho_tabela, adicionar_linha_zebrada
from src.View.tema import CORES

NOMES_ABAS = (
    "Empresa",
    "Indicadores",
    "Trimestres",
    "Anuais",
    "Demonstrativos",
    "Concorrentes",
)


class JanelaDetalhesAcao(ctk.CTkToplevel):
    """Tela ampla com abas: empresa, indicadores, resultados e concorrentes."""

    def __init__(self, pai: ctk.CTk, controlador: ControladorMercado, simbolo: str) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._frames_por_aba: dict[str, ctk.CTkFrame] = {}
        self._botoes_aba: dict[str, ctk.CTkButton] = {}

        codigo = simbolo.replace(".SA", "")
        self.title(f"Mais detalhes — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(960, 640)

        self._montar_interface()
        self.after(50, self._aplicar_maximizar)
        self.after(250, self._aplicar_maximizar)
        self.bind("<Map>", self._ao_mapear_janela)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()
        self.after(150, self._carregar_dados)

    def _montar_interface(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        self._label_titulo = ctk.CTkLabel(
            cabecalho,
            text="Carregando detalhes...",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        )
        self._label_titulo.pack(anchor="w", padx=16, pady=(12, 4))

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="Buscando dados no Yahoo Finance (pode levar alguns segundos).",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(anchor="w", padx=16, pady=(0, 6))

        self._frame_avisos = ctk.CTkFrame(cabecalho, fg_color="transparent")

        barra_abas = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        barra_abas.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self._montar_barra_abas(barra_abas)

        self._painel_conteudo = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._painel_conteudo.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))

        for nome in NOMES_ABAS:
            frame = ctk.CTkFrame(self._painel_conteudo, fg_color="transparent")
            self._frames_por_aba[nome] = frame

        self._label_carregando = ctk.CTkLabel(
            self._painel_conteudo,
            text="Carregando informacoes...",
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
        )
        self._label_carregando.place(relx=0.5, rely=0.5, anchor="center")

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self.destroy,
            fg_color=CORES["secundaria"],
            width=120,
        ).pack(side="right")

    def _montar_barra_abas(self, pai: ctk.CTkFrame) -> None:
        grade = ctk.CTkFrame(pai, fg_color=CORES["borda"], corner_radius=10)
        grade.pack(fill="x", padx=0, pady=(0, 8))

        for coluna, nome in enumerate(NOMES_ABAS):
            grade.columnconfigure(coluna, weight=1)
            botao = ctk.CTkButton(
                grade,
                text=nome,
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda n=nome: self._selecionar_aba(n),
                fg_color=CORES["superficie"],
                hover_color=CORES["zebraEscura"],
                text_color=CORES["texto"],
                border_width=1,
                border_color=CORES["borda"],
            )
            botao.grid(row=0, column=coluna, padx=4, pady=4, sticky="ew")
            self._botoes_aba[nome] = botao

        self._selecionar_aba("Empresa")

    def _aplicar_maximizar(self) -> None:
        maximizar_janela(self)

    def _ao_mapear_janela(self, _evento=None) -> None:
        self._aplicar_maximizar()

    def _selecionar_aba(self, nome: str) -> None:
        for rotulo, botao in self._botoes_aba.items():
            if rotulo == nome:
                botao.configure(
                    fg_color=CORES["primaria"],
                    hover_color=CORES["primariaHover"],
                    text_color=CORES["textoInverso"],
                    border_color=CORES["primaria"],
                )
            else:
                botao.configure(
                    fg_color=CORES["superficie"],
                    hover_color=CORES["zebraEscura"],
                    text_color=CORES["texto"],
                    border_color=CORES["borda"],
                )
        self._trocar_aba(nome)

    def _trocar_aba(self, nome: str) -> None:
        for rotulo, frame in self._frames_por_aba.items():
            if rotulo == nome:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        def trabalho():
            try:
                resultado = funcao()
                self.after(0, lambda: ao_concluir(resultado, None))
            except Exception as exc:
                self.after(0, lambda: ao_concluir(None, str(exc)))

        threading.Thread(target=trabalho, daemon=True).start()

    def _carregar_dados(self) -> None:
        def buscar():
            return self._controlador.obter_detalhes_acao(self._simbolo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                return
            detalhes, msg = resultado
            if msg:
                self._label_status.configure(text=msg, text_color=CORES["erro"])
                return
            if not detalhes:
                self._label_status.configure(text="Detalhes indisponiveis.", text_color=CORES["erro"])
                return
            self._preencher_tela(detalhes)

        self._executar_em_thread(buscar, ao_concluir)

    def _preencher_tela(self, dados: DetalhesAcao) -> None:
        titulo = f"{dados.codigo} — {dados.nome_empresa}"
        self._label_titulo.configure(text=titulo)

        if dados.preco_atual is not None and dados.variacao_dia_pct is not None:
            variacao_valor = dados.preco_atual * (dados.variacao_dia_pct / 100)
            status = formatar_variacao(variacao_valor, dados.variacao_dia_pct, dados.moeda)
            self._label_status.configure(
                text=f"Cotacao: {formatar_moeda(dados.preco_atual, dados.moeda)} ({status})",
                text_color=CORES["sucesso"] if dados.variacao_dia_pct >= 0 else CORES["erro"],
            )
        else:
            self._label_status.configure(
                text=f"Setor: {formatar_texto_opcional(dados.setor)} | Industria: {formatar_texto_opcional(dados.industria)}",
                text_color=CORES["textoSecundario"],
            )

        if dados.avisos:
            self._frame_avisos.pack(fill="x", padx=16, pady=(0, 8))
            for aviso in dados.avisos:
                ctk.CTkLabel(
                    self._frame_avisos,
                    text=aviso,
                    font=ctk.CTkFont(size=11),
                    text_color=CORES["aviso"],
                    wraplength=900,
                    justify="left",
                ).pack(anchor="w", pady=2)

        self._label_carregando.place_forget()

        self._montar_aba_empresa(dados)
        self._montar_aba_indicadores(dados)
        self._montar_aba_periodos(
            self._frames_por_aba["Trimestres"], dados.trimestres, dados.moeda, "trimestre"
        )
        self._montar_aba_periodos(self._frames_por_aba["Anuais"], dados.anuais, dados.moeda, "ano")
        self._montar_aba_demonstrativos(dados)
        self._montar_aba_concorrentes(dados)
        self._selecionar_aba("Empresa")

    def _montar_aba_empresa(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Empresa"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        campos = [
            ("Nome", dados.nome_empresa),
            ("Pais", dados.pais),
            ("Setor", dados.setor),
            ("Industria", dados.industria),
            ("Funcionarios", formatar_texto_opcional(dados.funcionarios)),
            ("Site", dados.site),
        ]
        for rotulo, valor in campos:
            self._linha_info(scroll, rotulo, formatar_texto_opcional(valor))

        if dados.site:
            ctk.CTkButton(
                scroll,
                text="Abrir site da empresa",
                command=lambda url=dados.site: webbrowser.open(url),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                width=200,
            ).pack(anchor="w", padx=4, pady=(4, 12))

        ctk.CTkLabel(
            scroll,
            text="Sobre a empresa",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=4, pady=(8, 4))

        texto_desc = dados.descricao or "Descricao nao disponivel para este ativo."
        ctk.CTkLabel(
            scroll,
            text=texto_desc,
            font=ctk.CTkFont(size=12),
            text_color=CORES["texto"],
            wraplength=880,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

    def _montar_aba_indicadores(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Indicadores"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        grade = ctk.CTkFrame(scroll, fg_color="transparent")
        grade.pack(fill="x")
        grade.columnconfigure((0, 1), weight=1)

        for indice, (rotulo, valor) in enumerate(dados.indicadores):
            linha = indice // 2
            coluna = indice % 2
            card = ctk.CTkFrame(grade, fg_color=CORES["fundo"], corner_radius=8)
            card.grid(row=linha, column=coluna, padx=6, pady=6, sticky="nsew")
            ctk.CTkLabel(
                card,
                text=rotulo,
                font=ctk.CTkFont(size=11),
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkLabel(
                card,
                text=valor,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=CORES["texto"],
                wraplength=400,
                justify="left",
            ).pack(anchor="w", padx=10, pady=(2, 10))

    def _montar_aba_periodos(
        self,
        aba: ctk.CTkFrame,
        periodos: list[PeriodoResultado],
        moeda: str,
        tipo: str,
    ) -> None:
        scroll = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        if not periodos:
            ctk.CTkLabel(
                scroll,
                text=f"Resultados por {tipo} nao disponiveis para este ativo.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=8, pady=8)
            return

        cabecalhos = ["Periodo", "Receita", "Lucro liquido", "EBITDA", "Lucro operacional"]
        adicionar_cabecalho_tabela(scroll, cabecalhos)

        for indice, item in enumerate(periodos):
            lucro_cor = CORES["texto"]
            if item.lucro_liquido is not None:
                lucro_cor = CORES["sucesso"] if item.lucro_liquido >= 0 else CORES["erro"]
            adicionar_linha_zebrada(
                scroll,
                [
                    item.periodo,
                    formatar_numero_grande(item.receita, moeda),
                    formatar_numero_grande(item.lucro_liquido, moeda),
                    formatar_numero_grande(item.ebitda, moeda),
                    formatar_numero_grande(item.lucro_operacional, moeda),
                ],
                indice,
                cores_celulas=[CORES["texto"], CORES["texto"], lucro_cor, CORES["texto"], CORES["texto"]],
            )

    def _montar_aba_demonstrativos(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Demonstrativos"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        secoes = [
            ("DRE trimestral", dados.dre_trimestral),
            ("DRE anual", dados.dre_anual),
            ("Balanco patrimonial (trimestral)", dados.balanco),
            ("Fluxo de caixa (trimestral)", dados.fluxo_caixa),
        ]
        for titulo, linhas in secoes:
            self._secao_demonstrativo(scroll, titulo, linhas, dados.moeda)

    def _secao_demonstrativo(
        self,
        pai: ctk.CTkScrollableFrame,
        titulo: str,
        linhas: list[LinhaDemonstrativo],
        moeda: str,
    ) -> None:
        ctk.CTkLabel(
            pai,
            text=titulo,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=4, pady=(12, 6))

        if not linhas:
            ctk.CTkLabel(
                pai,
                text="Sem dados para esta secao.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=8, pady=(0, 8))
            return

        periodos = list(linhas[0].valores.keys())
        adicionar_cabecalho_tabela(pai, ["Conta"] + periodos)

        for indice, linha in enumerate(linhas):
            valores = [formatar_numero_grande(linha.valores.get(p), moeda) for p in periodos]
            adicionar_linha_zebrada(pai, [linha.rotulo] + valores, indice, largura_wrap=200)

    def _montar_aba_concorrentes(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Concorrentes"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            scroll,
            text=(
                "Principais concorrentes do mesmo setor/industria (dados publicos). "
                "Lucro e receita em valor anualizado (TTM) quando disponivel."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=880,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

        if not dados.concorrentes:
            ctk.CTkLabel(
                scroll,
                text="Nenhum concorrente mapeado para esta industria.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=8)
            return

        cabecalhos = ["Codigo", "Empresa", "Lucro (TTM)", "Margem", "Receita (TTM)", "Cap. mercado"]
        adicionar_cabecalho_tabela(scroll, cabecalhos)

        for indice, item in enumerate(dados.concorrentes):
            lucro = item.lucro_liquido
            cor_lucro = CORES["texto"]
            if lucro is not None:
                cor_lucro = CORES["sucesso"] if lucro >= 0 else CORES["erro"]
            adicionar_linha_zebrada(
                scroll,
                [
                    item.codigo,
                    item.nome,
                    formatar_numero_grande(item.lucro_liquido, item.moeda),
                    formatar_percentual(item.margem_lucro),
                    formatar_numero_grande(item.receita, item.moeda),
                    formatar_numero_grande(item.capitalizacao, item.moeda),
                ],
                indice,
                cores_celulas=[
                    CORES["texto"],
                    CORES["texto"],
                    cor_lucro,
                    CORES["texto"],
                    CORES["texto"],
                    CORES["texto"],
                ],
            )

    @staticmethod
    def _linha_info(pai: ctk.CTkFrame, rotulo: str, valor: str) -> None:
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(
            linha,
            text=f"{rotulo}:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["textoSecundario"],
            width=120,
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            linha,
            text=valor,
            font=ctk.CTkFont(size=12),
            text_color=CORES["texto"],
            wraplength=700,
            justify="left",
        ).pack(side="left", fill="x", expand=True)
