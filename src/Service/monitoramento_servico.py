"""Persistencia local dos alertas de monitoramento de precos."""
from __future__ import annotations

import json
import uuid
from dataclasses import replace
from pathlib import Path

from src.Model.monitoramento import (
    MAXIMO_ITENS_MONITORAMENTO,
    MonitoramentoItem,
    TIPOS_ATIVO_MONITORAMENTO,
    TipoAtivoMonitoramento,
)
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import (
    normalizar_simbolo,
    normalizar_simbolo_cripto,
    validar_limites_monitoramento,
)

_ARQUIVO_NOME = "monitoramento.json"


class MonitoramentoServico:
    """Grava e le itens de monitoramento em dados/monitoramento.json."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_arquivo = self._pasta_dados / _ARQUIVO_NOME
        self._log = RegistradorLog(raiz)

    def listar(self) -> list[MonitoramentoItem]:
        dados = self._ler_arquivo()
        return list(dados.get("itens", []))

    def normalizar_simbolo(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
    ) -> tuple[str | None, str | None]:
        return self._normalizar_por_tipo(simbolo, tipo_ativo)

    def adicionar(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
        valor_baixo: float | None,
        valor_alto: float | None,
    ) -> tuple[MonitoramentoItem | None, str | None]:
        simbolo_ok, erro = self._normalizar_por_tipo(simbolo, tipo_ativo)
        if erro:
            return None, erro

        erro_limites = validar_limites_monitoramento(valor_baixo, valor_alto)
        if erro_limites:
            return None, erro_limites

        itens = self.listar()
        for existente in itens:
            if existente.simbolo == simbolo_ok and existente.tipo_ativo == tipo_ativo:
                return None, "Este ativo ja esta em monitoramento."

        if len(itens) >= MAXIMO_ITENS_MONITORAMENTO:
            return None, f"Maximo de {MAXIMO_ITENS_MONITORAMENTO} itens em monitoramento."

        novo = MonitoramentoItem(
            id=uuid.uuid4().hex[:12],
            simbolo=simbolo_ok,
            tipo_ativo=tipo_ativo,
            valor_baixo=valor_baixo,
            valor_alto=valor_alto,
            pausado=False,
        )
        itens.append(novo)
        self._salvar(itens)
        return novo, None

    def obter(self, item_id: str) -> MonitoramentoItem | None:
        if not item_id or not str(item_id).strip():
            return None
        for item in self.listar():
            if item.id == item_id:
                return item
        return None

    def atualizar_limites(
        self,
        item_id: str,
        valor_baixo: float | None,
        valor_alto: float | None,
    ) -> tuple[MonitoramentoItem | None, str | None]:
        erro_limites = validar_limites_monitoramento(valor_baixo, valor_alto)
        if erro_limites:
            return None, erro_limites

        itens = self.listar()
        atualizados: list[MonitoramentoItem] = []
        encontrado: MonitoramentoItem | None = None
        for item in itens:
            if item.id != item_id:
                atualizados.append(item)
                continue
            encontrado = replace(
                item,
                valor_baixo=valor_baixo,
                valor_alto=valor_alto,
            )
            atualizados.append(encontrado)

        if encontrado is None:
            return None, "Item de monitoramento nao encontrado."

        self._salvar(atualizados)
        return encontrado, None

    def definir_pausa(
        self,
        item_id: str,
        pausado: bool,
    ) -> tuple[MonitoramentoItem | None, str | None]:
        itens = self.listar()
        atualizados: list[MonitoramentoItem] = []
        encontrado: MonitoramentoItem | None = None
        for item in itens:
            if item.id != item_id:
                atualizados.append(item)
                continue
            encontrado = replace(item, pausado=pausado)
            atualizados.append(encontrado)

        if encontrado is None:
            return None, "Item de monitoramento nao encontrado."

        self._salvar(atualizados)
        return encontrado, None

    def definir_pausa_varios(
        self,
        ids: list[str],
        pausado: bool,
    ) -> tuple[int, str | None]:
        if not ids:
            return 0, "Selecione ao menos um item."

        conjunto = {item_id for item_id in ids if item_id}
        itens = self.listar()
        alterados = 0
        atualizados: list[MonitoramentoItem] = []
        for item in itens:
            if item.id in conjunto:
                atualizados.append(replace(item, pausado=pausado))
                alterados += 1
            else:
                atualizados.append(item)

        if alterados == 0:
            return 0, "Nenhum item selecionado foi encontrado."

        self._salvar(atualizados)
        return alterados, None

    def obter_por_simbolo(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
    ) -> MonitoramentoItem | None:
        simbolo_ok, erro = self._normalizar_por_tipo(simbolo, tipo_ativo)
        if erro or not simbolo_ok:
            return None
        for item in self.listar():
            if item.simbolo == simbolo_ok and item.tipo_ativo == tipo_ativo:
                return item
        return None

    def sincronizar_limites_carteira(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
        preco_referencia: float,
        variacao_pct: float,
    ) -> tuple[MonitoramentoItem | None, str | None]:
        """Cria ou atualiza limites com base no preco de compra ± percentual."""
        if preco_referencia <= 0:
            return None, "Preco de referencia invalido."

        fator = variacao_pct / 100.0
        valor_baixo = round(preco_referencia * (1.0 - fator), 4)
        valor_alto = round(preco_referencia * (1.0 + fator), 4)

        existente = self.obter_por_simbolo(simbolo, tipo_ativo)
        if existente is not None:
            return self.atualizar_limites(existente.id, valor_baixo, valor_alto)

        return self.adicionar(simbolo, tipo_ativo, valor_baixo, valor_alto)

    def remover_por_simbolo(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
    ) -> tuple[bool, str | None]:
        item = self.obter_por_simbolo(simbolo, tipo_ativo)
        if item is None:
            return True, None
        return self.remover(item.id)

    def remover(self, item_id: str) -> tuple[bool, str | None]:
        if not item_id or not str(item_id).strip():
            return False, "Selecione um item para remover."

        itens = self.listar()
        filtrados = [item for item in itens if item.id != item_id]
        if len(filtrados) == len(itens):
            return False, "Item de monitoramento nao encontrado."

        self._salvar(filtrados)
        return True, None

    def remover_varios(self, ids: list[str]) -> tuple[int, str | None]:
        if not ids:
            return 0, "Selecione ao menos um item para remover."

        conjunto = {item_id for item_id in ids if item_id}
        itens = self.listar()
        filtrados = [item for item in itens if item.id not in conjunto]
        removidos = len(itens) - len(filtrados)
        if removidos == 0:
            return 0, "Nenhum item selecionado foi encontrado."

        self._salvar(filtrados)
        return removidos, None

    def _normalizar_por_tipo(
        self,
        simbolo: str,
        tipo_ativo: TipoAtivoMonitoramento,
    ) -> tuple[str | None, str | None]:
        if tipo_ativo == "cripto":
            return normalizar_simbolo_cripto(simbolo)
        return normalizar_simbolo(simbolo)

    def _ler_arquivo(self) -> dict:
        if not self._caminho_arquivo.exists():
            return {"itens": []}

        try:
            with open(self._caminho_arquivo, encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
        except (json.JSONDecodeError, OSError) as exc:
            self._log.erro(f"Falha ao ler monitoramento: {exc}")
            return {"itens": []}

        if not isinstance(conteudo, dict):
            return {"itens": []}

        brutos = conteudo.get("itens", [])
        if not isinstance(brutos, list):
            return {"itens": []}

        validos: list[MonitoramentoItem] = []
        for bruto in brutos:
            item = self._parse_item(bruto)
            if item is not None:
                validos.append(item)
        return {"itens": validos}

    def _parse_item(self, bruto: object) -> MonitoramentoItem | None:
        if not isinstance(bruto, dict):
            return None

        item_id = str(bruto.get("id", "")).strip()
        simbolo = str(bruto.get("simbolo", "")).strip()
        tipo = str(bruto.get("tipo_ativo", "acoes")).strip().lower()
        if not item_id or not simbolo or tipo not in TIPOS_ATIVO_MONITORAMENTO:
            return None

        valor_baixo = self._parse_valor_opcional(bruto.get("valor_baixo"))
        valor_alto = self._parse_valor_opcional(bruto.get("valor_alto"))
        if validar_limites_monitoramento(valor_baixo, valor_alto):
            return None

        pausado = self._parse_pausado(bruto.get("pausado"))

        tipo_ativo: TipoAtivoMonitoramento = tipo  # type: ignore[assignment]
        simbolo_ok, erro = self._normalizar_por_tipo(simbolo, tipo_ativo)
        if erro or not simbolo_ok:
            return None

        return MonitoramentoItem(
            id=item_id,
            simbolo=simbolo_ok,
            tipo_ativo=tipo_ativo,
            valor_baixo=valor_baixo,
            valor_alto=valor_alto,
            pausado=pausado,
        )

    @staticmethod
    def _parse_pausado(valor: object) -> bool:
        if valor is None:
            return False
        if isinstance(valor, bool):
            return valor
        texto = str(valor).strip().lower()
        return texto in ("sim", "true", "1", "yes")

    @staticmethod
    def _parse_valor_opcional(valor: object) -> float | None:
        if valor is None or valor == "":
            return None
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return None
        if numero <= 0:
            return None
        return round(numero, 4)

    def _salvar(self, itens: list[MonitoramentoItem]) -> None:
        payload = {
            "itens": [
                {
                    "id": item.id,
                    "simbolo": item.simbolo,
                    "tipo_ativo": item.tipo_ativo,
                    "valor_baixo": item.valor_baixo,
                    "valor_alto": item.valor_alto,
                    "pausado": item.pausado,
                }
                for item in itens
            ]
        }
        try:
            with open(self._caminho_arquivo, "w", encoding="utf-8") as arquivo:
                json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar monitoramento: {exc}")
            raise
