"""Busca cotacoes e historico com fallback automatico entre provedores."""
from datetime import datetime

from src.Model.acoes_universo import ACOES_MONITORADAS, ACOES_PADRAO, LIMITE_ACOES_PAINEL
from src.Model.cotacao import CotacaoResumo, SerieHistorica
from src.Service.provedores.cadeia_mercado import CadeiaMercado
from src.Tool.registrador_log import RegistradorLog


def _alinhar_series_comparacao(
    series_brutas: dict[str, list[dict]],
    ordem: list[str],
) -> tuple[dict[str, list[dict]], list[str]]:
    """
    Alinha todas as acoes nas mesmas datas (intersecao) para o grafico comparativo.
    Recalcula o indice base 100 no primeiro dia comum de cada acao.
    """
    avisos: list[str] = []
    if len(series_brutas) < 2:
        return {}, avisos

    mapas = {simbolo: {p["data_iso"]: p for p in pontos} for simbolo, pontos in series_brutas.items()}
    isos_comuns: set[str] | None = None
    for simbolo in ordem:
        if simbolo not in mapas:
            continue
        conjunto = set(mapas[simbolo].keys())
        isos_comuns = conjunto if isos_comuns is None else isos_comuns & conjunto

    if not isos_comuns or len(isos_comuns) < 2:
        avisos.append(
            "As acoes selecionadas nao tem datas em comum suficientes no periodo. "
            "Prefira tickers do mesmo mercado (ex.: VALE3, PETR4 na B3)."
        )
        return {}, avisos

    isos_ordenados = sorted(isos_comuns)
    alinhadas: dict[str, list[dict]] = {}
    for simbolo in ordem:
        if simbolo not in mapas:
            continue
        mapa = mapas[simbolo]
        precos = [float(mapa[iso]["preco"] or 0) for iso in isos_ordenados]
        base = precos[0] if precos[0] else 1.0
        alinhadas[simbolo] = [
            {
                "data": mapa[iso]["data"],
                "data_iso": iso,
                "preco": mapa[iso]["preco"],
                "indice_relativo": round((preco / base) * 100, 2),
            }
            for iso, preco in zip(isos_ordenados, precos)
        ]

    return alinhadas, avisos


class MercadoServico:
    """Regras de negocio para consulta ao mercado (Yahoo -> Brapi -> Yahoo Chart)."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._cadeia = CadeiaMercado()

    def listar_acoes_padrao(self) -> list[str]:
        return self.listar_acoes_monitoradas()

    def listar_acoes_monitoradas(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[str]:
        from src.Model.acoes_universo import montar_lista_monitoradas

        return montar_lista_monitoradas(quantidade)

    def buscar_resumos(self, simbolos: list[str]) -> list[CotacaoResumo]:
        """Obtem resumo de varias acoes (em lotes para listas grandes)."""
        if not simbolos:
            return []

        tamanho_lote = 25
        if len(simbolos) <= tamanho_lote:
            return self._cadeia.buscar_resumos(simbolos)

        agregado: list[CotacaoResumo] = []
        for inicio in range(0, len(simbolos), tamanho_lote):
            lote = simbolos[inicio : inicio + tamanho_lote]
            agregado.extend(self._cadeia.buscar_resumos(lote))
        return agregado

    def listar_em_alta(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        em_alta = [r for r in resumos if r.variacao_percentual > 0]
        em_alta.sort(key=lambda item: item.variacao_percentual, reverse=True)
        return em_alta[:quantidade]

    def listar_em_queda(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        em_queda = [r for r in resumos if r.variacao_percentual < 0]
        em_queda.sort(key=lambda item: item.variacao_percentual)
        return em_queda[:quantidade]

    def listar_todas_monitoradas(self, quantidade: int = LIMITE_ACOES_PAINEL) -> list[CotacaoResumo]:
        resumos = self.buscar_resumos(self.listar_acoes_monitoradas(quantidade))
        resumos.sort(key=lambda item: item.simbolo)
        return resumos[:quantidade]

    def buscar_historico(
        self,
        simbolo: str,
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> SerieHistorica | None:
        return self._cadeia.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)

    def comparar_acoes(
        self,
        simbolos: list[str],
        periodo_chave: str = "mes",
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ) -> dict:
        series_brutas: dict[str, list[dict]] = {}
        avisos: list[str] = []

        for simbolo in simbolos:
            serie = self.buscar_historico(simbolo, periodo_chave, data_inicio, data_fim)
            if not serie or not serie.pontos:
                codigo = simbolo.replace(".SA", "")
                avisos.append(f"Sem historico no periodo: {codigo}")
                continue

            series_brutas[simbolo] = [
                {
                    "data": p.data_exibicao,
                    "data_iso": p.data_iso,
                    "preco": p.preco_fechamento,
                }
                for p in serie.pontos
            ]

        alinhadas, avisos_alinhamento = _alinhar_series_comparacao(series_brutas, simbolos)
        avisos.extend(avisos_alinhamento)

        return {
            "simbolos": [s for s in simbolos if s in alinhadas],
            "series": alinhadas,
            "avisos": avisos,
        }
