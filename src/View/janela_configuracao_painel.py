"""Janela modal para tema, quantidade de acoes e fonte das grids."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import customtkinter as ctk
from tkinter import messagebox

from src.Model.opcoes_atualizacao_automatica import (
    INTERVALO_MAXIMO_SEGUNDOS,
    INTERVALO_MINIMO_SEGUNDOS,
)
from src.Model.opcoes_fonte_grid import FONTE_MEDIO, ROTULOS_FONTE_GRID
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_filha_modal, liberar_modal_janela_filha
from src.Tool.validadores import (
    validar_fonte_grid,
    validar_intervalo_atualizacao_segundos,
    validar_quantidade_acoes,
)
from src.View.tema import (
    CORES,
    modo_de_rotulo,
    rotulo_modo_aparencia,
)

_LARGURA = 480
_ALTURA = 580


@dataclass(frozen=True)
class ResultadoConfiguracaoPainel:
    """Valores aplicados ao salvar a configuracao do painel principal."""

    modo_aparencia: str
    quantidade_acoes: int
    fonte_grid: str
    atualizacao_automatica_habilitada: bool
    intervalo_atualizacao_segundos: int
    tema_alterado: bool
    quantidade_alterada: bool
    fonte_alterada: bool
    atualizacao_alterada: bool


def _centralizar_sobre_pai(janela: ctk.CTkToplevel, pai: ctk.CTk) -> None:
    try:
        janela.update_idletasks()
        pai.update_idletasks()
        x = int(pai.winfo_rootx() + max(0, (pai.winfo_width() - _LARGURA) / 2))
        y = int(pai.winfo_rooty() + max(0, (pai.winfo_height() - _ALTURA) / 2))
        janela.geometry(f"{_LARGURA}x{_ALTURA}+{x}+{y}")
    except Exception:
        pass


class JanelaConfiguracaoPainel(ctk.CTkToplevel):
    """Define tema, limite de acoes, fonte das grids e atualizacao automatica."""

    def __init__(
        self,
        pai: ctk.CTk,
        config: ConfigPainelIni,
        ao_aplicar: Callable[[ResultadoConfiguracaoPainel], None],
    ) -> None:
        super().__init__(pai)
        self._config = config
        self._ao_aplicar = ao_aplicar
        self._modo_tema_inicial = config.carregar_modo_aparencia()
        self._qtd_inicial = config.carregar()
        self._fonte_inicial = config.carregar_fonte_grid()
        self._auto_inicial = config.carregar_atualizacao_automatica()

        self.title("Configuracoes do painel")
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(_LARGURA, _ALTURA)

        self._montar_interface()
        _centralizar_sobre_pai(self, pai)
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _ao_fechar(self) -> None:
        liberar_modal_janela_filha(self)
        self.destroy()

    def _montar_interface(self) -> None:
        painel = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        # Botoes fixos na parte inferior para nunca ficarem fora da janela.
        self._montar_botoes(painel)

        conteudo = ctk.CTkScrollableFrame(painel, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        ctk.CTkLabel(
            conteudo,
            text="Configuracoes",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            conteudo,
            text=(
                "Tema, quantidade de acoes, fonte das grids e atualizacao automatica "
                "de cotacoes em todos os paineis."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 12))

        self._montar_campo_tema(conteudo)
        self._montar_campo_quantidade(conteudo)
        self._montar_campo_fonte(conteudo)
        self._montar_campo_atualizacao_automatica(conteudo)

    def _montar_campo_tema(self, painel: ctk.CTkScrollableFrame) -> None:
        bloco = ctk.CTkFrame(painel, fg_color="transparent")
        bloco.pack(fill="x", padx=8, pady=(0, 12))

        ctk.CTkLabel(
            bloco,
            text="Tema da interface",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        self._seletor_tema = ctk.CTkSegmentedButton(
            bloco,
            values=["Claro", "Escuro"],
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_tema.set(rotulo_modo_aparencia(self._modo_tema_inicial))
        self._seletor_tema.pack(anchor="w", pady=(6, 0))

    def _montar_campo_quantidade(self, painel: ctk.CTkScrollableFrame) -> None:
        bloco = ctk.CTkFrame(painel, fg_color="transparent")
        bloco.pack(fill="x", padx=8, pady=(0, 12))

        ctk.CTkLabel(
            bloco,
            text="Quantidade de acoes (Em alta / Em queda / Todas)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            bloco,
            text="Limite de linhas em cada aba do painel (1 a 100).",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", pady=(2, 4))

        self._entrada_quantidade = ctk.CTkEntry(bloco, width=80, justify="center")
        self._entrada_quantidade.insert(0, str(self._qtd_inicial))
        self._entrada_quantidade.pack(anchor="w")

    def _montar_campo_fonte(self, painel: ctk.CTkScrollableFrame) -> None:
        bloco = ctk.CTkFrame(painel, fg_color="transparent")
        bloco.pack(fill="x", padx=8, pady=(0, 12))

        ctk.CTkLabel(
            bloco,
            text="Fonte das grids",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        self._rotulo_para_modo = {v: k for k, v in ROTULOS_FONTE_GRID.items()}
        rotulo_atual = ROTULOS_FONTE_GRID.get(self._fonte_inicial, ROTULOS_FONTE_GRID[FONTE_MEDIO])

        self._combo_fonte = ctk.CTkComboBox(
            bloco,
            values=list(ROTULOS_FONTE_GRID.values()),
            width=160,
        )
        self._combo_fonte.set(rotulo_atual)
        self._combo_fonte.pack(anchor="w", pady=(6, 0))

    def _montar_campo_atualizacao_automatica(self, painel: ctk.CTkScrollableFrame) -> None:
        bloco = ctk.CTkFrame(painel, fg_color="transparent")
        bloco.pack(fill="x", padx=8, pady=(0, 12))

        ctk.CTkLabel(
            bloco,
            text="Atualizacao automatica de cotacoes",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            bloco,
            text=(
                "Vale para o painel principal, criptomoedas, FIIs, dividendos, "
                "favoritos e demais telas com cotacoes."
            ),
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            wraplength=400,
            justify="left",
        ).pack(anchor="w", pady=(2, 6))

        linha = ctk.CTkFrame(bloco, fg_color="transparent")
        linha.pack(fill="x")

        self._seletor_auto = ctk.CTkSegmentedButton(
            linha,
            values=["Sim", "Nao"],
            command=self._ao_alterar_atualizacao_automatica,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            selected_hover_color=CORES["primariaHover"],
            unselected_color=CORES["superficie"],
            unselected_hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        )
        self._seletor_auto.set("Sim" if self._auto_inicial.habilitada else "Nao")
        self._seletor_auto.pack(side="left")

        ctk.CTkLabel(
            linha,
            text="Intervalo (s)",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(side="left", padx=(16, 6))

        self._entrada_intervalo = ctk.CTkEntry(linha, width=72, justify="center")
        self._entrada_intervalo.insert(0, str(self._auto_inicial.intervalo_segundos))
        self._entrada_intervalo.pack(side="left")

        ctk.CTkLabel(
            bloco,
            text=f"Padrao: desligado, {self._config.padrao_intervalo_atualizacao_segundos()} s "
            f"({INTERVALO_MINIMO_SEGUNDOS} a {INTERVALO_MAXIMO_SEGUNDOS}).",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", pady=(6, 8))

        self._ao_alterar_atualizacao_automatica(self._seletor_auto.get())

    def _ao_alterar_atualizacao_automatica(self, valor: str) -> None:
        estado = "normal" if valor == "Sim" else "disabled"
        self._entrada_intervalo.configure(state=estado)

    def _montar_botoes(self, painel: ctk.CTkFrame) -> None:
        barra = ctk.CTkFrame(painel, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            barra,
            text="Cancelar",
            command=self._ao_fechar,
            fg_color=CORES["superficie"],
            hover_color=CORES["zebraEscura"],
            border_width=1,
            border_color=CORES["borda"],
            text_color=CORES["texto"],
            width=110,
        ).pack(side="right")

        ctk.CTkButton(
            barra,
            text="Salvar",
            command=self._salvar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=110,
        ).pack(side="right", padx=(0, 8))

    def _salvar(self) -> None:
        modo = modo_de_rotulo(self._seletor_tema.get())

        quantidade, erro_qtd = validar_quantidade_acoes(self._entrada_quantidade.get())
        if erro_qtd:
            messagebox.showwarning("Quantidade", erro_qtd, parent=self)
            return

        rotulo_fonte = self._combo_fonte.get().strip()
        fonte_grid, erro_fonte = validar_fonte_grid(
            self._rotulo_para_modo.get(rotulo_fonte, rotulo_fonte)
        )
        if erro_fonte:
            messagebox.showwarning("Fonte grid", erro_fonte, parent=self)
            return

        habilitada = self._seletor_auto.get() == "Sim"
        intervalo, erro_intervalo = validar_intervalo_atualizacao_segundos(
            self._entrada_intervalo.get()
        )
        if erro_intervalo:
            messagebox.showwarning("Atualizacao automatica", erro_intervalo, parent=self)
            return
        if intervalo is None:
            messagebox.showwarning(
                "Atualizacao automatica",
                "Informe o intervalo em segundos.",
                parent=self,
            )
            return

        tema_alterado = modo != self._modo_tema_inicial
        quantidade_alterada = quantidade != self._qtd_inicial
        fonte_alterada = fonte_grid != self._fonte_inicial
        atualizacao_alterada = (
            habilitada != self._auto_inicial.habilitada
            or intervalo != self._auto_inicial.intervalo_segundos
        )

        try:
            self._config.salvar_modo_aparencia(modo)
            self._config.salvar(quantidade)
            self._config.salvar_fonte_grid(fonte_grid)
            self._config.salvar_atualizacao_automatica(habilitada, intervalo)
        except OSError:
            messagebox.showerror(
                "Configuracao",
                "Nao foi possivel gravar dados/painel.ini.",
                parent=self,
            )
            return

        resultado = ResultadoConfiguracaoPainel(
            modo_aparencia=modo,
            quantidade_acoes=quantidade,
            fonte_grid=fonte_grid,
            atualizacao_automatica_habilitada=habilitada,
            intervalo_atualizacao_segundos=intervalo,
            tema_alterado=tema_alterado,
            quantidade_alterada=quantidade_alterada,
            fonte_alterada=fonte_alterada,
            atualizacao_alterada=atualizacao_alterada,
        )
        self._ao_aplicar(resultado)
        self._ao_fechar()


def abrir_configuracao_painel(
    pai: ctk.CTk,
    config: ConfigPainelIni,
    ao_aplicar: Callable[[ResultadoConfiguracaoPainel], None],
) -> JanelaConfiguracaoPainel | None:
    """Abre o modal de configuracao (tema, qtd acoes, fonte grid)."""
    if not pai.winfo_exists():
        return None
    return JanelaConfiguracaoPainel(pai, config, ao_aplicar)
