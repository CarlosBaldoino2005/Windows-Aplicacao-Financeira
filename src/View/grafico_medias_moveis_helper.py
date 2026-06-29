"""Calculo, desenho e controles de medias moveis (MM e MME) nos graficos."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
import numpy as np

from src.Model.opcoes_medias_moveis_grafico import (
    PERIODO_MME_PADRAO,
    PERIODO_MM_PADRAO,
    OpcoesMediasMoveisGrafico,
)
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.icone_engrenagem_helper import criar_botao_engrenagem
from src.Tool.janela_helper import (
    centralizar_janela_sobre_referencia,
    configurar_janela_filha_modal,
    liberar_modal_janela_filha,
)
from src.Tool.validadores import validar_periodo_media_movel
from src.View.tema import CORES

_COR_MM = "#A855F7"
_COR_MME = "#F59E0B"
_LARGURA_MEDIA = 1.6
_LARGURA_DIALOG_MEDIAS = 460
_ALTURA_DIALOG_MEDIAS = 480


def calcular_sma(fechamentos: list[float], periodo: int) -> list[float | None]:
    """Media movel simples sobre o fechamento."""
    if periodo < 2 or not fechamentos:
        return []

    resultado: list[float | None] = [None] * len(fechamentos)
    soma = 0.0
    for indice, valor in enumerate(fechamentos):
        soma += float(valor)
        if indice >= periodo:
            soma -= float(fechamentos[indice - periodo])
        if indice >= periodo - 1:
            resultado[indice] = soma / periodo
    return resultado


def calcular_ema(fechamentos: list[float], periodo: int) -> list[float | None]:
    """Media movel exponencial sobre o fechamento."""
    if periodo < 2 or not fechamentos:
        return []

    resultado: list[float | None] = [None] * len(fechamentos)
    if len(fechamentos) < periodo:
        return resultado

    multiplicador = 2.0 / (periodo + 1)
    ema = sum(float(valor) for valor in fechamentos[:periodo]) / periodo
    resultado[periodo - 1] = ema

    for indice in range(periodo, len(fechamentos)):
        preco = float(fechamentos[indice])
        ema = (preco - ema) * multiplicador + ema
        resultado[indice] = ema

    return resultado


def valores_medias_para_limites(
    fechamentos: list[float],
    opcoes: OpcoesMediasMoveisGrafico,
) -> list[float]:
    """Valores das medias ativas para expandir o eixo Y."""
    extras: list[float] = []
    if opcoes.mm_ativa:
        extras.extend(
            valor
            for valor in calcular_sma(fechamentos, opcoes.mm_periodo)
            if valor is not None
        )
    if opcoes.mme_ativa:
        extras.extend(
            valor
            for valor in calcular_ema(fechamentos, opcoes.mme_periodo)
            if valor is not None
        )
    return extras


def desenhar_medias_moveis(
    eixo,
    posicoes_x: list[float] | np.ndarray,
    fechamentos: list[float],
    opcoes: OpcoesMediasMoveisGrafico,
) -> bool:
    """Desenha MM e MME sobre o grafico de preco. Retorna True se desenhou alguma linha."""
    if not fechamentos or not opcoes.alguma_ativa():
        return False

    xs = np.asarray(posicoes_x, dtype=float)
    desenhou = False

    if opcoes.mm_ativa:
        serie_mm = calcular_sma(fechamentos, opcoes.mm_periodo)
        if _plotar_serie_media(
            eixo,
            xs,
            serie_mm,
            cor=_COR_MM,
            rotulo=f"MM {opcoes.mm_periodo}",
        ):
            desenhou = True

    if opcoes.mme_ativa:
        serie_mme = calcular_ema(fechamentos, opcoes.mme_periodo)
        if _plotar_serie_media(
            eixo,
            xs,
            serie_mme,
            cor=_COR_MME,
            rotulo=f"MME {opcoes.mme_periodo}",
        ):
            desenhou = True

    return desenhou


def aplicar_legenda_com_medias(eixo, *, loc: str = "upper left") -> None:
    """Atualiza legenda incluindo MM/MME e demais series rotuladas."""
    legenda_atual = eixo.get_legend()
    if legenda_atual is not None:
        legenda_atual.remove()
    legenda = eixo.legend(loc=loc, fontsize=8, framealpha=0.85)
    if legenda is None:
        return
    fundo = CORES.get("graficoFundo", CORES["superficie"])
    moldura = legenda.get_frame()
    moldura.set_facecolor(fundo)
    moldura.set_edgecolor(CORES.get("borda", "#E2E8F0"))
    for texto in legenda.get_texts():
        texto.set_color(CORES["texto"])


def _plotar_serie_media(
    eixo,
    posicoes_x: np.ndarray,
    serie: list[float | None],
    *,
    cor: str,
    rotulo: str,
) -> bool:
    xs_plot: list[float] = []
    ys_plot: list[float] = []
    for x, y in zip(posicoes_x, serie, strict=False):
        if y is None:
            continue
        xs_plot.append(float(x))
        ys_plot.append(float(y))

    if len(xs_plot) < 2:
        return False

    eixo.plot(
        xs_plot,
        ys_plot,
        color=cor,
        linewidth=_LARGURA_MEDIA,
        label=rotulo,
        zorder=4,
    )
    return True


def _montar_rotulo_coluna_media(
    pai: ctk.CTkFrame,
    titulo: str,
    descricao: str,
    cor: str,
    *,
    wraplength: int = 150,
) -> ctk.CTkFrame:
    """Titulo e descricao acima de cada controle, com faixa na cor da linha no grafico."""
    bloco = ctk.CTkFrame(pai, fg_color="transparent")
    bloco.pack(anchor="w", fill="x", pady=(0, 12))

    linha_titulo = ctk.CTkFrame(bloco, fg_color="transparent")
    linha_titulo.pack(anchor="w")

    ctk.CTkFrame(
        linha_titulo,
        width=16,
        height=3,
        fg_color=cor,
        corner_radius=2,
    ).pack(side="left", padx=(0, 6), pady=(0, 1))

    ctk.CTkLabel(
        linha_titulo,
        text=titulo,
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=CORES["texto"],
        anchor="w",
    ).pack(side="left")

    ctk.CTkLabel(
        bloco,
        text=descricao,
        font=ctk.CTkFont(size=10),
        text_color=CORES["textoSecundario"],
        anchor="w",
        wraplength=wraplength,
        justify="left",
    ).pack(anchor="w", pady=(2, 4))

    return bloco


def _montar_conteudo_config_medias_moveis(
    pai: ctk.CTkFrame,
    *,
    opcoes_iniciais: OpcoesMediasMoveisGrafico,
    estado: dict[str, object],
    config: ConfigPainelIni,
    ao_alterar: Callable[[], None],
    label_erro: ctk.CTkLabel,
) -> None:
    """Monta checkboxes e periodos de MM/MME dentro do modal de configuracao."""
    cabecalho = ctk.CTkFrame(pai, fg_color="transparent")
    cabecalho.pack(anchor="w", fill="x", padx=8, pady=(8, 8))

    ctk.CTkLabel(
        cabecalho,
        text="Medias moveis",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=CORES["texto"],
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        cabecalho,
        text="Linhas sobre o preco de fechamento; periodo = quantidade de candles.",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
        anchor="w",
        wraplength=380,
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    corpo = ctk.CTkFrame(pai, fg_color="transparent")
    corpo.pack(anchor="w", fill="x", padx=8, pady=(4, 0))

    coluna_mm = _montar_rotulo_coluna_media(
        corpo,
        "MM — Media movel simples",
        "Media aritmetica dos ultimos fechamentos.",
        _COR_MM,
        wraplength=380,
    )
    coluna_mme = _montar_rotulo_coluna_media(
        corpo,
        "MME — Media movel exponencial",
        "Da mais peso aos fechamentos recentes.",
        _COR_MME,
        wraplength=380,
    )

    linha_mm = ctk.CTkFrame(coluna_mm, fg_color="transparent")
    linha_mm.pack(anchor="w")

    check_mm = ctk.CTkCheckBox(
        linha_mm,
        text="Exibir",
        width=72,
        font=ctk.CTkFont(size=11),
        checkbox_width=18,
        checkbox_height=18,
    )
    if opcoes_iniciais.mm_ativa:
        check_mm.select()
    check_mm.pack(side="left", padx=(0, 6))

    ctk.CTkLabel(
        linha_mm,
        text="Periodo",
        font=ctk.CTkFont(size=10),
        text_color=CORES["textoSecundario"],
    ).pack(side="left", padx=(0, 4))

    entrada_mm = ctk.CTkEntry(linha_mm, width=44, height=28, justify="center")
    entrada_mm.insert(0, str(opcoes_iniciais.mm_periodo))
    entrada_mm.pack(side="left")

    linha_mme = ctk.CTkFrame(coluna_mme, fg_color="transparent")
    linha_mme.pack(anchor="w")

    check_mme = ctk.CTkCheckBox(
        linha_mme,
        text="Exibir",
        width=72,
        font=ctk.CTkFont(size=11),
        checkbox_width=18,
        checkbox_height=18,
    )
    if opcoes_iniciais.mme_ativa:
        check_mme.select()
    check_mme.pack(side="left", padx=(0, 6))

    ctk.CTkLabel(
        linha_mme,
        text="Periodo",
        font=ctk.CTkFont(size=10),
        text_color=CORES["textoSecundario"],
    ).pack(side="left", padx=(0, 4))

    entrada_mme = ctk.CTkEntry(linha_mme, width=44, height=28, justify="center")
    entrada_mme.insert(0, str(opcoes_iniciais.mme_periodo))
    entrada_mme.pack(side="left")

    label_erro.pack(anchor="w", padx=8, pady=(4, 8))

    def ler_opcoes_da_tela() -> tuple[OpcoesMediasMoveisGrafico | None, str | None]:
        mm_periodo, erro_mm = validar_periodo_media_movel(
            entrada_mm.get(),
            padrao=PERIODO_MM_PADRAO,
        )
        mme_periodo, erro_mme = validar_periodo_media_movel(
            entrada_mme.get(),
            padrao=PERIODO_MME_PADRAO,
        )
        if erro_mm:
            return None, erro_mm
        if erro_mme:
            return None, erro_mme
        return (
            OpcoesMediasMoveisGrafico(
                mm_ativa=bool(check_mm.get()),
                mm_periodo=mm_periodo or PERIODO_MM_PADRAO,
                mme_ativa=bool(check_mme.get()),
                mme_periodo=mme_periodo or PERIODO_MME_PADRAO,
            ),
            None,
        )

    def aplicar_mudanca() -> None:
        opcoes, erro = ler_opcoes_da_tela()
        if erro:
            label_erro.configure(text=erro)
            return
        label_erro.configure(text="")
        assert opcoes is not None
        estado["opcoes"] = opcoes
        try:
            config.salvar_opcoes_medias_moveis_grafico(opcoes)
        except OSError:
            label_erro.configure(text="Nao foi possivel salvar no painel.ini.")
            return
        ao_alterar()

    def ao_toggle_checkbox() -> None:
        aplicar_mudanca()

    check_mm.configure(command=ao_toggle_checkbox)
    check_mme.configure(command=ao_toggle_checkbox)

    for entrada in (entrada_mm, entrada_mme):
        entrada.bind("<Return>", lambda _evento: aplicar_mudanca())
        entrada.bind("<FocusOut>", lambda _evento: aplicar_mudanca())


def _abrir_dialogo_config_medias_moveis(
    janela_pai: ctk.CTkBaseClass,
    *,
    estado: dict[str, object],
    config: ConfigPainelIni,
    ao_alterar: Callable[[], None],
) -> None:
    dialogo_existente = estado.get("dialogo")
    if isinstance(dialogo_existente, ctk.CTkToplevel):
        try:
            if dialogo_existente.winfo_exists():
                dialogo_existente.focus_force()
                dialogo_existente.lift()
                return
        except Exception:
            pass

    dialogo = ctk.CTkToplevel(janela_pai)
    estado["dialogo"] = dialogo
    dialogo.title("Medias moveis do grafico")
    dialogo.configure(fg_color=CORES["fundo"])
    dialogo.resizable(False, False)
    dialogo.geometry(f"{_LARGURA_DIALOG_MEDIAS}x{_ALTURA_DIALOG_MEDIAS}")
    dialogo.minsize(_LARGURA_DIALOG_MEDIAS, _ALTURA_DIALOG_MEDIAS)

    painel = ctk.CTkFrame(dialogo, fg_color=CORES["superficie"], corner_radius=12)
    painel.pack(fill="both", expand=True, padx=16, pady=16)

    def ao_fechar() -> None:
        liberar_modal_janela_filha(dialogo)
        estado["dialogo"] = None
        dialogo.destroy()

    barra = ctk.CTkFrame(painel, fg_color="transparent")
    barra.pack(side="bottom", fill="x", padx=16, pady=(8, 16))
    ctk.CTkButton(
        barra,
        text="Fechar",
        width=120,
        fg_color=CORES["primaria"],
        hover_color=CORES["primariaHover"],
        text_color=CORES.get("textoInverso", "#FFFFFF"),
        command=ao_fechar,
    ).pack(side="right")

    conteudo = ctk.CTkFrame(painel, fg_color="transparent")
    conteudo.pack(fill="both", expand=True, padx=8, pady=(8, 0))

    label_erro = ctk.CTkLabel(
        conteudo,
        text="",
        font=ctk.CTkFont(size=11),
        text_color=CORES["erro"],
        anchor="w",
    )

    opcoes_atuais = estado["opcoes"]
    assert isinstance(opcoes_atuais, OpcoesMediasMoveisGrafico)

    _montar_conteudo_config_medias_moveis(
        conteudo,
        opcoes_iniciais=opcoes_atuais,
        estado=estado,
        config=config,
        ao_alterar=ao_alterar,
        label_erro=label_erro,
    )

    dialogo.protocol("WM_DELETE_WINDOW", ao_fechar)
    dialogo.update_idletasks()
    try:
        centralizar_janela_sobre_referencia(
            dialogo,
            janela_pai,
            _LARGURA_DIALOG_MEDIAS,
            _ALTURA_DIALOG_MEDIAS,
        )
    except Exception:
        pass
    configurar_janela_filha_modal(dialogo, janela_pai)
    dialogo.focus_force()


def montar_botao_config_medias_moveis_grafico(
    pai: ctk.CTkFrame,
    config: ConfigPainelIni,
    ao_alterar: Callable[[], None],
) -> ctk.CTkFrame:
    """Botao de engrenagem que abre o modal de MM/MME na barra do grafico."""
    opcoes_iniciais = config.carregar_opcoes_medias_moveis_grafico()
    estado: dict[str, object] = {"opcoes": opcoes_iniciais, "dialogo": None}

    frame = ctk.CTkFrame(pai, fg_color="transparent")
    frame.pack(side="left", padx=(8, 0))

    janela_pai = pai.winfo_toplevel()

    criar_botao_engrenagem(
        frame,
        command=lambda: _abrir_dialogo_config_medias_moveis(
            janela_pai,
            estado=estado,
            config=config,
            ao_alterar=ao_alterar,
        ),
        width=36,
        height=36,
    ).pack(side="left")

    def obter_opcoes() -> OpcoesMediasMoveisGrafico:
        opcoes = estado["opcoes"]
        assert isinstance(opcoes, OpcoesMediasMoveisGrafico)
        return opcoes

    frame.obter_opcoes_medias_moveis = obter_opcoes  # type: ignore[attr-defined]
    return frame


def obter_opcoes_medias_do_frame(controles: ctk.CTkFrame | None) -> OpcoesMediasMoveisGrafico:
    """Le opcoes atuais dos controles ou retorna padrao desligado."""
    if controles is None:
        return OpcoesMediasMoveisGrafico()
    obter = getattr(controles, "obter_opcoes_medias_moveis", None)
    if callable(obter):
        return obter()
    return OpcoesMediasMoveisGrafico()
