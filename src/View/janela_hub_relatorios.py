"""Hub de relatorios (carteira e IPOs recentes)."""
from __future__ import annotations

import customtkinter as ctk

from src.View import mensagem_helper as messagebox

from src.Controller.controlador_relatorios import ControladorRelatorios
from src.Service.email_relatorio_servico import EmailRelatorioServico
from src.Service.relatorio_carteira_servico import RelatorioCarteiraServico
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.hub_painel_config_helper import ConfiguracaoHubPainel
from src.View.janela_relatorio_ipos import JanelaRelatorioIpos
from src.View.tema import CORES


class JanelaHubRelatorios(ctk.CTkToplevel):
    """Acesso aos relatorios da carteira e de IPOs recentes."""

    def __init__(self, pai: ctk.CTk) -> None:
        super().__init__(pai)
        self._controlador = ControladorRelatorios()
        self._config_painel = ConfigPainelIni()
        self._janela_ipos: JanelaRelatorioIpos | None = None
        self._gerando_relatorio = False
        self._config_hub = ConfiguracaoHubPainel(
            self,
            self._config_painel,
            incluir_quantidade=False,
            ao_remontar_layout=self._reconstruir_interface_apos_tema,
        )

        self.title("Relatorios")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(720, 420)

        self._montar_layout()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _ao_fechar(self) -> None:
        if self._janela_ipos is not None:
            try:
                if self._janela_ipos.winfo_exists():
                    self._janela_ipos._ao_fechar()
            except Exception:
                pass
        self.destroy()

    def _montar_layout(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        self._config_hub.montar_titulo_com_engrenagem(cabecalho, "Relatorios")

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Gere o PDF da carteira ou consulte empresas que fizeram IPO "
                "nos ultimos 30 dias (Brasil e mundo)."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self._montar_consultas()

        ctk.CTkLabel(
            self,
            text="Dados publicos (CVM, StockAnalysis, Yahoo Finance). Uso educacional.",
            font=ctk.CTkFont(size=11),
            text_color=CORES.get("textoAvisoLegal", CORES["aviso"]),
            fg_color=CORES.get("destaqueAvisoLegal", CORES["avisoFundo"]),
            corner_radius=8,
        ).pack(fill="x", padx=16, pady=(0, 12))

    def _montar_consultas(self) -> None:
        card = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        card.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            card,
            text="Consultas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(12, 4))

        ctk.CTkLabel(
            card,
            text="Escolha o relatorio desejado nos botoes abaixo.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=12, pady=(0, 8))

        linha = ctk.CTkFrame(card, fg_color="transparent")
        linha.pack(anchor="w", padx=12, pady=(0, 8))

        for texto, comando in (
            ("Relatorio da carteira (PDF)", self._gerar_relatorio_carteira),
            ("IPOs — ultimos 30 dias", self._abrir_relatorio_ipos),
        ):
            ctk.CTkButton(
                linha,
                text=texto,
                command=comando,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
                width=220,
                height=36,
            ).pack(side="left", padx=(0, 8))

        barra = ctk.CTkFrame(card, fg_color="transparent")
        barra.pack(fill="x", padx=12, pady=(0, 12))

        self._label_status = ctk.CTkLabel(
            barra,
            text="Escolha um relatorio acima.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=820,
            justify="left",
        )
        self._label_status.pack(side="left")

    def _reconstruir_interface_apos_tema(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()
        self._config_hub.limpar_referencia_modal()
        self.configure(fg_color=CORES["fundo"])
        self._montar_layout()

    def _gerar_relatorio_carteira(self) -> None:
        if self._gerando_relatorio or not janela_ui_ainda_ativa(self):
            return

        self._gerando_relatorio = True
        self._label_status.configure(
            text="Gerando relatorio PDF da carteira...",
            text_color=CORES["textoSecundario"],
        )

        def tarefa():
            caminho, erro, assunto = self._controlador.gerar_relatorio_pdf_carteira()
            if erro or caminho is None:
                return caminho, erro, None

            opcoes = self._controlador.carregar_relatorio_automatico_carteira()
            erro_email: str | None = None
            if opcoes.emails_destinatarios:
                _, erro_email = EmailRelatorioServico().enviar_relatorio_pdf(
                    caminho,
                    opcoes.emails_destinatarios,
                    assunto=assunto or "",
                )
            return caminho, None, erro_email

        def ao_concluir(resultado, erro_thread):
            self._gerando_relatorio = False
            if not janela_ui_ainda_ativa(self):
                return

            if erro_thread:
                messagebox.showerror("Relatorio", erro_thread, parent=self)
                self._label_status.configure(text=erro_thread, text_color=CORES["erro"])
                return

            caminho, erro, erro_email = (
                resultado if resultado is not None else (None, "Falha ao gerar relatorio.", None)
            )
            if erro or caminho is None:
                texto = erro or "Nao foi possivel gerar o relatorio."
                messagebox.showerror("Relatorio", texto, parent=self)
                self._label_status.configure(text=texto, text_color=CORES["erro"])
                return

            erro_abrir = RelatorioCarteiraServico.abrir_pdf_no_sistema(caminho)
            mensagem = f"PDF salvo em:\n{caminho}"
            if erro_abrir:
                mensagem = f"{mensagem}\n\n{erro_abrir}"
            opcoes_email = self._controlador.carregar_relatorio_automatico_carteira()
            if erro_email:
                mensagem = f"{mensagem}\n\nFalha no e-mail:\n{erro_email}"
            elif opcoes_email.emails_destinatarios:
                mensagem = (
                    f"{mensagem}\n\nE-mail enviado para "
                    f"{len(opcoes_email.emails_destinatarios)} destinatario(s)."
                )

            messagebox.showinfo("Relatorio gerado", mensagem, parent=self)
            texto_status = f"Relatorio da carteira salvo: {caminho.name}"
            if erro_email:
                texto_status = f"{texto_status} | E-mail: {erro_email}"
            self._label_status.configure(
                text=texto_status,
                text_color=CORES["erro"] if erro_email else CORES["sucesso"],
            )

        executar_em_thread(self, tarefa, ao_concluir)

    def _abrir_relatorio_ipos(self) -> None:
        if self._janela_ipos is not None:
            try:
                if self._janela_ipos.winfo_exists():
                    self._janela_ipos.focus_force()
                    self._janela_ipos.lift()
                    self._janela_ipos._atualizar_grid(forcar=True)
                    return
            except Exception:
                pass
        self._janela_ipos = JanelaRelatorioIpos(self, self._controlador)
