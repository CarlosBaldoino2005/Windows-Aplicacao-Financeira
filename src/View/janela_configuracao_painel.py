"""Janela modal para tema, quantidade de acoes e fonte das grids."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Model.opcoes_atualizacao_automatica import (
    INTERVALO_MAXIMO_SEGUNDOS,
    INTERVALO_MINIMO_SEGUNDOS,
)
from src.Model.opcoes_fonte_grid import FONTE_MEDIO, ROTULOS_FONTE_GRID
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.janela_helper import configurar_janela_filha_modal, liberar_modal_janela_filha, centralizar_janela_sobre_referencia
from src.Tool.validadores import (
    validar_fonte_grid,
    validar_intervalo_atualizacao_segundos,
    validar_quantidade_acoes,
    validar_quantidade_cripto,
)
from src.View.tema import (
    CORES,
    modo_de_rotulo,
    rotulo_modo_aparencia,
)

_LARGURA = 480
_ALTURA = 580

EscopoQuantidadePainel = Literal["acoes", "cripto", "etfs", "fiis", "dividendos", "acoes_globais"]

_TITULOS_ESCOPO: dict[EscopoQuantidadePainel, str] = {
    "acoes": "Configuracoes do painel",
    "cripto": "Configuracoes — criptomoedas",
    "etfs": "Configuracoes — ETFs",
    "fiis": "Configuracoes — fundos imobiliarios",
    "dividendos": "Configuracoes — empresa + dividendos",
    "acoes_globais": "Configuracoes — acoes globais (BDRs)",
}


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
        centralizar_janela_sobre_referencia(janela, pai, _LARGURA, _ALTURA)
    except Exception:
        pass


class JanelaConfiguracaoPainel(ctk.CTkToplevel):
    """Define tema, limite de acoes, fonte das grids e atualizacao automatica."""

    def __init__(
        self,
        pai: ctk.CTk,
        config: ConfigPainelIni,
        ao_aplicar: Callable[[ResultadoConfiguracaoPainel], None],
        *,
        escopo_quantidade: EscopoQuantidadePainel = "acoes",
        incluir_quantidade: bool = True,
    ) -> None:
        super().__init__(pai)
        self._config = config
        self._ao_aplicar = ao_aplicar
        self._escopo_quantidade = escopo_quantidade
        self._incluir_quantidade = incluir_quantidade
        self._modo_tema_inicial = config.carregar_modo_aparencia()
        if escopo_quantidade == "cripto":
            self._qtd_inicial = config.carregar_quantidade_cripto()
        else:
            self._qtd_inicial = config.carregar()
        self._fonte_inicial = config.carregar_fonte_grid()
        self._auto_inicial = config.carregar_atualizacao_automatica()

        self.title(_TITULOS_ESCOPO.get(escopo_quantidade, "Configuracoes do painel"))
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
            text=self._texto_descricao_configuracao(),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 12))

        self._montar_campo_tema(conteudo)
        if self._incluir_quantidade:
            self._montar_campo_quantidade(conteudo)
        self._montar_campo_fonte(conteudo)
        self._montar_campo_atualizacao_automatica(conteudo)

    def _texto_descricao_configuracao(self) -> str:
        if not self._incluir_quantidade:
            return (
                "Tema, fonte das grids e atualizacao automatica de cotacoes "
                "nos paineis que utilizam essas opcoes."
            )
        mapa: dict[EscopoQuantidadePainel, str] = {
            "acoes": (
                "Tema, quantidade de acoes, fonte das grids e atualizacao automatica "
                "de cotacoes em todos os paineis."
            ),
            "cripto": (
                "Tema, quantidade de criptos, fonte das grids e atualizacao automatica "
                "de cotacoes."
            ),
            "fiis": (
                "Tema, quantidade de FIIs, fonte das grids e atualizacao automatica "
                "de cotacoes."
            ),
            "etfs": (
                "Tema, quantidade de ETFs, fonte das grids e atualizacao automatica "
                "de cotacoes."
            ),
            "dividendos": (
                "Tema, quantidade de empresas, fonte das grids e atualizacao automatica "
                "de cotacoes."
            ),
            "acoes_globais": (
                "Tema, quantidade de BDRs, fonte das grids e atualizacao automatica "
                "de cotacoes."
            ),
        }
        return mapa.get(self._escopo_quantidade, mapa["acoes"])

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

        titulos_qtd: dict[EscopoQuantidadePainel, tuple[str, str]] = {
            "acoes": (
                "Quantidade de acoes (Em alta / Em queda / Todas)",
                "Limite de linhas em cada aba do painel (1 a 100).",
            ),
            "cripto": (
                "Quantidade de criptos (Em alta / Em queda / Todas)",
                "Limite de linhas em cada aba do painel de criptomoedas (1 a 100).",
            ),
            "fiis": (
                "Quantidade de FIIs (Em alta / Em queda / Todas)",
                "Limite de linhas em cada aba do painel de fundos imobiliarios (1 a 100).",
            ),
            "etfs": (
                "Quantidade de ETFs (Em alta / Em queda / Todas)",
                "Limite de linhas em cada aba do painel de ETFs (1 a 100).",
            ),
            "dividendos": (
                "Quantidade de empresas (Em alta / Em queda / Todas)",
                "Limite de linhas em cada aba do painel de dividendos (1 a 100).",
            ),
            "acoes_globais": (
                "Quantidade de BDRs (Em alta / Em queda / Todas)",
                "Limite de linhas em cada aba do painel de acoes globais (1 a 100).",
            ),
        }
        titulo_qtd, detalhe_qtd = titulos_qtd.get(
            self._escopo_quantidade,
            titulos_qtd["acoes"],
        )

        ctk.CTkLabel(
            bloco,
            text=titulo_qtd,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            bloco,
            text=detalhe_qtd,
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
                "Vale para o painel principal, criptomoedas, FIIs, dividendos e favoritos. "
                "A tela de monitoramento possui configuracao propria de atualizacao."
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

    def _salvar(self) -> None:
        modo = modo_de_rotulo(self._seletor_tema.get())

        if self._incluir_quantidade:
            if self._escopo_quantidade == "cripto":
                quantidade, erro_qtd = validar_quantidade_cripto(self._entrada_quantidade.get())
            else:
                quantidade, erro_qtd = validar_quantidade_acoes(self._entrada_quantidade.get())
            if erro_qtd:
                messagebox.showwarning("Quantidade", erro_qtd, parent=self)
                return
        else:
            quantidade = self._qtd_inicial

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
        quantidade_alterada = self._incluir_quantidade and quantidade != self._qtd_inicial
        fonte_alterada = fonte_grid != self._fonte_inicial
        atualizacao_alterada = (
            habilitada != self._auto_inicial.habilitada
            or intervalo != self._auto_inicial.intervalo_segundos
        )

        try:
            self._config.salvar_modo_aparencia(modo)
            if self._escopo_quantidade == "cripto":
                self._config.salvar_quantidade_cripto(quantidade)
            else:
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
    *,
    escopo_quantidade: EscopoQuantidadePainel = "acoes",
    incluir_quantidade: bool = True,
) -> JanelaConfiguracaoPainel | None:
    """Abre o modal de configuracao (tema, quantidade, fonte grid)."""
    if not pai.winfo_exists():
        return None
    return JanelaConfiguracaoPainel(
        pai,
        config,
        ao_aplicar,
        escopo_quantidade=escopo_quantidade,
        incluir_quantidade=incluir_quantidade,
    )
