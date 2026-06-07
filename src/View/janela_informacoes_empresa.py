"""Janela com informacoes cadastrais detalhadas da empresa."""
from __future__ import annotations

import webbrowser

import customtkinter as ctk

from src.Model.detalhes_acao import DetalhesAcao
from src.Tool.cadastro_empresa_helper import montar_endereco_completo
from src.Tool.janela_helper import configurar_janela_maximizada
from src.View.formatadores import formatar_texto_opcional
from src.View.tema import CORES

_FONTE_ROTULO = 14
_FONTE_VALOR = 15
_FONTE_TITULO_SECAO = 16
_FONTE_TEXTO = 14


class JanelaInformacoesEmpresa(ctk.CTkToplevel):
    """Exibe CNPJ, endereco, contatos, dirigentes e filiais quando disponiveis."""

    def __init__(self, pai: ctk.CTk, dados: DetalhesAcao) -> None:
        super().__init__(pai)
        self._dados = dados

        self.title(f"Informacoes cadastrais — {dados.codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(720, 520)

        self._montar_interface()
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text=f"{self._dados.codigo} — {self._dados.nome_empresa}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            cabecalho,
            text="Dados cadastrais e de contato obtidos do Yahoo Finance quando disponiveis.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=860,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=16, pady=(8, 8))

        self._secao_identificacao(scroll)
        self._secao_endereco(scroll)
        self._secao_contato(scroll)
        self._secao_dirigentes(scroll)
        self._secao_filiais(scroll)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self.destroy,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
        ).pack(side="right")

    def _titulo_secao(self, pai: ctk.CTkFrame, texto: str) -> None:
        ctk.CTkLabel(
            pai,
            text=texto,
            font=ctk.CTkFont(size=_FONTE_TITULO_SECAO, weight="bold"),
            text_color=CORES["primaria"],
        ).pack(anchor="w", padx=12, pady=(14, 6))

    def _campo(self, pai: ctk.CTkFrame, rotulo: str, valor: str) -> None:
        card = ctk.CTkFrame(pai, fg_color=CORES["fundo"], corner_radius=8)
        card.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(
            card,
            text=rotulo,
            font=ctk.CTkFont(size=_FONTE_ROTULO, weight="bold"),
            text_color=CORES["textoSecundario"],
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            card,
            text=valor or "—",
            font=ctk.CTkFont(size=_FONTE_VALOR),
            text_color=CORES["texto"],
            wraplength=820,
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

    def _secao_identificacao(self, pai: ctk.CTkScrollableFrame) -> None:
        self._titulo_secao(pai, "Identificacao")
        cnpj = self._dados.cnpj.strip() or (
            "Nao informado pela fonte de dados. Consulte a CVM ou o site de RI da empresa."
        )
        self._campo(pai, "CNPJ", cnpj)
        self._campo(pai, "Razao social / Nome", formatar_texto_opcional(self._dados.nome_empresa))
        self._campo(pai, "Codigo de negociacao", formatar_texto_opcional(self._dados.codigo))
        self._campo(pai, "Bolsa", formatar_texto_opcional(self._dados.bolsa))
        self._campo(pai, "Pais de origem", formatar_texto_opcional(self._dados.pais))
        self._campo(pai, "Setor", formatar_texto_opcional(self._dados.setor))
        self._campo(pai, "Industria", formatar_texto_opcional(self._dados.industria))
        self._campo(
            pai,
            "Funcionarios",
            formatar_texto_opcional(self._dados.funcionarios),
        )

    def _secao_endereco(self, pai: ctk.CTkScrollableFrame) -> None:
        self._titulo_secao(pai, "Endereco")
        endereco = montar_endereco_completo(self._dados)
        self._campo(
            pai,
            "Endereco completo",
            endereco or "Endereco nao informado pela fonte de dados.",
        )

    def _secao_contato(self, pai: ctk.CTkScrollableFrame) -> None:
        self._titulo_secao(pai, "Contato")
        self._campo(pai, "Telefone", formatar_texto_opcional(self._dados.telefone))
        self._campo(pai, "Site institucional", formatar_texto_opcional(self._dados.site))
        self._campo(pai, "Site de RI", formatar_texto_opcional(self._dados.site_ri))

        if self._dados.site:
            ctk.CTkButton(
                pai,
                text="Abrir site institucional",
                command=lambda: webbrowser.open(self._dados.site),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=200,
            ).pack(anchor="w", padx=12, pady=(4, 4))

        if self._dados.site_ri:
            ctk.CTkButton(
                pai,
                text="Abrir site de RI",
                command=lambda: webbrowser.open(self._dados.site_ri),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=200,
            ).pack(anchor="w", padx=12, pady=(0, 8))

    def _secao_dirigentes(self, pai: ctk.CTkScrollableFrame) -> None:
        self._titulo_secao(pai, "Dirigentes")
        if not self._dados.dirigentes:
            self._campo(
                pai,
                "Lista de dirigentes",
                "Nenhum dirigente informado pela fonte de dados.",
            )
            return

        for nome, cargo in self._dados.dirigentes:
            self._campo(pai, cargo, nome)

    def _secao_filiais(self, pai: ctk.CTkScrollableFrame) -> None:
        self._titulo_secao(pai, "Filiais e unidades")
        if not self._dados.filiais:
            self._campo(
                pai,
                "Filiais",
                (
                    "A fonte de dados (Yahoo Finance) nao disponibiliza a lista de filiais "
                    "para este ativo. Consulte o site de RI ou relatorios da empresa."
                ),
            )
            return

        for indice, filial in enumerate(self._dados.filiais, start=1):
            self._campo(pai, f"Unidade {indice}", filial)
