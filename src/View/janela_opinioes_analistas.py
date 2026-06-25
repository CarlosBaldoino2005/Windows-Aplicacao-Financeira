"""Janela com opinioes e recomendacoes de analistas sobre a acao."""
from __future__ import annotations

import customtkinter as ctk

from src.Model.opinioes_analistas import OpinioesAnalistasPacote
from src.Tool.cotacao_dual_helper import codigo_exibicao, rotulo_tipo_ativo
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.Tool.opinioes_analistas_helper import montar_opinioes_analistas
from src.View.formatadores import formatar_moeda, formatar_texto_opcional
from src.View.painel_carregamento_helper import montar_painel_carregamento, parar_painel_carregamento
from src.View.tabela_detalhes_helper import adicionar_cabecalho_tabela, adicionar_linha_zebrada
from src.View.tema import CORES

ROTULOS_INDICADORES_ANALISTAS = frozenset(
    {
        "Recomendacao analistas",
        "Opinioes de analistas",
        "Preco alvo medio",
    }
)


class JanelaOpinioesAnalistas(ctk.CTkToplevel):
    """Exibe resumo, distribuicao e movimentos recentes dos analistas."""

    def __init__(
        self,
        pai: ctk.CTk,
        simbolo: str,
        nome_empresa: str,
        moeda: str,
        pacote_inicial: OpinioesAnalistasPacote | None = None,
    ) -> None:
        super().__init__(pai)
        self._simbolo = simbolo
        self._nome_empresa = nome_empresa
        self._moeda = moeda
        self._pacote = pacote_inicial
        self._barra_carregamento = None

        codigo = simbolo.replace(".SA", "").replace("-USD", "")
        self.title(f"Opinioes dos analistas — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(820, 560)

        self._montar_esqueleto(codigo)
        self._exibir_carregando()

        def _iniciar_apos_janela_visivel() -> None:
            if not janela_ui_ainda_ativa(self):
                return
            if self._pacote is not None:
                self._exibir_pacote()
                return
            self._carregar_em_thread()

        configurar_janela_maximizada(
            self,
            janela_pai=pai,
            ao_apos_layout=_iniciar_apos_janela_visivel,
        )
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._garantir_janela_visivel(pai)

    def _garantir_janela_visivel(self, pai: ctk.CTk) -> None:
        """Mantem a janela visivel enquanto o layout e a busca de dados acontecem."""
        try:
            self.deiconify()
            self.lift(pai)
            self.focus_force()
            self.update_idletasks()
        except Exception:
            pass

    def _montar_esqueleto(self, codigo: str) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            cabecalho,
            text=f"Opinioes dos analistas — {codigo}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text="Consolidacao e movimentos recentes obtidos do Yahoo Finance quando disponiveis.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self._frame_conteudo = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        self._frame_conteudo.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self._frame_conteudo.grid_rowconfigure(0, weight=1)
        self._frame_conteudo.grid_columnconfigure(0, weight=1)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self.destroy,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

    def _limpar_conteudo(self) -> None:
        parar_painel_carregamento(self._barra_carregamento)
        self._barra_carregamento = None
        for widget in self._frame_conteudo.winfo_children():
            widget.destroy()

    def _exibir_carregando(self) -> None:
        self._limpar_conteudo()
        _, self._barra_carregamento, _ = montar_painel_carregamento(
            self._frame_conteudo,
            titulo="Carregando opinioes dos analistas...",
            detalhe=(
                "Buscando recomendacoes e precos-alvo no Yahoo Finance. "
                "Isso pode levar alguns segundos — aguarde nesta tela."
            ),
        )
        try:
            self.lift(self.master.winfo_toplevel())
            self.update_idletasks()
        except Exception:
            pass

    def _carregar_em_thread(self) -> None:
        executar_em_thread(
            self,
            lambda: montar_opinioes_analistas(self._simbolo, self._nome_empresa, self._moeda),
            self._ao_carregar,
        )

    def _ao_carregar(self, pacote: OpinioesAnalistasPacote | None, erro: str | None) -> None:
        if not janela_ui_ainda_ativa(self):
            return
        if erro:
            self._exibir_sem_dados(
                f"Erro ao carregar: {erro}",
                cor=CORES["erro"],
            )
            return
        if pacote is None:
            self._exibir_sem_dados(
                self._montar_mensagem_sem_dados(),
            )
            return
        self._pacote = pacote
        self._exibir_pacote()

    def _montar_mensagem_sem_dados(self) -> str:
        codigo = codigo_exibicao(self._simbolo)
        tipo = rotulo_tipo_ativo(self._simbolo)
        linhas = [
            f"Nenhuma opiniao de analista disponivel para {codigo}.",
            "",
            f"Tipo do ativo: {tipo}.",
            "",
            "O Yahoo Finance nao publica recomendacoes nem precos-alvo para este papel.",
        ]
        if self._simbolo.endswith("-USD"):
            linhas.append("Criptomoedas em geral nao possuem cobertura de analistas nesta fonte.")
        elif tipo == "Fundo imobiliario":
            linhas.append("FIIs costumam nao ter consenso de analistas no Yahoo Finance.")
        elif tipo == "ETF":
            linhas.append("ETFs podem nao ter precos-alvo de analistas individuais.")
        linhas.extend(
            [
                "",
                "Use a opcao Analisar com IA na tela Analise para uma visao alternativa.",
            ]
        )
        return "\n".join(linhas)

    def _exibir_sem_dados(self, texto: str, *, cor: str | None = None) -> None:
        self._limpar_conteudo()

        ctk.CTkLabel(
            self._frame_conteudo,
            text=texto,
            font=ctk.CTkFont(size=14),
            text_color=cor or CORES["textoSecundario"],
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(anchor="w", padx=4, pady=20)

    def _exibir_pacote(self) -> None:
        self._limpar_conteudo()

        pacote = self._pacote
        if pacote is None:
            return

        scroll = ctk.CTkScrollableFrame(self._frame_conteudo, fg_color=CORES["superficie"], corner_radius=12)
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text=f"{pacote.codigo} — {pacote.nome_empresa}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        for aviso in pacote.avisos:
            ctk.CTkLabel(
                scroll,
                text=aviso,
                font=ctk.CTkFont(size=12),
                text_color=CORES["aviso"],
                wraplength=900,
                justify="left",
            ).pack(anchor="w", padx=12, pady=(0, 6))

        self._secao_resumo(scroll, pacote)
        self._secao_distribuicao(scroll, pacote)
        self._secao_historico(scroll, pacote)
        self._secao_movimentos(scroll, pacote)

    def _titulo_secao(self, pai: ctk.CTkFrame, texto: str) -> None:
        ctk.CTkLabel(
            pai,
            text=texto,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(16, 8))

    def _linha_resumo(self, pai: ctk.CTkFrame, rotulo: str, valor: str) -> None:
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=12, pady=3)
        ctk.CTkLabel(
            linha,
            text=rotulo,
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
            width=220,
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            linha,
            text=valor,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
            justify="left",
        ).pack(side="left", fill="x", expand=True)

    def _secao_resumo(self, pai: ctk.CTkScrollableFrame, pacote: OpinioesAnalistasPacote) -> None:
        resumo = pacote.resumo
        self._titulo_secao(pai, "Resumo da recomendacao")

        bloco = ctk.CTkFrame(pai, fg_color=CORES["fundo"], corner_radius=10)
        bloco.pack(fill="x", padx=12, pady=(0, 8))

        media_txt = "—"
        if resumo.recomendacao_media is not None:
            media_txt = f"{resumo.recomendacao_media:.2f}"

        tem_campo = False
        if resumo.recomendacao_texto and resumo.recomendacao_texto != "—":
            self._linha_resumo(bloco, "Recomendacao geral", formatar_texto_opcional(resumo.recomendacao_texto))
            tem_campo = True
        if resumo.recomendacao_media is not None:
            self._linha_resumo(bloco, "Nota media (1 a 5)", media_txt)
            tem_campo = True
        if resumo.nota_media_descricao:
            self._linha_resumo(bloco, "Descricao da media", resumo.nota_media_descricao)
            tem_campo = True
        if resumo.quantidade_analistas is not None:
            self._linha_resumo(bloco, "Analistas com opiniao", str(resumo.quantidade_analistas))
            tem_campo = True
        if resumo.preco_alvo_min is not None:
            self._linha_resumo(bloco, "Preco alvo minimo", formatar_moeda(resumo.preco_alvo_min, pacote.moeda))
            tem_campo = True
        if resumo.preco_alvo_mediano is not None:
            self._linha_resumo(bloco, "Preco alvo mediano", formatar_moeda(resumo.preco_alvo_mediano, pacote.moeda))
            tem_campo = True
        if resumo.preco_alvo_medio is not None:
            self._linha_resumo(bloco, "Preco alvo medio", formatar_moeda(resumo.preco_alvo_medio, pacote.moeda))
            tem_campo = True
        if resumo.preco_alvo_max is not None:
            self._linha_resumo(bloco, "Preco alvo maximo", formatar_moeda(resumo.preco_alvo_max, pacote.moeda))
            tem_campo = True

        if not tem_campo:
            self._linha_resumo(
                bloco,
                "Situacao",
                "Sem dados consolidados de analistas para este ativo na fonte consultada.",
            )

    def _secao_distribuicao(self, pai: ctk.CTkScrollableFrame, pacote: OpinioesAnalistasPacote) -> None:
        resumo = pacote.resumo
        total = resumo.compra_forte + resumo.comprar + resumo.manter + resumo.vender + resumo.venda_forte
        if total <= 0:
            return

        self._titulo_secao(pai, "Distribuicao atual das opinioes")
        bloco = ctk.CTkFrame(pai, fg_color=CORES["fundo"], corner_radius=10)
        bloco.pack(fill="x", padx=12, pady=(0, 8))

        itens = [
            ("Compra forte", resumo.compra_forte, CORES["sucesso"]),
            ("Comprar", resumo.comprar, CORES["sucesso"]),
            ("Manter", resumo.manter, CORES["texto"]),
            ("Vender", resumo.vender, CORES["erro"]),
            ("Venda forte", resumo.venda_forte, CORES["erro"]),
        ]
        for rotulo, quantidade, cor in itens:
            if quantidade <= 0:
                continue
            pct = (quantidade / total) * 100
            self._linha_resumo(bloco, rotulo, f"{quantidade} analista(s) — {pct:.0f}%")

    def _secao_historico(self, pai: ctk.CTkScrollableFrame, pacote: OpinioesAnalistasPacote) -> None:
        if not pacote.historico:
            return

        self._titulo_secao(pai, "Historico mensal de recomendacoes")
        tabela = ctk.CTkFrame(pai, fg_color="transparent")
        tabela.pack(fill="x", padx=12, pady=(0, 8))
        adicionar_cabecalho_tabela(
            tabela,
            ["Periodo", "Compra forte", "Comprar", "Manter", "Vender", "Venda forte"],
        )
        for indice, item in enumerate(pacote.historico[:8]):
            adicionar_linha_zebrada(
                tabela,
                [
                    item.periodo,
                    str(item.compra_forte),
                    str(item.comprar),
                    str(item.manter),
                    str(item.vender),
                    str(item.venda_forte),
                ],
                indice,
            )

    def _secao_movimentos(self, pai: ctk.CTkScrollableFrame, pacote: OpinioesAnalistasPacote) -> None:
        if not pacote.movimentos:
            return

        self._titulo_secao(pai, "Movimentos recentes por instituicao")
        tabela = ctk.CTkFrame(pai, fg_color="transparent")
        tabela.pack(fill="x", padx=12, pady=(0, 16))
        adicionar_cabecalho_tabela(
            tabela,
            ["Data", "Instituicao", "Nota anterior", "Nota nova", "Acao", "Preco alvo"],
        )
        for indice, item in enumerate(pacote.movimentos):
            moeda_mov = pacote.moeda_movimentos or pacote.moeda
            preco = "—"
            if item.preco_alvo is not None:
                preco = formatar_moeda(item.preco_alvo, moeda_mov)
                if item.preco_alvo_anterior is not None:
                    preco += f" (antes {formatar_moeda(item.preco_alvo_anterior, moeda_mov)})"
            adicionar_linha_zebrada(
                tabela,
                [
                    item.data,
                    item.instituicao,
                    item.nota_anterior,
                    item.nota_nova,
                    item.acao,
                    preco,
                ],
                indice,
                largura_wrap=180,
            )


def abrir_janela_opinioes_analistas(
    pai: ctk.CTk,
    simbolo: str,
    nome_empresa: str,
    moeda: str,
    pacote: OpinioesAnalistasPacote | None = None,
) -> JanelaOpinioesAnalistas:
    return JanelaOpinioesAnalistas(pai, simbolo, nome_empresa, moeda, pacote)


def adicionar_botao_opinioes_analistas(card: ctk.CTkFrame, comando) -> None:
    """Botao auxiliar no card do indicador de analistas."""
    ctk.CTkButton(
        card,
        text="Ver opinioes dos analistas",
        height=28,
        font=ctk.CTkFont(size=12),
        fg_color=CORES["primaria"],
        hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        command=comando,
    ).pack(anchor="w", padx=10, pady=(0, 10))
