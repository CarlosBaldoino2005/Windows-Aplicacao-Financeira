"""Janela dedicada para pesquisar uma acao e ver cotacao."""
from __future__ import annotations

from src.View import mensagem_helper as messagebox

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Model.cotacao import CotacaoResumo
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.placeholders_ui import PLACEHOLDER_BUSCA_ACAO, PLACEHOLDER_BUSCA_CRIPTO
from src.View.janela_detalhes_acao import JanelaDetalhesAcao
from src.View.janela_grafico_acao import JanelaGraficoAcao
from src.View.tema import CORES


class JanelaPesquisaAcao(ctk.CTkToplevel):
    """Tela de pesquisa com informacoes da acao; grafico abre em janela separada."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorMercado,
        modo_cripto: bool = False,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._modo_cripto = modo_cripto
        self._simbolo_atual: str | None = None
        self._janela_grafico: JanelaGraficoAcao | None = None
        self._janela_detalhes: JanelaDetalhesAcao | None = None
        self._labels_info: dict[str, ctk.CTkLabel] = {}

        self.title("Pesquisar criptomoeda" if modo_cripto else "Pesquisar acao")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(720, 520)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _ao_fechar(self) -> None:
        for janela in (self._janela_grafico, self._janela_detalhes):
            if janela is None:
                continue
            try:
                if janela.winfo_exists():
                    if hasattr(janela, "_ao_fechar"):
                        janela._ao_fechar()
                    else:
                        janela.destroy()
            except Exception:
                pass
        self.destroy()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Pesquisar criptomoeda" if self._modo_cripto else "Pesquisar acao",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Busque por nome ou codigo (ex.: BTC, Bitcoin) e clique em Ver para abrir o grafico."
                if self._modo_cripto
                else "Busque por nome ou codigo e clique em Ver para abrir o grafico da acao."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        linha_busca = ctk.CTkFrame(cabecalho, fg_color="transparent")
        linha_busca.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(linha_busca, text="Codigo ou nome").pack(side="left", padx=(0, 8))
        self._entrada_busca = ctk.CTkEntry(
            linha_busca,
            width=320,
            placeholder_text=(
                PLACEHOLDER_BUSCA_CRIPTO if self._modo_cripto else PLACEHOLDER_BUSCA_ACAO
            ),
        )
        self._entrada_busca.pack(side="left", padx=(0, 8))
        self._entrada_busca.bind("<Return>", lambda _e: self._pesquisar())

        ctk.CTkButton(
            linha_busca,
            text="Buscar",
            command=self._pesquisar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            linha_busca,
            text="Consultar codigo",
            command=self._consultar_direto,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(side="left")

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(anchor="w", padx=16, pady=(0, 4))

        self._frame_resultados = ctk.CTkScrollableFrame(
            cabecalho, height=120, fg_color=CORES["fundo"], label_text="Resultados da busca"
        )
        self._frame_resultados.pack(fill="x", padx=16, pady=(0, 12))

        self._frame_info = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._frame_info.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self._montar_cards_info()

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(
            rodape,
            text="Abrir grafico",
            command=self._abrir_janela_grafico,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=160,
            height=36,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            rodape,
            text="Mais detalhes",
            command=self._abrir_mais_detalhes,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=160,
            height=36,
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

    def _montar_cards_info(self) -> None:
        titulo = ctk.CTkLabel(
            self._frame_info,
            text="Informacoes da acao",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        )
        titulo.pack(anchor="w", padx=12, pady=(12, 8))

        grid = ctk.CTkFrame(self._frame_info, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))

        campos = [
            ("codigo", "Acao"),
            ("nome", "Nome"),
            ("preco", "Preco atual"),
            ("variacao", "Variacao do dia"),
            ("volume", "Volume"),
        ]
        for i, (chave, rotulo) in enumerate(campos):
            col = i % 3
            lin = i // 3
            card = ctk.CTkFrame(grid, fg_color=CORES["fundo"], corner_radius=8)
            card.grid(row=lin, column=col, padx=6, pady=6, sticky="nsew")
            grid.grid_columnconfigure(col, weight=1)

            ctk.CTkLabel(
                card,
                text=rotulo,
                font=ctk.CTkFont(size=11),
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=10, pady=(8, 0))

            valor = ctk.CTkLabel(
                card,
                text="—",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=CORES["texto"],
            )
            valor.pack(anchor="w", padx=10, pady=(0, 10))
            self._labels_info[chave] = valor

    def _limpar_resultados(self) -> None:
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _pesquisar(self) -> None:
        termo = self._entrada_busca.get().strip()
        if not termo:
            messagebox.showwarning("Buscar", "Digite o nome ou codigo da acao.", parent=self)
            return

        self._label_status.configure(text="Buscando acoes...")

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
                text=f"{len(itens)} resultado(s). Clique em Ver na acao desejada.",
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
                text="Ver",
                width=80,
                command=lambda s=item.simbolo: self._selecionar_acao(s, abrir_analise=True),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(side="right", padx=8, pady=4)

    def _normalizar_entrada(self, termo: str):
        if self._modo_cripto:
            return normalizar_simbolo_cripto(termo)
        return normalizar_simbolo(termo)

    def _codigo_exibicao(self, simbolo: str) -> str:
        if self._modo_cripto:
            return simbolo.replace("-USD", "")
        return simbolo.replace(".SA", "")

    def _consultar_direto(self) -> None:
        termo = self._entrada_busca.get().strip()
        if not termo:
            aviso = "Digite o codigo da criptomoeda." if self._modo_cripto else "Digite o codigo da acao."
            messagebox.showwarning("Consultar", aviso, parent=self)
            return
        simbolo, erro = self._normalizar_entrada(termo)
        if erro:
            messagebox.showwarning("Consultar", erro, parent=self)
            return
        self._selecionar_acao(simbolo)

    def _selecionar_acao(self, simbolo: str, *, abrir_analise: bool = False) -> None:
        simbolo_ok, erro = self._normalizar_entrada(simbolo)
        if erro:
            titulo = "Cripto" if self._modo_cripto else "Acao"
            messagebox.showwarning(titulo, erro, parent=self)
            return

        self._simbolo_atual = simbolo_ok
        codigo = self._codigo_exibicao(simbolo_ok)
        self._entrada_busca.delete(0, "end")
        self._entrada_busca.insert(0, codigo)
        titulo_janela = "Pesquisar criptomoeda" if self._modo_cripto else "Pesquisar acao"
        self.title(f"{titulo_janela} — {codigo}")
        self._label_status.configure(text="Carregando cotacao...")

        def buscar():
            return self._controlador.obter_cotacao(simbolo_ok)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                messagebox.showwarning("Acao", erro, parent=self)
                return
            cotacao, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                messagebox.showwarning("Acao", msg_erro, parent=self)
                return
            self._exibir_info(cotacao)
            if abrir_analise:
                self._abrir_janela_grafico()
                self._label_status.configure(
                    text=f"Dados de {codigo} carregados. Grafico aberto em nova janela.",
                    text_color=CORES["sucesso"],
                )
            else:
                self._label_status.configure(
                    text=f"Dados de {codigo} carregados. Use Abrir grafico ou Mais detalhes para analisar.",
                    text_color=CORES["sucesso"],
                )

        self._executar_em_thread(buscar, ao_concluir)

    def _exibir_info(self, cotacao: CotacaoResumo) -> None:
        codigo = self._codigo_exibicao(cotacao.simbolo)
        volume_txt = "—"
        if cotacao.volume is not None:
            volume_txt = f"{cotacao.volume:,}".replace(",", ".")

        self._labels_info["codigo"].configure(text=codigo)
        self._labels_info["nome"].configure(text=cotacao.nome or "—")
        self._labels_info["preco"].configure(text=formatar_moeda(cotacao.preco, cotacao.moeda))
        self._labels_info["variacao"].configure(
            text=formatar_variacao(cotacao.variacao_valor, cotacao.variacao_percentual, cotacao.moeda)
        )
        self._labels_info["volume"].configure(text=volume_txt)

    def _abrir_janela_grafico(self) -> None:
        if not self._simbolo_atual:
            messagebox.showinfo(
                "Grafico",
                "Selecione uma acao nos resultados ou consulte um codigo antes.",
                parent=self,
            )
            return

        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass

        self._janela_grafico = JanelaGraficoAcao(self, self._controlador, self._simbolo_atual)
        self._label_status.configure(
            text="Grafico aberto em nova janela.",
            text_color=CORES["sucesso"],
        )

    def _abrir_mais_detalhes(self) -> None:
        if not self._simbolo_atual:
            messagebox.showinfo(
                "Mais detalhes",
                "Selecione uma acao nos resultados ou consulte um codigo antes.",
                parent=self,
            )
            return

        if self._janela_detalhes is not None:
            try:
                if self._janela_detalhes.winfo_exists():
                    self._janela_detalhes.focus_force()
                    return
            except Exception:
                pass

        self._janela_detalhes = JanelaDetalhesAcao(self, self._controlador, self._simbolo_atual)
        self._label_status.configure(
            text="Mais detalhes aberto em nova janela.",
            text_color=CORES["sucesso"],
        )
