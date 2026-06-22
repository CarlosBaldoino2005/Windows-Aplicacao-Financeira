"""Janela com fita de negocios do dia, atualizada em tempo quase real."""
from __future__ import annotations

from datetime import date, datetime

import customtkinter as ctk
from tkinter import ttk

from src.Model.negocio_agora import NegocioAgora, ResumoNegociosAgora
from src.Service.negocios_agora_servico import NegociosAgoraServico
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.painel_resumo_negocios_agora_helper import PainelResumoNegociosAgora
from src.View.tabela_negocios_agora_helper import (
    criar_grid_negocios_agora,
    liberar_grid_negocios_agora,
    preencher_grid_negocios_agora,
)
from src.View.tema import CORES

INTERVALO_ATUALIZACAO_MS = 3_000


class JanelaNegociosAgora(ctk.CTkToplevel):
    """Lista negocios do dia com atualizacao automatica."""

    def __init__(self, pai: ctk.CTk, simbolo: str) -> None:
        super().__init__(pai)
        self._simbolo = simbolo
        self._servico = NegociosAgoraServico()
        self._tabela: ttk.Treeview | None = None
        self._ao_vivo = True
        self._carregando = False
        self._job_atualizacao: str | None = None
        self._negocios: list[NegocioAgora] = []
        self._resumo: ResumoNegociosAgora = ResumoNegociosAgora(0, 0, 0)

        codigo = codigo_exibicao(simbolo)
        self.title(f"Negocios — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(980, 640)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(200, self._atualizar_dados)
        self._agendar_proxima_atualizacao()

    def _montar_interface(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=12)

        codigo = codigo_exibicao(self._simbolo)
        ctk.CTkLabel(
            barra,
            text=f"Negocios — {codigo}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        self._badge_ao_vivo = ctk.CTkLabel(
            barra,
            text="AO VIVO",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            fg_color=CORES["erro"],
            corner_radius=6,
            width=72,
            height=26,
        )
        self._badge_ao_vivo.pack(side="left", padx=(12, 0))

        self._btn_pausar = ctk.CTkButton(
            barra,
            text="Pausar",
            command=self._alternar_pausa,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=90,
        )
        self._btn_pausar.pack(side="right")

        ctk.CTkButton(
            barra,
            text="Atualizar agora",
            command=self._atualizar_dados,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=130,
        ).pack(side="right", padx=(0, 8))

        self._label_status = ctk.CTkLabel(
            cabecalho,
            text="Carregando negocios do dia...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
            justify="left",
        )
        self._label_status.pack(fill="x", padx=16, pady=(0, 8))

        self._painel_resumo = PainelResumoNegociosAgora(cabecalho)
        self._painel_resumo.pack(fill="x", padx=16, pady=(0, 10))

        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.grid(row=1, column=0, sticky="nsew", padx=16, pady=(8, 8))
        conteudo.grid_columnconfigure(0, weight=1)
        conteudo.grid_rowconfigure(0, weight=1)

        self._tabela = criar_grid_negocios_agora(
            conteudo,
            "Ultimas transacoes",
            altura=24,
        )

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkLabel(
            rodape,
            text=(
                "Dados intraday (Yahoo Finance), agregados por minuto. "
                "Pode haver atraso em relacao ao pregão ao vivo."
            ),
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
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

    def _ao_fechar(self) -> None:
        self._ao_vivo = False
        if self._job_atualizacao is not None:
            try:
                self.after_cancel(self._job_atualizacao)
            except Exception:
                pass
            self._job_atualizacao = None
        liberar_grid_negocios_agora(self._tabela)
        self.destroy()

    def _alternar_pausa(self) -> None:
        self._ao_vivo = not self._ao_vivo
        if self._ao_vivo:
            self._btn_pausar.configure(text="Pausar")
            self._badge_ao_vivo.configure(fg_color=CORES["erro"])
            self._atualizar_dados()
            self._agendar_proxima_atualizacao()
        else:
            self._btn_pausar.configure(text="Retomar")
            self._badge_ao_vivo.configure(fg_color=CORES["textoSecundario"])
            if self._job_atualizacao is not None:
                try:
                    self.after_cancel(self._job_atualizacao)
                except Exception:
                    pass
                self._job_atualizacao = None

    def _agendar_proxima_atualizacao(self) -> None:
        if not self._ao_vivo or not janela_ui_ainda_ativa(self):
            return
        self._job_atualizacao = self.after(INTERVALO_ATUALIZACAO_MS, self._ciclo_automatico)

    def _ciclo_automatico(self) -> None:
        self._job_atualizacao = None
        if not self._ao_vivo or not janela_ui_ainda_ativa(self):
            return
        self._atualizar_dados()
        self._agendar_proxima_atualizacao()

    def _atualizar_dados(self) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return
        self._carregando = True
        self._label_status.configure(text="Atualizando negocios...")

        def buscar():
            return self._servico.listar_negocios_do_dia(self._simbolo, date.today())

        def ao_concluir(resultado, erro_thread):
            self._carregando = False
            if not janela_ui_ainda_ativa(self):
                return
            if erro_thread:
                self._label_status.configure(
                    text=f"Erro ao carregar: {erro_thread}",
                    text_color=CORES["erro"],
                )
                return

            negocios, resumo, erro = resultado or (
                [],
                ResumoNegociosAgora(0, 0, 0),
                "Resposta invalida.",
            )
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                if self._tabela is not None:
                    preencher_grid_negocios_agora(self._tabela, [])
                self._painel_resumo.atualizar(ResumoNegociosAgora(0, 0, 0))
                return

            self._negocios = negocios
            self._resumo = resumo
            if self._tabela is not None:
                preencher_grid_negocios_agora(self._tabela, negocios)
            self._painel_resumo.atualizar(resumo)

            agora = datetime.now().strftime("%H:%M:%S")
            self._label_status.configure(
                text=(
                    f"{len(negocios)} negocio(s) em {date.today().strftime('%d/%m/%Y')} "
                    f"— atualizado as {agora}"
                ),
                text_color=CORES["textoSecundario"],
            )

        executar_em_thread(self, buscar, ao_concluir)


def abrir_janela_negocios_agora(
    pai: ctk.CTk,
    simbolo: str,
    janela_atual: JanelaNegociosAgora | None = None,
) -> JanelaNegociosAgora | None:
    """Abre ou foca a fita de negocios para o simbolo informado."""
    if not pai.winfo_exists():
        return None

    if janela_atual is not None:
        try:
            if janela_atual.winfo_exists():
                if getattr(janela_atual, "_simbolo", None) == simbolo:
                    janela_atual.focus_force()
                    janela_atual.lift()
                    return janela_atual
                janela_atual._ao_fechar()
        except Exception:
            pass

    return JanelaNegociosAgora(pai, simbolo)
