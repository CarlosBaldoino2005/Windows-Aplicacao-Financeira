"""Persistencia local da carteira de investimentos."""
from __future__ import annotations

import json
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Literal

from src.Model.carteira import (
    MAXIMO_POSICOES_CARTEIRA,
    TIPOS_ATIVO_CARTEIRA,
    PosicaoCarteira,
    TipoAtivoCarteira,
    VendaCarteira,
    tipo_carteira_para_monitoramento,
)
from src.Model.monitoramento import TipoAtivoMonitoramento
from src.Service.carteira_vendas_servico import CarteiraVendasServico
from src.Service.monitoramento_servico import MonitoramentoServico
from src.Tool.config_painel import ConfigPainelIni
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import (
    normalizar_simbolo,
    normalizar_simbolo_cripto,
    validar_data_ptbr,
    validar_quantidade_posicao,
    validar_quantidade_venda_por_tipo,
    validar_valor_monetario_opcional,
    validar_valor_monetario_ptbr,
)

ModoValorVenda = Literal["por_cota", "valor_total"]

_ARQUIVO_NOME = "carteira.json"


class CarteiraServico:
    """Grava e le posicoes em dados/carteira.json."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_arquivo = self._pasta_dados / _ARQUIVO_NOME
        self._log = RegistradorLog(raiz)
        self._monitoramento = MonitoramentoServico(pasta_base)
        self._vendas = CarteiraVendasServico(pasta_base)
        self._config = ConfigPainelIni(pasta_base)

    def listar(self) -> list[PosicaoCarteira]:
        dados = self._ler_arquivo()
        return list(dados.get("posicoes", []))

    def obter(self, posicao_id: str) -> PosicaoCarteira | None:
        for posicao in self.listar():
            if posicao.id == posicao_id:
                return posicao
        return None

    def adicionar(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
        quantidade: float,
        preco_compra: float,
        data_compra: str,
    ) -> tuple[PosicaoCarteira | None, str | None]:
        simbolo_ok, erro = self._normalizar_por_tipo(simbolo, tipo_ativo)
        if erro:
            return None, erro

        _, erro_data = validar_data_ptbr(data_compra)
        if erro_data:
            return None, erro_data

        if quantidade <= 0 or preco_compra <= 0:
            return None, "Quantidade e preco de compra devem ser maiores que zero."

        posicoes = self.listar()
        if len(posicoes) >= MAXIMO_POSICOES_CARTEIRA:
            return None, f"Maximo de {MAXIMO_POSICOES_CARTEIRA} posicoes na carteira."

        nova = PosicaoCarteira(
            id=uuid.uuid4().hex[:12],
            simbolo=simbolo_ok,
            tipo_ativo=tipo_ativo,
            quantidade=round(quantidade, 8),
            preco_compra=round(preco_compra, 4),
            data_compra=data_compra.strip(),
        )
        posicoes.insert(0, nova)
        self._salvar(posicoes)
        self._sincronizar_monitoramento_posicao(nova, posicoes)
        return nova, None

    def atualizar(
        self,
        posicao_id: str,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
        quantidade: float,
        preco_compra: float,
        data_compra: str,
    ) -> tuple[PosicaoCarteira | None, str | None]:
        simbolo_ok, erro = self._normalizar_por_tipo(simbolo, tipo_ativo)
        if erro:
            return None, erro

        _, erro_data = validar_data_ptbr(data_compra)
        if erro_data:
            return None, erro_data

        if quantidade <= 0 or preco_compra <= 0:
            return None, "Quantidade e preco de compra devem ser maiores que zero."

        posicoes = self.listar()
        atualizada: PosicaoCarteira | None = None
        novas: list[PosicaoCarteira] = []

        for posicao in posicoes:
            if posicao.id != posicao_id:
                novas.append(posicao)
                continue
            atualizada = PosicaoCarteira(
                id=posicao.id,
                simbolo=simbolo_ok,
                tipo_ativo=tipo_ativo,
                quantidade=round(quantidade, 8),
                preco_compra=round(preco_compra, 4),
                data_compra=data_compra.strip(),
            )
            novas.append(atualizada)

        if atualizada is None:
            return None, "Posicao nao encontrada na carteira."

        self._salvar(novas)
        self._sincronizar_monitoramento_posicao(atualizada, novas)
        return atualizada, None

    def registrar_venda(
        self,
        posicao_id: str,
        quantidade_vendida: float,
        preco_venda: float,
        data_venda: str,
        dividendos_recebidos: float = 0.0,
    ) -> tuple[bool, str | None]:
        if quantidade_vendida <= 0:
            return False, "Quantidade de venda invalida."

        if preco_venda <= 0:
            return False, "Preco de venda deve ser maior que zero."

        _, erro_data = validar_data_ptbr(data_venda)
        if erro_data:
            return False, erro_data

        posicoes = self.listar()
        indice = next((i for i, p in enumerate(posicoes) if p.id == posicao_id), -1)
        if indice < 0:
            return False, "Posicao nao encontrada."

        atual = posicoes[indice]
        restante = round(atual.quantidade - quantidade_vendida, 8)
        if restante < 0:
            return False, "Quantidade vendida maior que a posicao."

        removida_tipo = atual.tipo_ativo
        removida_simbolo = atual.simbolo

        venda = self._vendas.criar_venda(
            posicao_id=atual.id,
            simbolo=atual.simbolo,
            tipo_ativo=atual.tipo_ativo,
            quantidade=quantidade_vendida,
            preco_compra=atual.preco_compra,
            preco_venda=preco_venda,
            data_compra=atual.data_compra,
            data_venda=data_venda.strip(),
            dividendos_recebidos=dividendos_recebidos,
        )
        self._vendas.registrar(venda)

        if restante == 0:
            posicoes.pop(indice)
        else:
            posicoes[indice] = replace(atual, quantidade=restante)

        self._salvar(posicoes)
        self._atualizar_monitoramento_grupo(removida_tipo, removida_simbolo, posicoes)
        return True, None

    def listar_vendas(self) -> list[VendaCarteira]:
        return self._vendas.listar()

    def obter_venda(self, venda_id: str) -> VendaCarteira | None:
        return self._vendas.obter(venda_id)

    def atualizar_venda(
        self,
        venda_id: str,
        quantidade: float,
        preco_compra: float,
        data_compra: str,
        preco_venda: float,
        data_venda: str,
        dividendos_recebidos: float = 0.0,
    ) -> tuple[bool, str | None]:
        venda = self._vendas.obter(venda_id)
        if venda is None:
            return False, "Venda nao encontrada."

        _, erro_data_compra = validar_data_ptbr(data_compra)
        if erro_data_compra:
            return False, erro_data_compra

        _, erro_data = validar_data_ptbr(data_venda)
        if erro_data:
            return False, erro_data

        if quantidade <= 0:
            return False, "Quantidade de venda invalida."

        if preco_compra <= 0:
            return False, "Preco de compra deve ser maior que zero."

        if preco_venda <= 0:
            return False, "Preco de venda deve ser maior que zero."

        if dividendos_recebidos < 0:
            return False, "Dividendos nao podem ser negativos."

        atualizada = replace(
            venda,
            quantidade=round(quantidade, 8),
            preco_compra=round(preco_compra, 4),
            data_compra=data_compra.strip(),
            preco_venda=round(preco_venda, 4),
            data_venda=data_venda.strip(),
            dividendos_recebidos=round(dividendos_recebidos, 4),
        )
        return self._vendas.atualizar(atualizada)

    def remover_venda(self, venda_id: str) -> tuple[bool, str | None]:
        venda = self._vendas.obter(venda_id)
        if venda is None:
            return False, "Venda nao encontrada."

        ok, erro = self._vendas.remover(venda_id)
        if not ok:
            return ok, erro

        posicoes = self.listar()
        existente = next((posicao for posicao in posicoes if posicao.id == venda.posicao_id), None)
        if existente is not None:
            posicoes = [
                replace(
                    existente,
                    quantidade=round(existente.quantidade + venda.quantidade, 8),
                )
                if posicao.id == venda.posicao_id
                else posicao
                for posicao in posicoes
            ]
        else:
            posicoes.append(
                PosicaoCarteira(
                    id=venda.posicao_id,
                    simbolo=venda.simbolo,
                    tipo_ativo=venda.tipo_ativo,
                    quantidade=venda.quantidade,
                    preco_compra=venda.preco_compra,
                    data_compra=venda.data_compra,
                )
            )

        self._salvar(posicoes)
        self._atualizar_monitoramento_grupo(venda.tipo_ativo, venda.simbolo, posicoes)
        return True, None

    def remover(self, posicao_id: str) -> tuple[bool, str | None]:
        posicoes = self.listar()
        removida = next((p for p in posicoes if p.id == posicao_id), None)
        filtradas = [p for p in posicoes if p.id != posicao_id]
        if removida is None:
            return False, "Posicao nao encontrada."

        self._salvar(filtradas)
        self._atualizar_monitoramento_grupo(removida.tipo_ativo, removida.simbolo, filtradas)
        return True, None

    def resincronizar_monitoramento_todas(self) -> None:
        posicoes = self.listar()
        vistos: set[tuple[TipoAtivoCarteira, str]] = set()
        for posicao in posicoes:
            chave = (posicao.tipo_ativo, posicao.simbolo)
            if chave in vistos:
                continue
            vistos.add(chave)
            self._atualizar_monitoramento_grupo(posicao.tipo_ativo, posicao.simbolo, posicoes)

    @staticmethod
    def parse_quantidade(texto: str) -> tuple[float | None, str | None]:
        return validar_quantidade_posicao(texto)

    @staticmethod
    def parse_quantidade_venda(
        texto: str,
        tipo_ativo: TipoAtivoCarteira,
    ) -> tuple[float | None, str | None]:
        return validar_quantidade_venda_por_tipo(texto, tipo_ativo)

    @staticmethod
    def parse_preco(texto: str) -> tuple[float | None, str | None]:
        return validar_valor_monetario_ptbr(texto)

    @staticmethod
    def resolver_preco_venda(
        texto: str,
        quantidade: float,
        modo: ModoValorVenda = "por_cota",
    ) -> tuple[float | None, str | None]:
        valor, erro = validar_valor_monetario_ptbr(texto)
        if erro:
            return None, erro
        if valor is None or valor <= 0:
            return None, "Informe um valor de venda maior que zero."

        if modo == "valor_total":
            if quantidade <= 0:
                return None, "Informe a quantidade antes do valor total."
            preco = round(valor / quantidade, 4)
            if preco <= 0:
                return None, "Valor total invalido para a quantidade informada."
            return preco, None

        return valor, None

    @staticmethod
    def parse_preco_opcional(texto: str) -> tuple[float | None, str | None]:
        return validar_valor_monetario_opcional(texto)

    def _sincronizar_monitoramento_posicao(
        self,
        posicao: PosicaoCarteira,
        posicoes: list[PosicaoCarteira],
    ) -> None:
        self._atualizar_monitoramento_grupo(posicao.tipo_ativo, posicao.simbolo, posicoes)

    def _atualizar_monitoramento_grupo(
        self,
        tipo: TipoAtivoCarteira,
        simbolo: str,
        posicoes: list[PosicaoCarteira],
    ) -> None:
        grupo = [
            p for p in posicoes if p.tipo_ativo == tipo and p.simbolo == simbolo
        ]
        tipo_mon: TipoAtivoMonitoramento = tipo_carteira_para_monitoramento(tipo)  # type: ignore[assignment]

        if not grupo:
            self._monitoramento.remover_por_simbolo(simbolo, tipo_mon)
            return

        qtd_total = sum(p.quantidade for p in grupo)
        investido = sum(p.quantidade * p.preco_compra for p in grupo)
        preco_medio = investido / qtd_total if qtd_total > 0 else grupo[0].preco_compra
        variacao = self._config.carregar_carteira_variacao_monitoramento_pct()
        self._monitoramento.sincronizar_limites_carteira(
            simbolo,
            tipo_mon,
            preco_medio,
            variacao,
        )

    def _normalizar_por_tipo(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
    ) -> tuple[str | None, str | None]:
        if tipo_ativo == "cripto":
            return normalizar_simbolo_cripto(simbolo)
        return normalizar_simbolo(simbolo)

    def _ler_arquivo(self) -> dict:
        if not self._caminho_arquivo.exists():
            return {"posicoes": []}

        try:
            with open(self._caminho_arquivo, encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
        except (json.JSONDecodeError, OSError) as exc:
            self._log.erro(f"Falha ao ler carteira: {exc}")
            return {"posicoes": []}

        if not isinstance(conteudo, dict):
            return {"posicoes": []}

        brutos = conteudo.get("posicoes", [])
        if not isinstance(brutos, list):
            return {"posicoes": []}

        validos: list[PosicaoCarteira] = []
        for bruto in brutos:
            posicao = self._parse_posicao(bruto)
            if posicao is not None:
                validos.append(posicao)
        return {"posicoes": validos}

    def _parse_posicao(self, bruto: object) -> PosicaoCarteira | None:
        if not isinstance(bruto, dict):
            return None

        posicao_id = str(bruto.get("id", "")).strip()
        simbolo = str(bruto.get("simbolo", "")).strip()
        tipo = str(bruto.get("tipo_ativo", "acoes")).strip().lower()
        if not posicao_id or not simbolo or tipo not in TIPOS_ATIVO_CARTEIRA:
            return None

        try:
            quantidade = float(bruto.get("quantidade", 0))
            preco = float(bruto.get("preco_compra", 0))
        except (TypeError, ValueError):
            return None

        if quantidade <= 0 or preco <= 0:
            return None

        data_compra = str(bruto.get("data_compra", "")).strip()
        _, erro_data = validar_data_ptbr(data_compra)
        if erro_data:
            return None

        tipo_ativo: TipoAtivoCarteira = tipo  # type: ignore[assignment]
        simbolo_ok, erro = self._normalizar_por_tipo(simbolo, tipo_ativo)
        if erro or not simbolo_ok:
            return None

        return PosicaoCarteira(
            id=posicao_id,
            simbolo=simbolo_ok,
            tipo_ativo=tipo_ativo,
            quantidade=round(quantidade, 8),
            preco_compra=round(preco, 4),
            data_compra=data_compra,
        )

    def _salvar(self, posicoes: list[PosicaoCarteira]) -> None:
        payload = {
            "posicoes": [
                {
                    "id": p.id,
                    "simbolo": p.simbolo,
                    "tipo_ativo": p.tipo_ativo,
                    "quantidade": p.quantidade,
                    "preco_compra": p.preco_compra,
                    "data_compra": p.data_compra,
                }
                for p in posicoes
            ]
        }
        try:
            with open(self._caminho_arquivo, "w", encoding="utf-8") as arquivo:
                json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar carteira: {exc}")
            raise
