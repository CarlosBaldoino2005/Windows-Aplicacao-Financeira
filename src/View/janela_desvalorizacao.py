"""Tela que mostra a ultima desvalorizacao no periodo do grafico."""
from __future__ import annotations

from typing import Any

import customtkinter as ctk

from src.Model.desvalorizacao import AnaliseDesvalorizacao, EventoDesvalorizacao
from src.Model.periodos_mercado import PERIODOS_MERCADO, rotulo_periodo_por_chave
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.grid_ordenacao_helper import EstadoOrdenacaoColuna, LinhaTabelaOrdenavel
from src.View.tabela_detalhes_helper import renderizar_tabela_zebrada
from src.View.tema import CORES

PERIODOS = PERIODOS_MERCADO


class JanelaDesvalorizacao(ctk.CTkToplevel):
    """Busca quedas de preco (pico → fundo) no periodo escolhido."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: Any,
        simbolo: str,
        periodo_chave: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._simbolo = simbolo
        self._modo_cripto = simbolo.endswith("-USD")
        self._ordenacao_eventos = EstadoOrdenacaoColuna()
        self._analise_eventos: AnaliseDesvalorizacao | None = None

        codigo = simbolo.replace(".SA", "").replace("-USD", "")
        self.title(f"Desvalorizacao — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(820, 520)

        self._montar_interface()
        if periodo_chave:
            self._combo_periodo.set(rotulo_periodo_por_chave(periodo_chave))
            self._alternar_datas()
        if data_inicio:
            self._entrada_inicio.delete(0, "end")
            self._entrada_inicio.insert(0, data_inicio.strip())
        if data_fim:
            self._entrada_fim.delete(0, "end")
            self._entrada_fim.insert(0, data_fim.strip())

        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._buscar_desvalorizacao)

    def _ao_fechar(self) -> None:
        self.destroy()

    def _montar_interface(self) -> None:
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(side="top", fill="x")

        codigo = self._simbolo.replace(".SA", "").replace("-USD", "")
        tipo = "criptomoeda" if self._modo_cripto else "acao"
        self._label_titulo = ctk.CTkLabel(
            cabecalho,
            text=f"Ultima desvalorizacao — {codigo}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        )
        self._label_titulo.pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                f"Analisa o historico da {tipo} no periodo escolhido e identifica quedas "
                "do topo local ate o fundo seguinte. A ultima queda aparece em destaque."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=780,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(barra, text="Periodo").pack(side="left", padx=(0, 8))
        self._combo_periodo = ctk.CTkComboBox(
            barra,
            values=[p[1] for p in PERIODOS],
            width=140,
            command=self._alternar_datas,
        )
        self._combo_periodo.set("Mes")
        self._combo_periodo.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            barra,
            text="Buscar desvalorizacao",
            command=self._buscar_desvalorizacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="left")

        self._frame_datas = ctk.CTkFrame(cabecalho, fg_color="transparent")
        ctk.CTkLabel(self._frame_datas, text="Inicio (dd/mm/aaaa)").pack(side="left", padx=16)
        self._entrada_inicio = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_inicio.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(self._frame_datas, text="Fim (dd/mm/aaaa)").pack(side="left")
        self._entrada_fim = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_fim.pack(side="left", padx=8)

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(anchor="w", padx=16, pady=(0, 12))

        self._painel = ctk.CTkScrollableFrame(
            self,
            fg_color=CORES["superficie"],
            corner_radius=12,
            label_text="Resultado",
        )
        self._painel.pack(fill="both", expand=True, padx=16, pady=(8, 8))

    def _periodo_chave(self) -> str:
        rotulo = self._combo_periodo.get()
        for chave, nome in PERIODOS:
            if nome == rotulo:
                return chave
        return "mes"

    def _alternar_datas(self, _valor=None) -> None:
        if self._periodo_chave() == "personalizado":
            self._frame_datas.pack(fill="x", pady=(0, 8))
        else:
            self._frame_datas.pack_forget()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _buscar_desvalorizacao(self) -> None:
        self._label_status.configure(text="Buscando historico e analisando quedas...")
        self._limpar_painel()
        periodo = self._periodo_chave()

        def buscar():
            return self._controlador.obter_desvalorizacoes_periodo(
                self._simbolo,
                periodo,
                self._entrada_inicio.get(),
                self._entrada_fim.get(),
            )

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                self._exibir_instrucao(erro)
                return
            analise, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                self._exibir_instrucao(msg_erro)
                return
            if analise is None:
                self._label_status.configure(
                    text="Nao foi possivel analisar o periodo.",
                    text_color=CORES["erro"],
                )
                self._exibir_instrucao("Nao foi possivel analisar o periodo.")
                return
            self._exibir_analise(analise)
            self._label_status.configure(
                text="Analise concluida.",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _limpar_painel(self) -> None:
        for widget in self._painel.winfo_children():
            widget.destroy()

    def _exibir_instrucao(self, texto: str) -> None:
        ctk.CTkLabel(
            self._painel,
            text=texto,
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
            wraplength=760,
            justify="left",
        ).pack(anchor="w", padx=12, pady=12)

    def _exibir_analise(self, analise: AnaliseDesvalorizacao) -> None:
        self._limpar_painel()
        ultima = analise.ultima
        if ultima is None:
            self._exibir_instrucao(
                f"Nenhuma desvalorizacao identificada no periodo {analise.periodo_rotulo}. "
                "O preco pode ter subido ou permanecido estavel."
            )
            return

        self._painel.configure(
            label_text=f"Periodo: {analise.periodo_rotulo} — ultima queda em destaque"
        )
        self._montar_card_destaque(analise, ultima)

        if len(analise.eventos) > 1:
            ctk.CTkLabel(
                self._painel,
                text="Outras desvalorizacoes no mesmo periodo",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=CORES["texto"],
            ).pack(anchor="w", padx=12, pady=(16, 8))
            self._montar_tabela_eventos(analise, destacar_ultima=True)

    def _montar_card_destaque(
        self,
        analise: AnaliseDesvalorizacao,
        evento: EventoDesvalorizacao,
    ) -> None:
        card = ctk.CTkFrame(self._painel, fg_color=CORES["fundo"], corner_radius=10)
        card.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(
            card,
            text=f"Ultima desvalorizacao — {analise.codigo_exibicao}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CORES["primaria"],
        ).pack(anchor="w", padx=12, pady=(12, 8))

        linhas = (
            ("Topo (pico)", evento.data_pico, formatar_moeda(evento.preco_pico, analise.moeda)),
            ("Fundo (menor preco)", evento.data_fundo, formatar_moeda(evento.preco_fundo, analise.moeda)),
            (
                "Queda no intervalo",
                f"{evento.pregões} pregão(ões)",
                formatar_variacao(evento.variacao_valor, evento.variacao_percentual, analise.moeda),
            ),
        )
        for rotulo, coluna_meio, coluna_fim in linhas:
            linha = ctk.CTkFrame(card, fg_color="transparent")
            linha.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(
                linha,
                text=rotulo,
                width=180,
                anchor="w",
                text_color=CORES["textoSecundario"],
            ).pack(side="left")
            ctk.CTkLabel(
                linha,
                text=coluna_meio,
                width=160,
                anchor="w",
                text_color=CORES["texto"],
            ).pack(side="left", padx=(0, 12))
            ctk.CTkLabel(
                linha,
                text=coluna_fim,
                anchor="w",
                text_color=CORES["erro"] if "Queda" in rotulo else CORES["texto"],
                font=ctk.CTkFont(weight="bold") if "Queda" in rotulo else ctk.CTkFont(),
            ).pack(side="left")

        ctk.CTkLabel(card, text="").pack(pady=4)

    def _montar_tabela_eventos(
        self,
        analise: AnaliseDesvalorizacao,
        destacar_ultima: bool = False,
    ) -> None:
        self._analise_eventos = analise
        self._destacar_ultimo_evento = destacar_ultima

        tabela = ctk.CTkFrame(self._painel, fg_color="transparent")
        tabela.pack(fill="x", padx=12, pady=(0, 12))
        self._frame_tabela_eventos = tabela
        self._redesenhar_tabela_eventos()

    def _redesenhar_tabela_eventos(self) -> None:
        analise = self._analise_eventos
        tabela = getattr(self, "_frame_tabela_eventos", None)
        if analise is None or tabela is None:
            return

        for widget in tabela.winfo_children():
            widget.destroy()

        colunas = ("Pico", "Fundo", "Preco pico", "Preco fundo", "Queda %", "Pregões")
        linhas: list[LinhaTabelaOrdenavel] = []
        destacar_ultima = getattr(self, "_destacar_ultimo_evento", False)

        for indice, evento in enumerate(analise.eventos):
            valores = [
                evento.data_pico,
                evento.data_fundo,
                formatar_moeda(evento.preco_pico, analise.moeda),
                formatar_moeda(evento.preco_fundo, analise.moeda),
                f"{evento.variacao_percentual:.2f}%",
                str(evento.pregões),
            ]
            cor_queda = CORES["erro"]
            cores = [CORES["texto"]] * 4 + [cor_queda, CORES["texto"]]
            if destacar_ultima and indice == len(analise.eventos) - 1:
                cores = [CORES["primaria"]] * len(valores)
            linhas.append(
                LinhaTabelaOrdenavel(
                    valores=valores,
                    chaves=[
                        evento.data_pico,
                        evento.data_fundo,
                        evento.preco_pico,
                        evento.preco_fundo,
                        evento.variacao_percentual,
                        evento.pregões,
                    ],
                    cores_celulas=cores,
                )
            )

        renderizar_tabela_zebrada(
            tabela,
            list(colunas),
            linhas,
            self._ordenacao_eventos,
            self._redesenhar_tabela_eventos,
            nome_arquivo_exportacao="desvalorizacao",
        )
