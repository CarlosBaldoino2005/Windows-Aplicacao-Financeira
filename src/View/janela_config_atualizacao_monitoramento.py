"""Modal para configurar atualizacao automatica da tela de monitoramento."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.opcoes_atualizacao_automatica import (
    INTERVALO_MAXIMO_SEGUNDOS,
    INTERVALO_MINIMO_SEGUNDOS,
)
from src.Tool.atualizacao_automatica_helper import (
    notificar_mudanca_configuracao_atualizacao_automatica_monitoramento,
)
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_filha_modal, liberar_modal_janela_filha
from src.Tool.validadores import validar_intervalo_atualizacao_segundos
from src.View import mensagem_helper as messagebox
from src.View.tema import CORES

_LARGURA = 460
_ALTURA = 300


class JanelaConfigAtualizacaoMonitoramento(ctk.CTkToplevel):
    """Define se a grid de monitoramento atualiza sozinha e em qual intervalo."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        config: ConfigPainelIni,
        ao_salvar: Callable[[], None],
    ) -> None:
        super().__init__(pai)
        self._config = config
        self._ao_salvar = ao_salvar
        self._opcoes_iniciais = config.carregar_atualizacao_automatica_monitoramento()

        self.title("Atualizacao do monitoramento")
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(_LARGURA, _ALTURA)

        self._montar_interface()
        self._centralizar_sobre_pai(pai)
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _centralizar_sobre_pai(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            pai.update_idletasks()
            x = int(pai.winfo_rootx() + max(0, (pai.winfo_width() - _LARGURA) / 2))
            y = int(pai.winfo_rooty() + max(0, (pai.winfo_height() - _ALTURA) / 2))
            self.geometry(f"{_LARGURA}x{_ALTURA}+{x}+{y}")
        except Exception:
            pass

    def _ao_fechar(self) -> None:
        liberar_modal_janela_filha(self)
        self.destroy()

    def _montar_interface(self) -> None:
        painel = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            painel,
            text="Atualizacao automatica",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            painel,
            text=(
                "Atualiza as cotacoes e cores de alerta da grid de monitoramento "
                "sem precisar clicar em Atualizar cotacoes."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        linha = ctk.CTkFrame(painel, fg_color="transparent")
        linha.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(
            linha,
            text="Automatico",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left", padx=(0, 12))

        self._seletor_auto = ctk.CTkSegmentedButton(
            linha,
            values=["Sim", "Nao"],
            command=self._ao_alterar_automatico,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_auto.set("Sim" if self._opcoes_iniciais.habilitada else "Nao")
        self._seletor_auto.pack(side="left")

        linha_intervalo = ctk.CTkFrame(painel, fg_color="transparent")
        linha_intervalo.pack(fill="x", padx=16, pady=(8, 8))

        ctk.CTkLabel(
            linha_intervalo,
            text="Intervalo (segundos)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left", padx=(0, 12))

        self._entrada_intervalo = ctk.CTkEntry(linha_intervalo, width=80, justify="center")
        self._entrada_intervalo.insert(0, str(self._opcoes_iniciais.intervalo_segundos))
        self._entrada_intervalo.pack(side="left")

        ctk.CTkLabel(
            painel,
            text=(
                f"Padrao: desligado, {self._config.padrao_intervalo_atualizacao_segundos()} s "
                f"({INTERVALO_MINIMO_SEGUNDOS} a {INTERVALO_MAXIMO_SEGUNDOS})."
            ),
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=16, pady=(0, 8))

        self._ao_alterar_automatico(self._seletor_auto.get())

        barra = ctk.CTkFrame(painel, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=16, pady=(8, 16))

        ctk.CTkButton(
            barra,
            text="Cancelar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        ).pack(side="right")

        ctk.CTkButton(
            barra,
            text="Salvar",
            command=self._salvar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        ).pack(side="right", padx=(0, 8))

    def _ao_alterar_automatico(self, valor: str) -> None:
        estado = "normal" if valor == "Sim" else "disabled"
        self._entrada_intervalo.configure(state=estado)

    def _salvar(self) -> None:
        habilitada = self._seletor_auto.get() == "Sim"
        intervalo, erro_intervalo = validar_intervalo_atualizacao_segundos(
            self._entrada_intervalo.get()
        )
        if erro_intervalo:
            messagebox.showwarning("Intervalo", erro_intervalo, parent=self)
            return
        if intervalo is None:
            messagebox.showwarning(
                "Intervalo",
                "Informe o intervalo em segundos.",
                parent=self,
            )
            return

        try:
            self._config.salvar_atualizacao_automatica_monitoramento(habilitada, intervalo)
        except OSError:
            messagebox.showerror(
                "Configuracao",
                "Nao foi possivel gravar dados/painel.ini.",
                parent=self,
            )
            return

        notificar_mudanca_configuracao_atualizacao_automatica_monitoramento()
        self._ao_salvar()
        self._ao_fechar()


def abrir_config_atualizacao_monitoramento(
    pai: ctk.CTk | ctk.CTkToplevel,
    config: ConfigPainelIni,
    ao_salvar: Callable[[], None],
) -> JanelaConfigAtualizacaoMonitoramento | None:
    if not pai.winfo_exists():
        return None
    return JanelaConfigAtualizacaoMonitoramento(pai, config, ao_salvar)
