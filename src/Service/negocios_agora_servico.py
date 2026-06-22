"""Busca negocios intraday para a fita em tempo quase real do Agora."""
from __future__ import annotations

from datetime import date, datetime

from src.Model.negocio_agora import LadoNegocio, NegocioAgora, ResumoNegociosAgora, TendenciaNegocio
from src.Model.cotacao import PontoHistorico
from src.Service.provedores.provedor_yahoo_chart import ProvedorYahooChart
from src.Tool.cotacao_dual_helper import codigo_exibicao


class NegociosAgoraServico:
    """Converte candles intraday (1m) em linhas de negocios do dia."""

    _INTERVALOS = ("1m", "5m")

    def __init__(self) -> None:
        self._provedor = ProvedorYahooChart()

    def listar_negocios_do_dia(
        self,
        simbolo: str,
        data_ref: date | None = None,
    ) -> tuple[list[NegocioAgora], ResumoNegociosAgora, str | None]:
        dia = data_ref or date.today()
        serie = None
        for intervalo in self._INTERVALOS:
            serie = self._provedor.buscar_intraday_em_data(simbolo, dia, intervalo)
            if serie and serie.pontos:
                break

        if not serie or not serie.pontos:
            codigo = codigo_exibicao(simbolo)
            return [], ResumoNegociosAgora(0, 0, 0), (
                f"Negocios indisponiveis para {codigo} em "
                f"{dia.strftime('%d/%m/%Y')}."
            )

        negocios = self._converter_pontos(serie.pontos, simbolo)
        negocios.sort(key=lambda item: item.id, reverse=True)
        resumo = self._montar_resumo(negocios)
        return negocios, resumo, None

    def _converter_pontos(self, pontos: list[PontoHistorico], simbolo: str) -> list[NegocioAgora]:
        ordenados = sorted(pontos, key=lambda ponto: ponto.data_iso)
        resultado: list[NegocioAgora] = []
        preco_anterior: float | None = None
        bolsa = self._resolver_bolsa(simbolo)

        for indice, ponto in enumerate(ordenados, start=1):
            if not ponto.volume or int(ponto.volume) <= 0:
                continue

            preco = round(float(ponto.preco_fechamento), 4)
            hora = self._extrair_hora(ponto)
            if not hora:
                continue

            tendencia = self._calcular_tendencia(preco, preco_anterior, ponto)
            lado = self._inferir_lado(ponto, tendencia)
            preco_compra, preco_venda = self._estimar_book(preco, ponto, lado)

            resultado.append(
                NegocioAgora(
                    id=ponto.data_iso,
                    hora=hora,
                    preco=preco,
                    tamanho=int(ponto.volume),
                    tipo="",
                    lado=lado,
                    preco_compra=preco_compra,
                    preco_venda=preco_venda,
                    total_volume=1,
                    numero=indice,
                    bolsa=bolsa,
                    tendencia=tendencia,
                )
            )
            preco_anterior = preco

        return resultado

    @staticmethod
    def _montar_resumo(negocios: list[NegocioAgora]) -> ResumoNegociosAgora:
        compra = sum(1 for item in negocios if item.lado == "compra")
        venda = sum(1 for item in negocios if item.lado == "venda")
        neutro = sum(1 for item in negocios if item.lado == "neutro")
        return ResumoNegociosAgora(compra=compra, neutro=neutro, venda=venda)

    @staticmethod
    def _resolver_bolsa(simbolo: str) -> str:
        if simbolo.upper().endswith(".SA"):
            return "BOV"
        return "—"

    @staticmethod
    def _extrair_hora(ponto: PontoHistorico) -> str:
        texto = (ponto.data_iso or "").strip()
        if not texto:
            return ""
        try:
            instante = datetime.fromisoformat(texto.replace("Z", "+00:00"))
            return instante.strftime("%H:%M:%S")
        except ValueError:
            return ""

    @staticmethod
    def _calcular_tendencia(
        preco: float,
        preco_anterior: float | None,
        ponto: PontoHistorico,
    ) -> TendenciaNegocio:
        if preco_anterior is not None:
            if preco > preco_anterior:
                return "alta"
            if preco < preco_anterior:
                return "baixa"
            return "neutra"

        abertura = ponto.preco_abertura
        if abertura is None:
            return "neutra"
        if preco > abertura:
            return "alta"
        if preco < abertura:
            return "baixa"
        return "neutra"

    @staticmethod
    def _inferir_lado(ponto: PontoHistorico, tendencia: TendenciaNegocio) -> LadoNegocio:
        if tendencia == "alta":
            return "compra"
        if tendencia == "baixa":
            return "venda"

        abertura = ponto.preco_abertura
        if abertura is None:
            return "neutro"
        if ponto.preco_fechamento > abertura:
            return "compra"
        if ponto.preco_fechamento < abertura:
            return "venda"
        return "neutro"

    @staticmethod
    def _estimar_book(
        preco: float,
        ponto: PontoHistorico,
        lado: LadoNegocio,
    ) -> tuple[float | None, float | None]:
        abertura = ponto.preco_abertura
        spread = 0.01
        if abertura is not None:
            spread = max(0.01, round(abs(preco - abertura), 2))

        if lado == "compra":
            return round(preco - spread, 2), preco
        if lado == "venda":
            return preco, round(preco + spread, 2)
        if abertura is not None:
            menor = round(min(preco, abertura), 2)
            maior = round(max(preco, abertura), 2)
            return menor, maior
        return preco, preco
