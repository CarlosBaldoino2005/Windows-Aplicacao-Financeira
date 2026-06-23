"""Coordena carteira de investimentos entre interface e servicos."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Model.carteira import (
    CompraCarteira,
    LinhaCarteira,
    LinhaCompraCarteira,
    LinhaVendaCarteira,
    PosicaoCarteira,
    ResultadoBuscaCarteira,
    TipoAtivoCarteira,
    VendaCarteira,
    tipo_carteira_para_monitoramento,
)
from src.Model.resultado_busca import ResultadoBusca
from src.Model.opcoes_atualizacao_automatica import OpcoesAtualizacaoAutomatica
from src.Model.opcoes_relatorio_automatico_carteira import OpcoesRelatorioAutomaticoCarteira
from src.Model.cotacao import CotacaoResumo
from src.Model.monitoramento import TipoAtivoMonitoramento
from src.Service.carteira_servico import CarteiraServico
from src.Service.detalhes_acao_servico import DetalhesAcaoServico
from src.Service.mercado_cripto_servico import MercadoCriptoServico
from src.Service.mercado_etfs_servico import MercadoEtfsServico
from src.Service.mercado_fiis_servico import MercadoFiisServico
from src.Service.mercado_servico import MercadoServico, _alinhar_series_comparacao
from src.Service.relatorio_carteira_servico import RelatorioCarteiraServico
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.validadores import validar_data_ptbr
from src.Tool.carteira_dividendos_helper import (
    calcular_dividendos_recebidos,
    estimar_dividendo_proximo_mes,
    estimar_proximo_dividendo,
)
from src.Tool.dividendos_helper import extrair_pagamentos_dividendos
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
        self._mercado_etfs = MercadoEtfsServico()
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
        preco_venda_texto: str,
        data_venda_texto: str | None = None,
        *,
        modo_valor_venda: str = "por_cota",
    ) -> tuple[bool, str | None]:
        posicao = self._persistencia.obter(posicao_id)
        if posicao is None:
            return False, "Posicao nao encontrada."

        quantidade, erro = self._persistencia.parse_quantidade_venda(
            quantidade_texto,
            posicao.tipo_ativo,
        )
        if erro:
            return False, erro
        preco_venda, erro_preco = self._persistencia.resolver_preco_venda(
            preco_venda_texto,
            quantidade or 0,
            "valor_total" if modo_valor_venda == "valor_total" else "por_cota",
        )
        if erro_preco:
            return False, erro_preco

        data_venda = (data_venda_texto or "").strip()
        if not data_venda:
            from datetime import datetime

            data_venda = datetime.now().strftime("%d/%m/%Y")
        _, erro_data = validar_data_ptbr(data_venda)
        if erro_data:
            return False, erro_data

        dividendos = 0.0
        if self._tipo_ativo_pode_ter_dividendos(posicao.tipo_ativo):
            pagamentos = extrair_pagamentos_dividendos(posicao.simbolo)
            if pagamentos:
                dividendos = calcular_dividendos_recebidos(
                    pagamentos,
                    posicao.data_compra,
                    quantidade or 0,
                    data_fim_texto=data_venda,
                )

        return self._persistencia.registrar_venda(
            posicao_id,
            quantidade or 0,
            preco_venda or 0,
            data_venda,
            dividendos,
        )

    def obter_linhas_vendas_carteira(self) -> tuple[list[LinhaVendaCarteira], str | None]:
        vendas = self._persistencia.listar_vendas()
        if not vendas:
            return [], None

        linhas: list[LinhaVendaCarteira] = []
        for venda in vendas:
            nome = codigo_exibicao(venda.simbolo)
            moeda = self._moeda_por_venda(venda)
            if venda.tipo_ativo != "indices":
                detalhes, _ = self._detalhes.obter_detalhes(venda.simbolo)
                if detalhes is not None and detalhes.nome_empresa:
                    nome = detalhes.nome_empresa
            linhas.append(LinhaVendaCarteira(venda=venda, nome=nome, moeda=moeda))
        return linhas, None

    def obter_venda(self, venda_id: str) -> VendaCarteira | None:
        return self._persistencia.obter_venda(venda_id)

    def atualizar_venda(
        self,
        venda_id: str,
        quantidade_texto: str,
        preco_compra_texto: str,
        data_compra_texto: str,
        preco_venda_texto: str,
        data_venda_texto: str,
        dividendos_texto: str = "",
        *,
        modo_valor_venda: str = "por_cota",
    ) -> tuple[bool, str | None]:
        venda = self._persistencia.obter_venda(venda_id)
        if venda is None:
            return False, "Venda nao encontrada."

        quantidade, erro_qtd = self._persistencia.parse_quantidade_venda(
            quantidade_texto,
            venda.tipo_ativo,
        )
        if erro_qtd:
            return False, erro_qtd
        preco_compra, erro_compra = self._persistencia.parse_preco(preco_compra_texto)
        if erro_compra:
            return False, erro_compra
        preco_venda, erro_preco = self._persistencia.resolver_preco_venda(
            preco_venda_texto,
            quantidade or 0,
            "valor_total" if modo_valor_venda == "valor_total" else "por_cota",
        )
        if erro_preco:
            return False, erro_preco
        dividendos, erro_div = self._persistencia.parse_preco_opcional(dividendos_texto)
        if erro_div:
            return False, erro_div
        data_compra = (data_compra_texto or "").strip()
        _, erro_data_compra = validar_data_ptbr(data_compra)
        if erro_data_compra:
            return False, erro_data_compra
        data_venda = (data_venda_texto or "").strip()
        _, erro_data = validar_data_ptbr(data_venda)
        if erro_data:
            return False, erro_data
        return self._persistencia.atualizar_venda(
            venda_id,
            quantidade or 0,
            preco_compra or 0,
            data_compra,
            preco_venda or 0,
            data_venda,
            dividendos if dividendos is not None else 0.0,
        )

    def remover_venda(self, venda_id: str) -> tuple[bool, str | None]:
        return self._persistencia.remover_venda(venda_id)

    def obter_linhas_compras_carteira(self) -> tuple[list[LinhaCompraCarteira], str | None]:
        compras = self._persistencia.listar_compras()
        if not compras:
            return [], None

        posicoes_ids = {posicao.id for posicao in self._persistencia.listar()}
        linhas: list[LinhaCompraCarteira] = []
        for compra in compras:
            nome = codigo_exibicao(compra.simbolo)
            moeda = self._moeda_por_ativo_carteira(compra.tipo_ativo, compra.simbolo)
            if compra.tipo_ativo != "indices":
                detalhes, _ = self._detalhes.obter_detalhes(compra.simbolo)
                if detalhes is not None and detalhes.nome_empresa:
                    nome = detalhes.nome_empresa
            linhas.append(
                LinhaCompraCarteira(
                    compra=compra,
                    nome=nome,
                    moeda=moeda,
                    na_carteira=compra.posicao_id in posicoes_ids,
                )
            )
        return linhas, None

    def obter_compra(self, compra_id: str) -> CompraCarteira | None:
        return self._persistencia.obter_compra(compra_id)

    def atualizar_compra(
        self,
        compra_id: str,
        quantidade_texto: str,
        preco_compra_texto: str,
        data_compra_texto: str,
        *,
        modo_valor_compra: str = "por_cota",
    ) -> tuple[bool, str | None]:
        compra = self._persistencia.obter_compra(compra_id)
        if compra is None:
            return False, "Compra nao encontrada."

        quantidade, erro_qtd = self._persistencia.parse_quantidade(quantidade_texto)
        if erro_qtd:
            return False, erro_qtd
        preco_compra, erro_preco = self._persistencia.resolver_preco_venda(
            preco_compra_texto,
            quantidade or 0,
            "valor_total" if modo_valor_compra == "valor_total" else "por_cota",
        )
        if erro_preco:
            return False, erro_preco

        data_compra = (data_compra_texto or "").strip()
        _, erro_data = validar_data_ptbr(data_compra)
        if erro_data:
            return False, erro_data

        return self._persistencia.atualizar_compra(
            compra_id,
            quantidade or 0,
            preco_compra or 0,
            data_compra,
        )

    def remover_compra(self, compra_id: str) -> tuple[bool, str | None]:
        return self._persistencia.remover_compra(compra_id)

    @staticmethod
    def _moeda_por_ativo_carteira(tipo_ativo: TipoAtivoCarteira, simbolo: str) -> str:
        if tipo_ativo == "cripto":
            return "USD"
        if tipo_ativo in ("fiis", "etfs") or simbolo.endswith(".SA"):
            return "BRL"
        return "BRL"

    @staticmethod
    def _moeda_por_venda(venda) -> str:
        return ControladorCarteira._moeda_por_ativo_carteira(venda.tipo_ativo, venda.simbolo)

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

    def carregar_relatorio_automatico(self) -> OpcoesRelatorioAutomaticoCarteira:
        return self._config.carregar_relatorio_automatico_carteira()

    def salvar_relatorio_automatico(
        self,
        habilitado: bool,
        horarios: tuple[str, ...],
        emails_destinatarios: tuple[str, ...],
    ) -> None:
        self._config.salvar_relatorio_automatico_carteira(
            habilitado,
            horarios,
            emails_destinatarios,
        )

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

        for tipo_mon in ("acoes", "etfs", "fiis", "cripto"):
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
            "etfs": [],
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
        for resumo in self._mercado_etfs.buscar_resumos(por_tipo["etfs"]):
            cotacoes[("etfs", resumo.simbolo)] = resumo

        pagamentos_por_simbolo = self._carregar_pagamentos_dividendos(posicoes)

        linhas: list[LinhaCarteira] = []
        for posicao in posicoes:
            cotacao = cotacoes.get((posicao.tipo_ativo, posicao.simbolo))
            dividendos = 0.0
            dividendo_prev_mes = None
            prox_data = ""
            prox_valor_cota = None
            prox_total = None

            pagamentos = pagamentos_por_simbolo.get(posicao.simbolo)
            if pagamentos:
                dividendos = calcular_dividendos_recebidos(
                    pagamentos,
                    posicao.data_compra,
                    posicao.quantidade,
                )
                dividendo_prev_mes = estimar_dividendo_proximo_mes(
                    pagamentos,
                    posicao.quantidade,
                )
                prox_data, prox_valor_cota, prox_total = estimar_proximo_dividendo(
                    pagamentos,
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

    def gerar_relatorio_pdf(self) -> tuple[Path | None, str | None, str | None]:
        """Monta dados da carteira, grava PDF e retorna caminho, erro e assunto do resumo."""
        linhas, erro = self.obter_linhas_carteira()
        if erro:
            return None, erro, None
        if not linhas:
            return None, "Cadastre ao menos uma posicao na carteira para gerar o relatorio.", None

        servico = RelatorioCarteiraServico()
        dados = servico.montar_dados(linhas)
        assunto = servico.formatar_assunto_resumo_carteira(dados.resumo)
        try:
            caminho = servico.gerar_pdf(dados)
        except Exception as exc:
            return None, f"Nao foi possivel gerar o PDF: {exc}", None
        return Path(caminho), None, assunto

    @staticmethod
    def _tipo_ativo_pode_ter_dividendos(tipo: TipoAtivoCarteira) -> bool:
        return tipo not in ("indices", "cripto")

    def _carregar_pagamentos_dividendos(
        self, posicoes: list[PosicaoCarteira]
    ) -> dict[str, list]:
        """Busca historico de dividendos em paralelo (apenas o necessario para a grid)."""
        simbolos = list(
            dict.fromkeys(
                posicao.simbolo
                for posicao in posicoes
                if self._tipo_ativo_pode_ter_dividendos(posicao.tipo_ativo)
            )
        )
        if not simbolos:
            return {}

        saida: dict[str, list] = {}
        workers = min(8, len(simbolos))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futuros = {
                executor.submit(extrair_pagamentos_dividendos, simbolo): simbolo
                for simbolo in simbolos
            }
            for futuro in as_completed(futuros):
                simbolo = futuros[futuro]
                try:
                    saida[simbolo] = futuro.result()
                except Exception:
                    saida[simbolo] = []
        return saida

    def _mercado_por_tipo(self, tipo: TipoAtivoCarteira):
        if tipo == "cripto":
            return self._mercado_cripto
        if tipo == "fiis":
            return self._mercado_fiis
        if tipo == "etfs":
            return self._mercado_etfs
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
