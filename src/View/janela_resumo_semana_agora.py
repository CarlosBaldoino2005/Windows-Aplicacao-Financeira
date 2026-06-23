"""Janela com metricas dos ultimos trinta dias uteis do ativo (tela Agora)."""
from __future__ import annotations

import customtkinter as ctk

from src.Model.resumo_semana_agora import ResumoSemanaAgora
from src.Service.resumo_semana_agora_servico import ResumoSemanaAgoraServico
from src.Tool.cotacao_dual_helper import codigo_exibicao, rotulo_tipo_ativo
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.tabela_resumo_semana_agora_helper import (
    criar_grid_resumo_semana_agora,
    liberar_grid_resumo_semana_agora,
    preencher_grid_resumo_semana_agora,
)
from src.View.tema import CORES


class JanelaResumoSemanaAgora(ctk.CTkToplevel):
    """Exibe OHLCV e variacao dos ultimos trinta pregões uteis."""

    def __init__(self, pai: ctk.CTk, simbolo: str) -> None:
        super().__init__(pai)
        self._simbolo = simbolo
        self._servico = ResumoSemanaAgoraServico()
        self._tabela = None
        self._carregando = False

        codigo = codigo_exibicao(simbolo)
        self.title(f"Resumo do mês — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(980, 620)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._carregar_dados)

    def _ao_fechar(self) -> None:
        liberar_grid_resumo_semana_agora(self._tabela)
        self.destroy()

    def _montar_interface(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=12)

        codigo = codigo_exibicao(self._simbolo)
        tipo = rotulo_tipo_ativo(self._simbolo)
        ctk.CTkLabel(
            barra,
            text=f"Resumo do mês — {codigo}  ·  {tipo}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        ctk.CTkButton(
            barra,
            text="Atualizar",
            command=self._carregar_dados,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        ).pack(side="right")

        self._frame_resumo = ctk.CTkFrame(
            cabecalho,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=1,
            border_color=CORES["borda"],
        )
        self._frame_resumo.pack(fill="x", padx=16, pady=(0, 12))

        grade = ctk.CTkFrame(self._frame_resumo, fg_color="transparent")
        grade.pack(fill="x", padx=12, pady=10)
        for coluna in range(3):
            grade.grid_columnconfigure(coluna, weight=1)

        self._valor_variacao_acum, _ = self._criar_card_resumo(grade, 0, "Variacao acumulada (30 pregões)")
        self._valor_media_fechamento, _ = self._criar_card_resumo(grade, 1, "Media de fechamento")
        self._valor_volume_total, _ = self._criar_card_resumo(grade, 2, "Volume total")

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="Carregando metricas dos ultimos 30 dias uteis...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        self._label_status.pack(fill="x", padx=16, pady=(0, 10))

        corpo = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        corpo.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        corpo.grid_rowconfigure(0, weight=1)
        corpo.grid_columnconfigure(0, weight=1)

        self._tabela = criar_grid_resumo_semana_agora(
            corpo,
            "Metricas por dia de pregão",
            altura=18,
        )

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            rodape,
            text="Variacao diaria em relacao ao fechamento do pregão anterior. Dados via Yahoo Finance.",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

    def _criar_card_resumo(
        self,
        pai: ctk.CTkFrame,
        coluna: int,
        rotulo: str,
    ) -> tuple[ctk.CTkLabel, ctk.CTkFrame]:
        quadro = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=8)
        quadro.grid(row=0, column=coluna, sticky="nsew", padx=(0 if coluna == 0 else 6, 0))
        ctk.CTkLabel(
            quadro,
            text=rotulo,
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(8, 2))
        valor = ctk.CTkLabel(
            quadro,
            text="—",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        )
        valor.pack(anchor="w", padx=10, pady=(0, 8))
        return valor, quadro

    def _carregar_dados(self) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return

        self._carregando = True
        self._label_status.configure(
            text="Carregando metricas dos ultimos 30 dias uteis...",
            text_color=CORES["textoSecundario"],
        )

        def buscar():
            return self._servico.obter_resumo(self._simbolo)

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self):
                return

            if erro_thread:
                self._label_status.configure(text=erro_thread, text_color=CORES["erro"])
                return

            resumo, erro = resultado if resultado is not None else (None, None)
            if erro or resumo is None:
                self._label_status.configure(
                    text=erro or "Nao foi possivel carregar o resumo do mês.",
                    text_color=CORES["erro"],
                )
                return

            self._aplicar_resumo(resumo)

        executar_em_thread(self, buscar, ao_concluir)

    def _aplicar_resumo(self, resumo: ResumoSemanaAgora) -> None:
        moeda = resumo.moeda
        if resumo.variacao_acumulada_valor is not None and resumo.variacao_acumulada_pct is not None:
            texto_var = formatar_variacao(
                resumo.variacao_acumulada_valor,
                resumo.variacao_acumulada_pct,
                moeda,
            )
            cor_var = (
                CORES["sucesso"]
                if resumo.variacao_acumulada_valor >= 0
                else CORES["erro"]
            )
        else:
            texto_var = "—"
            cor_var = CORES["textoSecundario"]

        self._valor_variacao_acum.configure(text=texto_var, text_color=cor_var)
        self._valor_media_fechamento.configure(
            text=(
                formatar_moeda(resumo.media_fechamento, moeda)
                if resumo.media_fechamento is not None
                else "—"
            ),
        )
        self._valor_volume_total.configure(
            text=(
                f"{resumo.volume_total:,}".replace(",", ".")
                if resumo.volume_total is not None
                else "—"
            ),
        )

        if self._tabela is not None:
            preencher_grid_resumo_semana_agora(self._tabela, resumo)

        periodo = ""
        if resumo.dias:
            periodo = (
                f"{resumo.dias[0].data.strftime('%d/%m/%Y')} a "
                f"{resumo.dias[-1].data.strftime('%d/%m/%Y')}"
            )
        self._label_status.configure(
            text=f"{len(resumo.dias)} dias uteis · {periodo}",
            text_color=CORES["textoSecundario"],
        )


def abrir_janela_resumo_semana_agora(
    pai: ctk.CTk,
    simbolo: str,
    *,
    janela_atual: JanelaResumoSemanaAgora | None = None,
) -> JanelaResumoSemanaAgora | None:
    """Abre ou foca o resumo mensal do ativo."""
    if not pai.winfo_exists():
        return None

    if janela_atual is not None:
        try:
            if janela_atual.winfo_exists():
                if getattr(janela_atual, "_simbolo", None) == simbolo:
                    janela_atual.focus_force()
                    janela_atual.lift()
                    janela_atual._carregar_dados()
                    return janela_atual
                janela_atual._ao_fechar()
        except Exception:
            pass

    return JanelaResumoSemanaAgora(pai, simbolo)
