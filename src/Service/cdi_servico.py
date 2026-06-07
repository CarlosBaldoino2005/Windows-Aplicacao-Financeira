"""Rendimento em 100% do CDI com taxas diarias do Banco Central (serie SGS 12)."""
from __future__ import annotations

from datetime import date, datetime

from src.Service.provedores.util_provedor import requisicao_json
from src.Tool.registrador_log import RegistradorLog

CODIGO_SERIE_CDI_DIARIO = 12
URL_SERIE_BCB = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

_log = RegistradorLog()


def _parse_data_texto(texto: str) -> date | None:
    """Converte data do grafico (dd/mm/aaaa ou com hora) para date."""
    parte = texto.strip().split()[0]
    try:
        return datetime.strptime(parte, "%d/%m/%Y").date()
    except ValueError:
        return None


def _formatar_data_bcb(data: date) -> str:
    return data.strftime("%d/%m/%Y")


class CdiServico:
    """Busca CDI diario no BCB e compoe o rendimento no intervalo informado."""

    def __init__(self) -> None:
        self._cache_taxas: dict[tuple[str, str], list[tuple[date, float]]] = {}

    def _buscar_taxas_periodo(self, data_inicio: date, data_fim: date) -> list[tuple[date, float]]:
        chave = (_formatar_data_bcb(data_inicio), _formatar_data_bcb(data_fim))
        if chave in self._cache_taxas:
            return self._cache_taxas[chave]

        url = (
            URL_SERIE_BCB.format(codigo=CODIGO_SERIE_CDI_DIARIO)
            + f"?formato=json&dataInicial={chave[0]}&dataFinal={chave[1]}"
        )
        dados = requisicao_json(url, log=_log)
        if not isinstance(dados, list):
            _log.aviso("Resposta invalida da API CDI do Banco Central.")
            return []

        taxas: list[tuple[date, float]] = []
        for item in dados:
            if not isinstance(item, dict):
                continue
            data_txt = item.get("data")
            valor_txt = item.get("valor")
            if not data_txt or valor_txt is None:
                continue
            data_item = _parse_data_texto(str(data_txt))
            if data_item is None:
                continue
            try:
                taxa_pct = float(str(valor_txt).replace(",", "."))
            except ValueError:
                continue
            taxas.append((data_item, taxa_pct))

        self._cache_taxas[chave] = taxas
        return taxas

    def calcular_rendimento(
        self,
        valor_inicial: float,
        texto_data_inicio: str,
        texto_data_fim: str,
    ) -> dict | None:
        """
        Aplica CDI (% ao dia, serie 12) em cada dia util entre as datas.
        Retorna valor final, rendimento em R$ e percentual no periodo.
        """
        data_ini = _parse_data_texto(texto_data_inicio)
        data_fim = _parse_data_texto(texto_data_fim)
        if data_ini is None or data_fim is None or data_fim < data_ini:
            return None
        if valor_inicial <= 0:
            return None

        taxas = self._buscar_taxas_periodo(data_ini, data_fim)
        if not taxas:
            return None

        valor = float(valor_inicial)
        dias_uteis = 0
        for data_taxa, taxa_pct in taxas:
            if data_ini <= data_taxa <= data_fim:
                valor *= 1.0 + taxa_pct / 100.0
                dias_uteis += 1

        if dias_uteis == 0:
            return None

        rendimento = valor - valor_inicial
        return {
            "valor_fim": round(valor, 2),
            "rendimento": round(rendimento, 2),
            "rendimento_pct": round((valor / valor_inicial - 1.0) * 100.0, 2),
            "dias_uteis": dias_uteis,
        }

    def calcular_rendimento_ate_vencimento(
        self,
        valor_inicial: float,
        texto_data_inicio: str,
        texto_data_fim: str,
    ) -> dict | None:
        """
        CDI historico (BCB) ate hoje e, se o vencimento for futuro,
        projeta o restante com a media anualizada dos ultimos ~90 dias uteis.
        """
        data_ini = _parse_data_texto(texto_data_inicio)
        data_fim = _parse_data_texto(texto_data_fim)
        if data_ini is None or data_fim is None or data_fim < data_ini:
            return None
        if valor_inicial <= 0:
            return None

        hoje = date.today()
        data_historico_fim = min(data_fim, hoje)

        valor = float(valor_inicial)
        dias_uteis = 0
        taxas = self._buscar_taxas_periodo(data_ini, data_historico_fim)
        if not taxas and data_historico_fim >= data_ini:
            taxas = self._buscar_taxas_periodo(
                date(data_ini.year, 1, 1),
                data_historico_fim,
            )

        for data_taxa, taxa_pct in taxas:
            if data_ini <= data_taxa <= data_historico_fim:
                valor *= 1.0 + taxa_pct / 100.0
                dias_uteis += 1

        projecao = False
        if data_fim > data_ini:
            taxas_ref = self._buscar_taxas_periodo(date(hoje.year, 1, 1), hoje)
            if not taxas_ref:
                taxas_ref = taxas
            taxas_recentes = [taxa for _, taxa in (taxas_ref or [])[-60:]]
            if taxas_recentes:
                media_diaria = sum(taxas_recentes) / len(taxas_recentes)
                taxa_aa = ((1.0 + media_diaria / 100.0) ** 252 - 1.0) * 100.0
                if dias_uteis == 0:
                    dias_projecao = (data_fim - data_ini).days
                elif data_fim > hoje:
                    dias_projecao = (data_fim - hoje).days
                else:
                    dias_projecao = 0
                if dias_projecao > 0 and taxa_aa > 0:
                    if dias_uteis == 0:
                        valor = float(valor_inicial)
                    valor *= (1.0 + taxa_aa / 100.0) ** (dias_projecao / 365.25)
                    projecao = True

        if dias_uteis == 0 and not projecao:
            return None

        rendimento = valor - valor_inicial
        resultado = {
            "valor_fim": round(valor, 2),
            "rendimento": round(rendimento, 2),
            "rendimento_pct": round((valor / valor_inicial - 1.0) * 100.0, 2),
            "dias_uteis": dias_uteis,
            "projecao_futura": projecao,
        }
        return resultado

    def fatores_cdi_acumulados(self, textos_data: list[str]) -> list[float] | None:
        """Fator multiplicador do CDI desde a 1ª data ate cada data da lista (1.0 no inicio)."""
        datas: list[date] = []
        for texto in textos_data:
            data_item = _parse_data_texto(str(texto))
            if data_item is None:
                return None
            datas.append(data_item)
        if not datas:
            return None

        taxas = self._buscar_taxas_periodo(datas[0], datas[-1])
        if not taxas:
            return None

        data_base = datas[0]
        fatores: list[float] = []
        for data_alvo in datas:
            fator = 1.0
            for data_cdi, taxa_pct in taxas:
                if data_base <= data_cdi <= data_alvo:
                    fator *= 1.0 + taxa_pct / 100.0
            fatores.append(round(fator, 8))
        return fatores

    def montar_linha_preco_equivalente_cdi(self, pontos: list[dict]) -> list[float] | None:
        """
        Valores para o grafico de preco: comeca no mesmo fechamento do 1º dia
        e evolui apenas com CDI (comparacao visual com a acao).
        """
        if not pontos:
            return None
        textos = [str(p["data"]) for p in pontos]
        fatores = self.fatores_cdi_acumulados(textos)
        if not fatores:
            return None
        try:
            preco_base = float(pontos[0]["fechamento"])
        except (KeyError, TypeError, ValueError):
            return None
        if preco_base <= 0:
            return None
        return [round(preco_base * fator, 4) for fator in fatores]

    def montar_indice_cdi_base100(self, textos_data: list[str]) -> list[float] | None:
        """Indice relativo (base 100) do CDI para grafico de comparacao."""
        fatores = self.fatores_cdi_acumulados(textos_data)
        if not fatores:
            return None
        return [round(fator * 100.0, 2) for fator in fatores]
