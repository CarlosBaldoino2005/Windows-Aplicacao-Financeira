"""Monta dados e gera PDF do relatorio da carteira."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.Model.carteira import ROTULOS_TIPO_CARTEIRA, LinhaCarteira
from src.Model.cotacao import PontoHistorico
from src.Model.relatorio_carteira import (
    DadosRelatorioCarteira,
    LinhaRelatorioMercado,
    LinhaRelatorioPosicao,
    OhlcDia,
    ResumoRelatorioCarteira,
)
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.mercado_servico import MercadoServico
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.registrador_log import RegistradorLog
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.tabela_carteira_helper import _formatar_quantidade


class RelatorioCarteiraServico:
    """Coleta cotacoes do dia e grava relatorio em PDF na pasta Relatorios."""

    _PASTA_RELATORIOS = "Relatorios"
    _QUANTIDADE_DESTAQUES = 12
    _PAGINA_PDF = landscape(A4)
    _MARGEM_PDF_CM = 1.2

    def __init__(self, pasta_base: Path | None = None) -> None:
        self._raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_relatorios = self._raiz / self._PASTA_RELATORIOS
        self._mercado_acoes = MercadoServico()
        self._mercado_fiis = MercadoFiisServico()
        self._log = RegistradorLog(self._raiz)

    def montar_dados(self, linhas: list[LinhaCarteira]) -> DadosRelatorioCarteira:
        """Monta o pacote de dados a partir das linhas atuais da carteira."""
        agora = datetime.now()
        avisos: list[str] = []

        total_investido = sum(l.posicao.valor_investido for l in linhas)
        total_atual = sum(l.valor_atual or 0 for l in linhas)
        resultado = round(total_atual - total_investido, 2)
        resultado_pct = round((resultado / total_investido) * 100, 2) if total_investido else 0.0
        total_dividendos = round(sum(l.dividendos_recebidos for l in linhas), 2)
        dividendo_prev = round(
            sum(l.dividendo_previsto_proximo_mes or 0 for l in linhas),
            2,
        )

        resumo = ResumoRelatorioCarteira(
            total_investido=round(total_investido, 2),
            total_atual=round(total_atual, 2),
            resultado_reais=resultado,
            resultado_pct=resultado_pct,
            total_dividendos=total_dividendos,
            dividendo_previsto_mes=dividendo_prev,
        )

        posicoes_relatorio: list[LinhaRelatorioPosicao] = []
        for linha in linhas:
            moeda = linha.cotacao.moeda if linha.cotacao else "BRL"
            ohlc, aviso_ohlc = self._buscar_ohlc_dia(linha.posicao.simbolo, linha.posicao.tipo_ativo)
            if aviso_ohlc:
                avisos.append(aviso_ohlc)

            posicoes_relatorio.append(
                LinhaRelatorioPosicao(
                    simbolo=linha.posicao.simbolo,
                    codigo=codigo_exibicao(linha.posicao.simbolo),
                    nome=linha.cotacao.nome if linha.cotacao else codigo_exibicao(linha.posicao.simbolo),
                    tipo=linha.posicao.tipo_ativo,
                    quantidade=linha.posicao.quantidade,
                    preco_compra=linha.posicao.preco_compra,
                    valor_investido=linha.posicao.valor_investido,
                    preco_atual=linha.preco_atual,
                    valor_atual=linha.valor_atual,
                    variacao_dia_pct=linha.cotacao.variacao_percentual if linha.cotacao else None,
                    resultado_reais=linha.resultado_reais,
                    resultado_pct=linha.resultado_percentual,
                    moeda=moeda,
                    ohlc_dia=ohlc,
                )
            )

        acoes_alta = self._listar_mercado(
            self._mercado_acoes.listar_em_alta,
            self._QUANTIDADE_DESTAQUES,
            "acoes",
        )
        acoes_queda = self._listar_mercado(
            self._mercado_acoes.listar_em_queda,
            self._QUANTIDADE_DESTAQUES,
            "acoes",
        )
        fiis_alta = self._listar_mercado(
            self._mercado_fiis.listar_em_alta,
            self._QUANTIDADE_DESTAQUES,
            "fiis",
        )
        fiis_queda = self._listar_mercado(
            self._mercado_fiis.listar_em_queda,
            self._QUANTIDADE_DESTAQUES,
            "fiis",
        )

        return DadosRelatorioCarteira(
            gerado_em=agora.strftime("%d/%m/%Y %H:%M:%S"),
            resumo=resumo,
            posicoes=posicoes_relatorio,
            acoes_em_alta=acoes_alta,
            acoes_em_queda=acoes_queda,
            fiis_em_alta=fiis_alta,
            fiis_em_queda=fiis_queda,
            avisos=avisos,
        )

    @staticmethod
    def formatar_assunto_resumo_carteira(resumo: ResumoRelatorioCarteira) -> str:
        """Texto do resumo consolidado para o assunto do e-mail."""
        return (
            f"Investido {formatar_moeda(resumo.total_investido)}"
            f" | Atual {formatar_moeda(resumo.total_atual)}"
            f" | Resultado {formatar_variacao(resumo.resultado_reais, resumo.resultado_pct)}"
            f" | Dividendos {formatar_moeda(resumo.total_dividendos)}"
            f" | Prev. mes {formatar_moeda(resumo.dividendo_previsto_mes)}"
        )

    def gerar_pdf(self, dados: DadosRelatorioCarteira) -> Path:
        """Grava o PDF e retorna o caminho completo."""
        self._pasta_relatorios.mkdir(parents=True, exist_ok=True)
        nome = f"relatorio-{datetime.now().strftime('%d-%m-%Y %H-%M-%S')}.pdf"
        caminho = self._pasta_relatorios / nome
        self._escrever_pdf(caminho, dados)
        self._log.info(f"Relatorio da carteira gerado: {caminho.name}")
        return caminho

    @staticmethod
    def abrir_pdf_no_sistema(caminho: Path) -> str | None:
        """Abre o PDF com o programa padrao do Windows."""
        try:
            os.startfile(str(caminho.resolve()))
        except OSError as exc:
            return f"PDF salvo, mas nao foi possivel abrir automaticamente: {exc}"
        return None

    def _buscar_ohlc_dia(
        self,
        simbolo: str,
        tipo_ativo: str,
    ) -> tuple[OhlcDia | None, str | None]:
        mercado = self._mercado_fiis if tipo_ativo == "fiis" else self._mercado_acoes
        if tipo_ativo == "cripto":
            from src.Service.mercado_cripto_servico import MercadoCriptoServico

            mercado = MercadoCriptoServico()

        try:
            serie = mercado.buscar_historico(simbolo, "dia")
        except Exception as exc:
            return None, f"OHLC indisponivel para {codigo_exibicao(simbolo)}: {exc}"

        if not serie or not serie.pontos:
            return None, f"Sem dados intradiarios para {codigo_exibicao(simbolo)}."

        ohlc = _calcular_ohlc_intraday(serie.pontos)
        if ohlc is None:
            return None, f"Nao foi possivel calcular OHLC de {codigo_exibicao(simbolo)}."
        return ohlc, None

    def _listar_mercado(
        self,
        metodo,
        quantidade: int,
        tipo_ativo: str,
    ) -> list[LinhaRelatorioMercado]:
        try:
            resumos = metodo(quantidade)
        except Exception as exc:
            self._log.aviso(f"Falha ao listar mercado para relatorio: {exc}")
            return []

        linhas: list[LinhaRelatorioMercado] = []
        for item in resumos:
            ohlc, _ = self._buscar_ohlc_dia(item.simbolo, tipo_ativo)
            linhas.append(
                LinhaRelatorioMercado(
                    simbolo=item.simbolo,
                    codigo=codigo_exibicao(item.simbolo),
                    nome=item.nome,
                    preco=item.preco,
                    variacao_pct=item.variacao_percentual,
                    variacao_valor=item.variacao_valor,
                    moeda=item.moeda,
                    ohlc_dia=ohlc,
                )
            )
        return linhas

    def _escrever_pdf(self, caminho: Path, dados: DadosRelatorioCarteira) -> None:
        margem = self._MARGEM_PDF_CM * cm
        doc = SimpleDocTemplate(
            str(caminho),
            pagesize=self._PAGINA_PDF,
            leftMargin=margem,
            rightMargin=margem,
            topMargin=margem,
            bottomMargin=margem,
            title="Relatorio Carteira Financeiro",
        )

        estilos = getSampleStyleSheet()
        titulo = ParagraphStyle(
            "TituloRelatorio",
            parent=estilos["Heading1"],
            fontSize=16,
            spaceAfter=8,
        )
        subtitulo = ParagraphStyle(
            "SubtituloRelatorio",
            parent=estilos["Heading2"],
            fontSize=12,
            spaceBefore=14,
            spaceAfter=6,
        )
        corpo = estilos["Normal"]

        elementos: list = []
        elementos.append(Paragraph("Relatorio da Carteira de Investimentos", titulo))
        elementos.append(Paragraph(f"Gerado em: {dados.gerado_em}", corpo))
        elementos.append(Spacer(1, 0.3 * cm))

        resumo = dados.resumo
        linhas_resumo = [
            ["Indicador", "Valor"],
            ["Total investido", formatar_moeda(resumo.total_investido)],
            ["Valor atual", formatar_moeda(resumo.total_atual)],
            [
                "Resultado",
                formatar_variacao(resumo.resultado_reais, resumo.resultado_pct),
            ],
            ["Dividendos recebidos", formatar_moeda(resumo.total_dividendos)],
            ["Dividendo prev. proximo mes", formatar_moeda(resumo.dividendo_previsto_mes)],
        ]
        elementos.append(Paragraph("Resumo consolidado", subtitulo))
        elementos.append(_tabela_pdf(linhas_resumo, [7 * cm, 12 * cm]))

        if dados.posicoes:
            elementos.append(Paragraph("Posicoes da carteira (dia)", subtitulo))
            cabecalho = [
                "Ativo",
                "Tipo",
                "Qtd",
                "V/cota",
                "V. compr.",
                *_cabecalho_ohlc_pdf(),
                "Var. dia",
                "Ganho/Perda",
            ]
            linhas_tabela = [cabecalho]
            for item in dados.posicoes:
                linhas_tabela.append(
                    [
                        item.codigo,
                        ROTULOS_TIPO_CARTEIRA.get(item.tipo, item.tipo),
                        _formatar_quantidade(item.quantidade),
                        formatar_moeda(item.preco_compra, item.moeda),
                        formatar_moeda(item.valor_investido, item.moeda),
                        *_celulas_ohlc_pdf(item.ohlc_dia, item.moeda, item.preco_atual),
                        _fmt_pct(item.variacao_dia_pct),
                        _fmt_resultado_posicao(item),
                    ]
                )
            elementos.append(
                _tabela_pdf(
                    linhas_tabela,
                    _larguras_tabela_posicoes_pdf(),
                    tamanho_fonte=8,
                )
            )

        elementos.extend(
            self._secao_mercado_pdf(subtitulo, "Acoes em alta no mercado", dados.acoes_em_alta)
        )
        elementos.extend(
            self._secao_mercado_pdf(subtitulo, "Acoes em queda no mercado", dados.acoes_em_queda)
        )
        elementos.extend(
            self._secao_mercado_pdf(subtitulo, "FIIs em alta no mercado", dados.fiis_em_alta)
        )
        elementos.extend(
            self._secao_mercado_pdf(subtitulo, "FIIs em queda no mercado", dados.fiis_em_queda)
        )

        if dados.avisos:
            elementos.append(Paragraph("Observacoes", subtitulo))
            for aviso in dados.avisos[:20]:
                elementos.append(Paragraph(f"• {aviso}", corpo))

        doc.build(elementos)

    def _secao_mercado_pdf(
        self,
        estilo_subtitulo: ParagraphStyle,
        titulo: str,
        itens: list[LinhaRelatorioMercado],
    ) -> list:
        if not itens:
            return []
        linhas = [["Codigo", "Nome", *_cabecalho_ohlc_pdf(), "Variacao"]]
        for item in itens:
            linhas.append(
                [
                    item.codigo,
                    _truncar(item.nome, 42),
                    *_celulas_ohlc_pdf(item.ohlc_dia, item.moeda, item.preco),
                    formatar_variacao(item.variacao_valor, item.variacao_pct, item.moeda),
                ]
            )
        return [
            Paragraph(titulo, estilo_subtitulo),
            _tabela_pdf(
                linhas,
                _larguras_tabela_mercado_pdf(),
                tamanho_fonte=8,
            ),
        ]


def _calcular_ohlc_intraday(pontos: list[PontoHistorico]) -> OhlcDia | None:
    if not pontos:
        return None

    abertura = pontos[0].preco_abertura or pontos[0].preco_fechamento
    fechamento = pontos[-1].preco_fechamento
    maxima = float("-inf")
    minima = float("inf")
    horario_maxima = ""
    horario_minima = ""

    for ponto in pontos:
        valores = [ponto.preco_fechamento]
        if ponto.preco_abertura is not None:
            valores.append(ponto.preco_abertura)
        for valor in valores:
            if valor > maxima:
                maxima = valor
                horario_maxima = _extrair_hora(ponto.data_exibicao)
            if valor < minima:
                minima = valor
                horario_minima = _extrair_hora(ponto.data_exibicao)

    if maxima == float("-inf") or minima == float("inf"):
        return None

    return OhlcDia(
        abertura=round(abertura, 4),
        maxima=round(maxima, 4),
        minima=round(minima, 4),
        fechamento=round(fechamento, 4),
        horario_maxima=horario_maxima or "—",
        horario_minima=horario_minima or "—",
    )


def _extrair_hora(data_exibicao: str) -> str:
    texto = (data_exibicao or "").strip()
    if " " in texto:
        return texto.split(" ", 1)[1]
    return "—"


def _cabecalho_ohlc_pdf() -> list[str]:
    return [
        "Abr.",
        "Max.",
        "Hr.max",
        "Min.",
        "Hr.min",
        "Fech.",
    ]


def _larguras_tabela_mercado_pdf() -> list[float]:
    """Larguras para tabelas de alta/queda (paisagem A4)."""
    return [
        1.6 * cm,
        6.2 * cm,
        2.0 * cm,
        2.0 * cm,
        1.6 * cm,
        2.0 * cm,
        1.6 * cm,
        2.0 * cm,
        4.2 * cm,
    ]


def _larguras_tabela_posicoes_pdf() -> list[float]:
    """Larguras para posicoes da carteira (paisagem A4)."""
    return [
        1.6 * cm,
        1.5 * cm,
        1.2 * cm,
        2.0 * cm,
        2.2 * cm,
        2.0 * cm,
        2.0 * cm,
        1.6 * cm,
        2.0 * cm,
        1.6 * cm,
        2.0 * cm,
        1.8 * cm,
        3.0 * cm,
    ]


def _celulas_ohlc_pdf(
    ohlc: OhlcDia | None,
    moeda: str,
    preco_fechamento: float | None = None,
) -> list[str]:
    return [
        _fmt_preco(ohlc.abertura if ohlc else None, moeda),
        _fmt_preco(ohlc.maxima if ohlc else None, moeda),
        ohlc.horario_maxima if ohlc else "—",
        _fmt_preco(ohlc.minima if ohlc else None, moeda),
        ohlc.horario_minima if ohlc else "—",
        _fmt_preco(
            ohlc.fechamento if ohlc else preco_fechamento,
            moeda,
        ),
    ]


def _fmt_preco(valor: float | None, moeda: str) -> str:
    if valor is None:
        return "—"
    return formatar_moeda(valor, moeda)


def _fmt_pct(valor: float | None) -> str:
    if valor is None:
        return "—"
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{valor:.2f}%"


def _fmt_resultado_posicao(item: LinhaRelatorioPosicao) -> str:
    if item.resultado_reais is None or item.resultado_pct is None:
        return "—"
    return formatar_variacao(item.resultado_reais, item.resultado_pct, item.moeda)


def _truncar(texto: str, limite: int) -> str:
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1] + "…"


def _tabela_pdf(
    linhas: list[list[str]],
    larguras: list[float],
    *,
    tamanho_fonte: int = 9,
) -> Table:
    tabela = Table(linhas, colWidths=larguras, repeatRows=1)
    zebra_clara = colors.white
    zebra_escura = colors.HexColor("#EEF2F7")
    tamanho_cabecalho = max(6, tamanho_fonte - 1)

    comandos: list = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), tamanho_cabecalho),
        ("FONTSIZE", (0, 1), (-1, -1), tamanho_fonte),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]

    for indice in range(1, len(linhas)):
        cor_fundo = zebra_clara if indice % 2 == 1 else zebra_escura
        comandos.append(("BACKGROUND", (0, indice), (-1, indice), cor_fundo))

    tabela.setStyle(TableStyle(comandos))
    return tabela
