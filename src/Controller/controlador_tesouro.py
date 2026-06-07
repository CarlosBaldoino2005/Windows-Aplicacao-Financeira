"""Coordena consultas ao Tesouro Direto para as telas desktop."""
from __future__ import annotations

from src.Model.tesouro_informacoes import (
    IndicadorTesouro,
    InformacoesFamiliaTesouro,
    obter_indicadores_gerais_tesouro,
    obter_informacoes_familia,
)
from src.Model.tesouro_urls import obter_rotulo_botao_site_tesouro, obter_url_site_tesouro
from src.Model.simulacao_tesouro import ResultadoSimulacaoTesouro
from src.Model.titulo_tesouro import DetalhesTituloTesouro, PainelTesouro
from src.Service.tesouro_direto_servico import TesouroDiretoServico
from src.Service.tesouro_simulacao_servico import TesouroSimulacaoServico
from src.Tool.validadores import validar_valor_monetario_ptbr


class ControladorTesouro:
    """Expoe painel, detalhes e textos educativos do Tesouro Direto."""

    def __init__(self) -> None:
        self._servico = TesouroDiretoServico()
        self._simulacao = TesouroSimulacaoServico()

    def obter_painel(self, forcar_atualizacao: bool = False) -> tuple[PainelTesouro | None, str | None]:
        return self._servico.obter_painel(forcar_atualizacao=forcar_atualizacao)

    def obter_detalhes(self, identificador: str) -> tuple[DetalhesTituloTesouro | None, str | None]:
        if not identificador or not str(identificador).strip():
            return None, "Selecione um titulo para ver os detalhes."
        return self._servico.obter_detalhes(str(identificador).strip())

    def obter_informacoes_familia(self, familia: str) -> InformacoesFamiliaTesouro | None:
        return obter_informacoes_familia(familia)

    def obter_indicadores_gerais(self) -> list[IndicadorTesouro]:
        return obter_indicadores_gerais_tesouro()

    def obter_url_site(self, tipo_titulo: str, data_vencimento_texto: str = "") -> str:
        return obter_url_site_tesouro(tipo_titulo, data_vencimento_texto)

    def obter_rotulo_botao_site(self, familia: str, data_vencimento_texto: str = "") -> str:
        return obter_rotulo_botao_site_tesouro(familia, data_vencimento_texto)

    def simular_investimento(
        self,
        identificador: str,
        valor_texto: str,
    ) -> tuple[ResultadoSimulacaoTesouro | None, str | None]:
        valor, erro_valor = validar_valor_monetario_ptbr(valor_texto)
        if erro_valor:
            return None, erro_valor

        detalhes, erro = self.obter_detalhes(identificador)
        if erro or detalhes is None:
            return None, erro or "Titulo nao encontrado."

        return self._simulacao.simular(detalhes.titulo, valor)
