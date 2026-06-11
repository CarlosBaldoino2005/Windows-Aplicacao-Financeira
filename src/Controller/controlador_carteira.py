"""Coordena carteira de investimentos entre interface e servicos."""
from __future__ import annotations

from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Model.carteira import (
    LinhaCarteira,
    PosicaoCarteira,
    ResultadoBuscaCarteira,
    TipoAtivoCarteira,
    tipo_carteira_para_monitoramento,
)
from src.Model.resultado_busca import ResultadoBusca
from src.Model.opcoes_atualizacao_automatica import OpcoesAtualizacaoAutomatica
from src.Model.cotacao import CotacaoResumo
from src.Model.monitoramento import TipoAtivoMonitoramento
from src.Service.carteira_servico import CarteiraServico
from src.Service.detalhes_acao_servico import DetalhesAcaoServico
from src.Service.mercado_cripto_servico import MercadoCriptoServico
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.mercado_servico import MercadoServico, _alinhar_series_comparacao
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.validadores import validar_data_ptbr
from src.Tool.carteira_dividendos_helper import (
    calcular_dividendos_recebidos,
    estimar_dividendo_proximo_mes,
    estimar_proximo_dividendo,
)
from src.Tool.carteira_ativo_helper import (
    buscar_indices_por_termo,
    inferir_tipo_ativo_carteira,
)
from src.Tool.config_painel import ConfigPainelIni


class ControladorCarteira:
    """API usada pela tela de carteira."""

    def __init__(self) -> None:
        self._persistencia = CarteiraServico()
        self._config = ConfigPainelIni()
        self._mercado_acoes = MercadoServico()
        self._mercado_cripto = MercadoCriptoServico()
        self._mercado_fiis = MercadoFiisServico()
        self._detalhes = DetalhesAcaoServico()
        self._monitoramento = ControladorMonitoramento()

    def listar_posicoes(self) -> list[PosicaoCarteira]:
        return self._persistencia.listar()

    def obter_posicao(self, posicao_id: str) -> PosicaoCarteira | None:
        return self._persistencia.obter(posicao_id)

    def adicionar_posicao(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
        quantidade_texto: str,
        preco_texto: str,
        data_compra: str,
    ) -> tuple[PosicaoCarteira | None, str | None]:
        quantidade, erro_qtd = self._persistencia.parse_quantidade(quantidade_texto)
        if erro_qtd:
            return None, erro_qtd
        preco, erro_preco = self._persistencia.parse_preco(preco_texto)
        if erro_preco:
            return None, erro_preco
        return self._persistencia.adicionar(
            simbolo,
            tipo_ativo,
            quantidade or 0,
            preco or 0,
            data_compra,
        )

    def atualizar_posicao(
        self,
        posicao_id: str,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
        quantidade_texto: str,
        preco_texto: str,
        data_compra: str,
    ) -> tuple[PosicaoCarteira | None, str | None]:
        quantidade, erro_qtd = self._persistencia.parse_quantidade(quantidade_texto)
        if erro_qtd:
            return None, erro_qtd
        preco, erro_preco = self._persistencia.parse_preco(preco_texto)
        if erro_preco:
            return None, erro_preco
        return self._persistencia.atualizar(
            posicao_id,
            simbolo,
            tipo_ativo,
            quantidade or 0,
            preco or 0,
            data_compra,
        )

    def registrar_venda(
        self,
        posicao_id: str,
        quantidade_texto: str,
    ) -> tuple[bool, str | None]:
        quantidade, erro = self._persistencia.parse_quantidade(quantidade_texto)
        if erro:
            return False, erro
        return self._persistencia.registrar_venda(posicao_id, quantidade or 0)

    def remover_posicao(self, posicao_id: str) -> tuple[bool, str | None]:
        return self._persistencia.remover(posicao_id)

    def carregar_variacao_monitoramento_pct(self) -> float:
        return self._config.carregar_carteira_variacao_monitoramento_pct()

    def salvar_variacao_monitoramento_pct(self, valor: float) -> None:
        from src.Tool.validadores import validar_percentual_carteira

        pct, erro = validar_percentual_carteira(str(valor))
        if erro or pct is None:
            return
        self._config.salvar_carteira_variacao_monitoramento_pct(pct)
        self._persistencia.resincronizar_monitoramento_todas()

    def carregar_atualizacao_automatica(self) -> OpcoesAtualizacaoAutomatica:
        return self._config.carregar_atualizacao_automatica_carteira()

    def salvar_atualizacao_automatica(self, habilitada: bool, intervalo_segundos: int) -> None:
        self._config.salvar_atualizacao_automatica_carteira(habilitada, intervalo_segundos)

    def pesquisar_ativos(
        self,
        tipo_ativo: TipoAtivoCarteira,
        termo: str,
    ) -> tuple[list, str | None]:
        tipo_mon: TipoAtivoMonitoramento = tipo_carteira_para_monitoramento(tipo_ativo)  # type: ignore[assignment]
        return self._monitoramento.pesquisar_ativos(tipo_mon, termo)

    def pesquisar_ativos_automatico(
        self,
        termo: str,
        *,
        limite: int = 12,
    ) -> tuple[list[ResultadoBuscaCarteira], str | None]:
        """Busca em acoes, FIIs, cripto e indices; infere o tipo de cada resultado."""
        texto = (termo or "").strip()
        if not texto:
            return [], "Digite o codigo ou nome do ativo."

        vistos: set[str] = set()
        saida: list[ResultadoBuscaCarteira] = []

        def incluir(item: ResultadoBusca, tipo_busca: TipoAtivoCarteira) -> None:
            if len(saida) >= limite:
                return
            simbolo = (item.simbolo or "").strip()
            if not simbolo or simbolo in vistos:
                return
            vistos.add(simbolo)
            tipo = inferir_tipo_ativo_carteira(simbolo)
            if tipo_busca == "indices":
                tipo = "indices"
            saida.append(ResultadoBuscaCarteira.de_resultado_busca(item, tipo))

        for item in buscar_indices_por_termo(texto, limite=limite):
            incluir(item, "indices")

        for tipo_mon in ("acoes", "fiis", "cripto"):
            itens, _erro = self._monitoramento.pesquisar_ativos(
                tipo_mon,  # type: ignore[arg-type]
                texto,
            )
            for bruto in itens or []:
                if isinstance(bruto, ResultadoBusca):
                    item = bruto
                else:
                    simbolo = str(getattr(bruto, "simbolo", bruto))
                    item = ResultadoBusca(
                        simbolo=simbolo,
                        nome=str(getattr(bruto, "nome", "")),
                        bolsa=str(getattr(bruto, "bolsa", "")),
                    )
                incluir(item, tipo_mon)  # type: ignore[arg-type]

        if saida:
            return saida, None

        return [], "Nenhum resultado encontrado."

    def obter_linhas_carteira(self) -> tuple[list[LinhaCarteira], str | None]:
        posicoes = self._persistencia.listar()
        if not posicoes:
            return [], None

        por_tipo: dict[TipoAtivoCarteira, list[str]] = {
            "acoes": [],
            "cripto": [],
            "fiis": [],
            "indices": [],
        }
        for posicao in posicoes:
            por_tipo[posicao.tipo_ativo].append(posicao.simbolo)

        cotacoes: dict[tuple[TipoAtivoCarteira, str], CotacaoResumo] = {}
        for resumo in self._mercado_acoes.buscar_resumos(
            por_tipo["acoes"] + por_tipo["indices"]
        ):
            chave_acoes = ("acoes", resumo.simbolo)
            chave_indices = ("indices", resumo.simbolo)
            cotacoes[chave_acoes] = resumo
            cotacoes[chave_indices] = resumo
        for resumo in self._mercado_cripto.buscar_resumos(por_tipo["cripto"]):
            cotacoes[("cripto", resumo.simbolo)] = resumo
        for resumo in self._mercado_fiis.buscar_resumos(por_tipo["fiis"]):
            cotacoes[("fiis", resumo.simbolo)] = resumo

        linhas: list[LinhaCarteira] = []
        for posicao in posicoes:
            cotacao = cotacoes.get((posicao.tipo_ativo, posicao.simbolo))
            dividendos = 0.0
            dividendo_prev_mes = None
            prox_data = ""
            prox_valor_cota = None
            prox_total = None

            if posicao.tipo_ativo != "indices":
                detalhes, _ = self._detalhes.obter_detalhes(posicao.simbolo)
                if detalhes is not None:
                    dividendos = calcular_dividendos_recebidos(
                        detalhes.pagamentos_dividendos,
                        posicao.data_compra,
                        posicao.quantidade,
                    )
                    dividendo_prev_mes = estimar_dividendo_proximo_mes(
                        detalhes.pagamentos_dividendos,
                        posicao.quantidade,
                    )
                    prox_data, prox_valor_cota, prox_total = estimar_proximo_dividendo(
                        detalhes.pagamentos_dividendos,
                        posicao.quantidade,
                    )

            linhas.append(
                LinhaCarteira(
                    posicao=posicao,
                    cotacao=cotacao,
                    dividendos_recebidos=dividendos,
                    dividendo_previsto_proximo_mes=dividendo_prev_mes,
                    proximo_dividendo_data=prox_data,
                    proximo_dividendo_valor_por_cota=prox_valor_cota,
                    proximo_dividendo_previsto=prox_total,
                )
            )

        return linhas, None

    def _mercado_por_tipo(self, tipo: TipoAtivoCarteira):
        if tipo == "cripto":
            return self._mercado_cripto
        if tipo == "fiis":
            return self._mercado_fiis
        return self._mercado_acoes

    def comparar_ativos_carteira(
        self,
        periodo_chave: str = "mes",
        data_inicio_texto: str | None = None,
        data_fim_texto: str | None = None,
    ) -> tuple[dict | None, str | None]:
        """Historico alinhado dos ativos unicos da carteira para grafico comparativo."""
        posicoes = self._persistencia.listar()
        if not posicoes:
            return None, "Cadastre ao menos uma posicao na carteira."

        vistos: set[str] = set()
        ativos: list[tuple[TipoAtivoCarteira, str]] = []
        for posicao in posicoes:
            if posicao.simbolo in vistos:
                continue
            vistos.add(posicao.simbolo)
            ativos.append((posicao.tipo_ativo, posicao.simbolo))

        dt_inicio = None
        dt_fim = None
        if periodo_chave == "personalizado":
            dt_inicio, err_i = validar_data_ptbr(data_inicio_texto or "")
            if err_i:
                return None, err_i
            dt_fim, err_f = validar_data_ptbr(data_fim_texto or "")
            if err_f:
                return None, err_f

        series_brutas: dict[str, list[dict]] = {}
        ordem: list[str] = []
        avisos: list[str] = []

        for tipo, simbolo in ativos:
            serie = self._mercado_por_tipo(tipo).buscar_historico(
                simbolo, periodo_chave, dt_inicio, dt_fim
            )
            if not serie or not serie.pontos:
                avisos.append(f"Sem historico no periodo: {codigo_exibicao(simbolo)}")
                continue

            ordem.append(simbolo)
            series_brutas[simbolo] = [
                {
                    "data": p.data_exibicao,
                    "data_iso": p.data_iso,
                    "preco": p.preco_fechamento,
                }
                for p in serie.pontos
            ]

        if not series_brutas:
            return None, "Nenhum ativo da carteira com historico no periodo selecionado."

        if len(series_brutas) == 1:
            simbolo = ordem[0]
            pontos = series_brutas[simbolo]
            base = float(pontos[0]["preco"] or 1) or 1.0
            alinhadas = {
                simbolo: [
                    {
                        **ponto,
                        "indice_relativo": round((float(ponto["preco"] or 0) / base) * 100, 2),
                    }
                    for ponto in pontos
                ]
            }
        else:
            alinhadas, avisos_alinhamento = _alinhar_series_comparacao(series_brutas, ordem)
            avisos.extend(avisos_alinhamento)
            if not alinhadas:
                mensagem = (
                    avisos[0]
                    if avisos
                    else "Nao foi possivel alinhar os ativos da carteira no periodo."
                )
                return None, mensagem

        return {
            "simbolos": [simbolo for simbolo in ordem if simbolo in alinhadas],
            "series": alinhadas,
            "avisos": avisos,
        }, None
