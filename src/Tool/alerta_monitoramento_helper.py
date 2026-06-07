"""Alertas visuais e notificacoes quando itens saem dos limites de monitoramento."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import customtkinter as ctk

from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Model.monitoramento import MonitoramentoLinha
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.View.botao_helper import estilo_botao_icone, estilo_botao_padrao
from src.View.formatadores import formatar_moeda
from src.View.tema import CORES


@dataclass(frozen=True)
class AlertaMonitoramentoItem:
    """Dados de um ativo fora do limite configurado."""

    linha: MonitoramentoLinha
    titulo: str
    mensagem: str


def _cor_hover_aviso() -> str:
    return CORES.get("avisoHover", "#B45309")


def obter_alertas_monitoramento() -> tuple[list[AlertaMonitoramentoItem], bool]:
    """
    Retorna alertas de itens fora do limite e se o monitoramento global esta ativo.
    Segundo valor False quando o monitoramento esta pausado globalmente.
    """
    config = ConfigPainelIni()
    if config.carregar_monitoramento_pausado():
        return [], False

    linhas, _ = ControladorMonitoramento().obter_linhas_monitoramento()
    alertas: list[AlertaMonitoramentoItem] = []
    for linha in linhas:
        if linha.item.pausado:
            continue
        if linha.status not in ("abaixo", "acima"):
            continue
        alertas.append(_montar_alerta(linha))

    return alertas, True


def _montar_alerta(linha: MonitoramentoLinha) -> AlertaMonitoramentoItem:
    codigo = codigo_exibicao(linha.item.simbolo)
    moeda = linha.cotacao.moeda if linha.cotacao is not None else "BRL"
    preco = (
        linha.cotacao.preco
        if linha.cotacao is not None and linha.cotacao.preco > 0
        else None
    )
    preco_texto = formatar_moeda(preco, moeda) if preco is not None else "indisponivel"

    if linha.status == "abaixo":
        limite = linha.item.valor_baixo
        limite_texto = (
            formatar_moeda(limite, moeda) if limite is not None else "nao definido"
        )
        titulo = f"{codigo} abaixo do limite"
        mensagem = f"Preco atual: {preco_texto} | Limite baixo: {limite_texto}"
    else:
        limite = linha.item.valor_alto
        limite_texto = (
            formatar_moeda(limite, moeda) if limite is not None else "nao definido"
        )
        titulo = f"{codigo} acima do limite"
        mensagem = f"Preco atual: {preco_texto} | Limite alto: {limite_texto}"

    return AlertaMonitoramentoItem(linha=linha, titulo=titulo, mensagem=mensagem)


def notificar_alertas_windows(alertas: list[AlertaMonitoramentoItem]) -> int:
    """Envia uma notificacao do Windows para cada alerta. Retorna quantidade enviada."""
    from src.Tool.notificacao_windows_helper import enviar_varias_notificacoes_windows

    pares = [(alerta.titulo, alerta.mensagem) for alerta in alertas]
    return enviar_varias_notificacoes_windows(pares)


def aplicar_destaque_alerta_ui(
    botao_icone: ctk.CTkButton | None,
    botao_monitoramento: ctk.CTkButton | None,
) -> None:
    """Icone e botao Monitoramento ficam amarelos (aviso)."""
    if botao_icone is not None:
        try:
            botao_icone.configure(
                text_color=CORES["aviso"],
                hover_color=CORES.get("avisoFundo", CORES["zebraEscura"]),
            )
        except Exception:
            pass

    if botao_monitoramento is not None:
        try:
            botao_monitoramento.configure(
                fg_color=CORES["aviso"],
                hover_color=_cor_hover_aviso(),
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            )
        except Exception:
            pass


def remover_destaque_alerta_ui(
    botao_icone: ctk.CTkButton | None,
    botao_monitoramento: ctk.CTkButton | None,
) -> None:
    """Restaura o visual padrao (icone transparente azul, botao azul)."""
    if botao_icone is not None:
        try:
            botao_icone.configure(**estilo_botao_icone())
        except Exception:
            pass

    if botao_monitoramento is not None:
        try:
            botao_monitoramento.configure(**estilo_botao_padrao(height=36))
        except Exception:
            pass


def widget_ainda_existe(widget: Any) -> bool:
    if widget is None:
        return False
    try:
        return bool(widget.winfo_exists())
    except Exception:
        return False
