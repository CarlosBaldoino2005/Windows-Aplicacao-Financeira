"""Janela com informacoes fundamentais e financeiras da acao."""
from __future__ import annotations

import webbrowser

import customtkinter as ctk

from typing import Any
from src.Model.detalhes_acao import DetalhesAcao, LinhaDemonstrativo, PeriodoResultado
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.View.formatadores import (
    formatar_moeda,
    formatar_numero_grande,
    formatar_percentual,
    formatar_texto_opcional,
    formatar_variacao,
)
from src.Model.explicacoes_indicadores import obter_explicacao_indicador
from src.View.janela_pesquisa_noticias import JanelaPesquisaNoticias
from src.View.tabela_detalhes_helper import adicionar_cabecalho_tabela, adicionar_linha_zebrada
from src.View.tema import CORES
from src.View.explicacao_indicador_helper import (
    GerenciadorExplicacaoIndicadores,
    adicionar_botao_explicacao_indicador,
)
from src.View.janela_informacoes_empresa import JanelaInformacoesEmpresa
from src.View.janela_opinioes_analistas import (
    ROTULOS_INDICADORES_ANALISTAS,
    abrir_janela_opinioes_analistas,
    adicionar_botao_opinioes_analistas,
)

NOMES_ABAS_ACAO = (
    "Empresa",
    "Indicadores",
    "Dividendos",
    "Trimestres",
    "Anuais",
    "Demonstrativos",
    "Concorrentes",
)

NOMES_ABAS_CRIPTO = (
    "Ativo",
    "Indicadores",
    "Outras criptos",
)


class JanelaDetalhesAcao(ctk.CTkToplevel):
    """Tela ampla com abas: empresa, indicadores, resultados e concorrentes."""

    def __init__(self, pai: ctk.CTk, controlador: Any, simbolo: str) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._modo_cripto = simbolo.endswith("-USD")
        self._nomes_abas = NOMES_ABAS_CRIPTO if self._modo_cripto else NOMES_ABAS_ACAO
        self._frames_por_aba: dict[str, ctk.CTkFrame] = {}
        self._botoes_aba: dict[str, ctk.CTkButton] = {}
        self._detalhes: DetalhesAcao | None = None
        self._janela_noticias: JanelaPesquisaNoticias | None = None
        self._gerenciador_explicacoes = GerenciadorExplicacaoIndicadores()
        self._janela_info_empresa: JanelaInformacoesEmpresa | None = None
        self._janela_grafico: ctk.CTkToplevel | None = None
        self._janela_opinioes_analistas: ctk.CTkToplevel | None = None

        codigo = simbolo.replace(".SA", "").replace("-USD", "")
        self.title(f"Mais detalhes — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(960, 640)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
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
            text=(
                "Buscando dados da criptomoeda no Yahoo Finance (pode levar alguns segundos)."
                if self._modo_cripto
                else "Buscando dados no Yahoo Finance (pode levar alguns segundos)."
            ),
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

        for nome in self._nomes_abas:
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
            text="Noticias",
            command=self._abrir_noticias,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="left")
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

    def _ao_fechar(self) -> None:
        self._gerenciador_explicacoes.fechar_todos()
        if self._janela_info_empresa is not None:
            try:
                if self._janela_info_empresa.winfo_exists():
                    self._janela_info_empresa.destroy()
            except Exception:
                pass
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        if self._janela_noticias is not None:
            try:
                if self._janela_noticias.winfo_exists():
                    self._janela_noticias.destroy()
            except Exception:
                pass
        if self._janela_opinioes_analistas is not None:
            try:
                if self._janela_opinioes_analistas.winfo_exists():
                    self._janela_opinioes_analistas.destroy()
            except Exception:
                pass
        self.destroy()

    def _termo_busca_noticias(self) -> str:
        if self._detalhes and self._detalhes.codigo:
            return self._detalhes.codigo.strip()
        return self._simbolo.replace(".SA", "").replace("-USD", "").strip()

    def _abrir_noticias(self) -> None:
        if self._janela_noticias is not None:
            try:
                if self._janela_noticias.winfo_exists():
                    self._janela_noticias.focus_force()
                    self._janela_noticias.lift()
                    return
            except Exception:
                pass

        termo = self._termo_busca_noticias()
        if len(termo) < 2:
            termo = self._simbolo.replace(".SA", "").replace("-USD", "")
        titulo = f"Noticias — {termo}"
        self._janela_noticias = JanelaPesquisaNoticias(
            self,
            self._controlador,
            modo_cripto=self._modo_cripto,
            termo_inicial=termo,
            titulo_personalizado=titulo,
            buscar_ao_abrir=True,
        )

    def _montar_barra_abas(self, pai: ctk.CTkFrame) -> None:
        grade = ctk.CTkFrame(pai, fg_color=CORES["borda"], corner_radius=10)
        grade.pack(fill="x", padx=0, pady=(0, 8))

        for coluna, nome in enumerate(self._nomes_abas):
            grade.columnconfigure(coluna, weight=1)
            botao = ctk.CTkButton(
                grade,
                text=nome,
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda n=nome: self._selecionar_aba(n),
                fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
                border_width=1,
                border_color=CORES["borda"],
            )
            botao.grid(row=0, column=coluna, padx=4, pady=4, sticky="ew")
            self._botoes_aba[nome] = botao

        self._selecionar_aba(self._nomes_abas[0])

    def _selecionar_aba(self, nome: str) -> None:
        self._gerenciador_explicacoes.fechar_todos()
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
                    fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
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
        executar_em_thread(self, funcao, ao_concluir)

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
        self._detalhes = dados
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

        if dados.eh_cripto or self._modo_cripto:
            self._montar_aba_ativo(dados)
            self._montar_aba_indicadores(dados)
            self._montar_aba_outras_criptos(dados)
        else:
            self._montar_aba_empresa(dados)
            self._montar_aba_indicadores(dados)
            self._montar_aba_dividendos(dados)
            self._montar_aba_periodos(
                self._frames_por_aba["Trimestres"], dados.trimestres, dados.moeda, "trimestre"
            )
            self._montar_aba_periodos(self._frames_por_aba["Anuais"], dados.anuais, dados.moeda, "ano")
            self._montar_aba_demonstrativos(dados)
            self._montar_aba_concorrentes(dados)
        self._selecionar_aba(self._nomes_abas[0])

    def _montar_aba_ativo(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Ativo"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        campos = [
            ("Nome", dados.nome_empresa),
            ("Codigo", dados.codigo),
            ("Par Yahoo", dados.simbolo),
            ("Categoria", dados.setor),
            ("Tipo", dados.industria),
            ("Site", dados.site),
        ]
        for rotulo, valor in campos:
            self._linha_info(scroll, rotulo, formatar_texto_opcional(valor))

        if dados.site:
            ctk.CTkButton(
                scroll,
                text="Abrir site do projeto",
                command=lambda url=dados.site: webbrowser.open(url),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=200,
            ).pack(anchor="w", padx=4, pady=(4, 12))

        ctk.CTkLabel(
            scroll,
            text="Sobre o ativo",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=4, pady=(8, 4))

        texto_desc = dados.descricao or "Descricao nao disponivel para esta criptomoeda."
        ctk.CTkLabel(
            scroll,
            text=texto_desc,
            font=ctk.CTkFont(size=12),
            text_color=CORES["texto"],
            wraplength=880,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

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
            self._linha_info(
                scroll,
                rotulo,
                formatar_texto_opcional(valor),
                fonte_maior=True,
            )

        ctk.CTkButton(
            scroll,
            text="Mais informacoes cadastrais",
            command=self._abrir_informacoes_empresa,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=220,
            height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=4, pady=(8, 4))

        if dados.site:
            ctk.CTkButton(
                scroll,
                text="Abrir site da empresa",
                command=lambda url=dados.site: webbrowser.open(url),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=200,
            ).pack(anchor="w", padx=4, pady=(4, 12))

        ctk.CTkLabel(
            scroll,
            text="Sobre a empresa",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=4, pady=(8, 4))

        texto_desc = dados.descricao or "Descricao nao disponivel para este ativo."
        ctk.CTkLabel(
            scroll,
            text=texto_desc,
            font=ctk.CTkFont(size=14),
            text_color=CORES["texto"],
            wraplength=880,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

    def _abrir_informacoes_empresa(self) -> None:
        if self._detalhes is None:
            return
        if self._janela_info_empresa is not None:
            try:
                if self._janela_info_empresa.winfo_exists():
                    self._janela_info_empresa.focus_force()
                    return
            except Exception:
                pass
        self._janela_info_empresa = JanelaInformacoesEmpresa(self, self._detalhes)

    def _abrir_opinioes_analistas(self) -> None:
        if self._detalhes is None:
            return
        if self._janela_opinioes_analistas is not None:
            try:
                if self._janela_opinioes_analistas.winfo_exists():
                    self._janela_opinioes_analistas.focus_force()
                    return
            except Exception:
                pass
        self._janela_opinioes_analistas = abrir_janela_opinioes_analistas(
            self,
            self._detalhes.simbolo,
            self._detalhes.nome_empresa,
            self._detalhes.moeda,
            self._detalhes.opinioes_analistas,
        )

    def _montar_aba_dividendos(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Dividendos"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            scroll,
            text=(
                "Pagamentos de dividendos por acao registrados no Yahoo Finance "
                "(valor creditado na data indicada)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=880,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

        pagamentos = dados.pagamentos_dividendos
        if not pagamentos:
            ctk.CTkLabel(
                scroll,
                text="Nenhum pagamento de dividendo encontrado para esta empresa.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=8, pady=8)
            return

        ultimo = pagamentos[0]
        destaque = ctk.CTkFrame(
            scroll,
            fg_color=CORES.get("destaqueDividendo", CORES.get("infoFundo", CORES["fundo"])),
            corner_radius=8,
        )
        destaque.pack(fill="x", padx=4, pady=(0, 10))
        ctk.CTkLabel(
            destaque,
            text="Ultimo dividendo pago",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            destaque,
            text=(
                f"{ultimo.data_pagamento} — "
                f"{formatar_moeda(ultimo.valor_por_cota, dados.moeda)} por acao"
            ),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["sucesso"],
        ).pack(anchor="w", padx=12, pady=(0, 10))

        total = sum(p.valor_por_cota for p in pagamentos)
        ctk.CTkLabel(
            scroll,
            text=(
                f"Historico: {len(pagamentos)} pagamentos — "
                f"soma: {formatar_moeda(total, dados.moeda)} por acao"
            ),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=4, pady=(0, 8))

        adicionar_cabecalho_tabela(scroll, ["Data do pagamento", "Valor por acao"])
        for indice, item in enumerate(pagamentos):
            adicionar_linha_zebrada(
                scroll,
                [
                    item.data_pagamento,
                    formatar_moeda(item.valor_por_cota, dados.moeda),
                ],
                indice,
                cores_celulas=[CORES["texto"], CORES["sucesso"]],
            )

    def _montar_aba_indicadores(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Indicadores"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            scroll,
            text=(
                "Clique no botao ? ao lado de cada indicador para ver o que ele significa. "
                "Nos indicadores com calculo, tambem mostramos os valores e a conta usada."
            ),
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

        grade = ctk.CTkFrame(scroll, fg_color="transparent")
        grade.pack(fill="x")
        grade.columnconfigure((0, 1), weight=1)

        for indice, (rotulo, valor) in enumerate(dados.indicadores):
            linha = indice // 2
            coluna = indice % 2
            card = ctk.CTkFrame(grade, fg_color=CORES["fundo"], corner_radius=8)
            card.grid(row=linha, column=coluna, padx=6, pady=6, sticky="nsew")

            explicacao = obter_explicacao_indicador(rotulo)
            calculo = dados.calculos_indicadores.get(rotulo)
            adicionar_botao_explicacao_indicador(
                card,
                rotulo,
                explicacao,
                self._gerenciador_explicacoes,
                calculo=calculo,
            )

            ctk.CTkLabel(
                card,
                text=valor,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=CORES["texto"],
                wraplength=400,
                justify="left",
            ).pack(anchor="w", padx=10, pady=(2, 10))

            if rotulo in ROTULOS_INDICADORES_ANALISTAS and not dados.eh_cripto:
                adicionar_botao_opinioes_analistas(card, self._abrir_opinioes_analistas)

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

    def _montar_aba_outras_criptos(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Outras criptos"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            scroll,
            text=(
                "Outras criptomoedas monitoradas no painel, com cotacao atual do Yahoo Finance. "
                "Duplo clique na linha abre o grafico da cripto."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=880,
            justify="left",
        ).pack(anchor="w", padx=4, pady=(0, 8))

        if not dados.concorrentes:
            ctk.CTkLabel(
                scroll,
                text="Nenhuma outra cripto listada no momento.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=8)
            return

        cabecalhos = ["Codigo", "Nome", "Preco", "Variacao dia"]
        adicionar_cabecalho_tabela(scroll, cabecalhos)

        for indice, item in enumerate(dados.concorrentes):
            variacao = (
                formatar_variacao(
                    (item.preco_atual or 0) * ((item.variacao_dia_pct or 0) / 100),
                    item.variacao_dia_pct or 0,
                    item.moeda,
                )
                if item.preco_atual is not None and item.variacao_dia_pct is not None
                else "—"
            )
            cor_var = CORES["texto"]
            if item.variacao_dia_pct is not None:
                cor_var = CORES["sucesso"] if item.variacao_dia_pct >= 0 else CORES["erro"]
            simbolo = self._simbolo_yahoo_concorrente(item.codigo)
            adicionar_linha_zebrada(
                scroll,
                [
                    item.codigo,
                    item.nome,
                    formatar_moeda(item.preco_atual, item.moeda),
                    variacao,
                ],
                indice,
                cores_celulas=[CORES["texto"], CORES["texto"], CORES["texto"], cor_var],
                ao_duplo_clique=lambda s=simbolo: self._abrir_grafico_ativo(s),
            )

    def _montar_aba_concorrentes(self, dados: DetalhesAcao) -> None:
        scroll = ctk.CTkScrollableFrame(self._frames_por_aba["Concorrentes"], fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(
            scroll,
            text=(
                "Principais concorrentes do mesmo setor/industria (dados publicos). "
                "Lucro e receita em valor anualizado (TTM) quando disponivel. "
                "Duplo clique na linha abre o grafico do ativo."
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
            simbolo = self._simbolo_yahoo_concorrente(item.codigo)
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
                ao_duplo_clique=lambda s=simbolo: self._abrir_grafico_ativo(s),
            )

    def _simbolo_yahoo_concorrente(self, codigo: str) -> str:
        """Monta ticker Yahoo do concorrente conforme o tipo do ativo atual."""
        limpo = codigo.replace(".SA", "").replace("-USD", "")
        if self._modo_cripto:
            return f"{limpo}-USD"
        if self._simbolo.endswith(".SA"):
            return f"{limpo}.SA"
        return limpo

    def _abrir_grafico_ativo(self, simbolo: str) -> None:
        from src.View.janela_grafico_acao import JanelaGraficoAcao

        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        self._janela_grafico = JanelaGraficoAcao(self, self._controlador, simbolo)
        codigo = simbolo.replace(".SA", "").replace("-USD", "")
        self._janela_grafico.title(f"Grafico — {codigo}")

    @staticmethod
    def _linha_info(
        pai: ctk.CTkFrame,
        rotulo: str,
        valor: str,
        fonte_maior: bool = False,
    ) -> None:
        tamanho_rotulo = 14 if fonte_maior else 12
        tamanho_valor = 15 if fonte_maior else 12
        largura_rotulo = 140 if fonte_maior else 120

        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=4, pady=3 if fonte_maior else 2)
        ctk.CTkLabel(
            linha,
            text=f"{rotulo}:",
            font=ctk.CTkFont(size=tamanho_rotulo, weight="bold"),
            text_color=CORES["textoSecundario"],
            width=largura_rotulo,
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            linha,
            text=valor,
            font=ctk.CTkFont(size=tamanho_valor),
            text_color=CORES["texto"],
            wraplength=700,
            justify="left",
        ).pack(side="left", fill="x", expand=True)
