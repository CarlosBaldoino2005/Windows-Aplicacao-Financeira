"""Persistencia local do historico de compras da carteira."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from src.Model.carteira import (
    TIPOS_ATIVO_CARTEIRA,
    CompraCarteira,
    PosicaoCarteira,
    TipoAtivoCarteira,
)
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import validar_data_ptbr

_ARQUIVO_NOME = "carteira_compras.json"


class CarteiraComprasServico:
    """Grava e le compras em dados/carteira_compras.json."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_arquivo = self._pasta_dados / _ARQUIVO_NOME
        self._log = RegistradorLog(raiz)

    def listar(self) -> list[CompraCarteira]:
        dados = self._ler_arquivo()
        return list(dados.get("compras", []))

    def registrar(self, compra: CompraCarteira) -> None:
        compras = self.listar()
        compras.insert(0, compra)
        self._salvar(compras)

    def obter(self, compra_id: str) -> CompraCarteira | None:
        compra_id = (compra_id or "").strip()
        if not compra_id:
            return None
        return next((compra for compra in self.listar() if compra.id == compra_id), None)

    def obter_por_posicao(self, posicao_id: str) -> CompraCarteira | None:
        posicao_id = (posicao_id or "").strip()
        if not posicao_id:
            return None
        return next(
            (compra for compra in self.listar() if compra.posicao_id == posicao_id),
            None,
        )

    def atualizar(self, compra: CompraCarteira) -> tuple[bool, str | None]:
        compras = self.listar()
        indice = next((i for i, item in enumerate(compras) if item.id == compra.id), -1)
        if indice < 0:
            return False, "Compra nao encontrada."
        compras[indice] = compra
        self._salvar(compras)
        return True, None

    def remover(self, compra_id: str) -> tuple[bool, str | None]:
        compra_id = (compra_id or "").strip()
        if not compra_id:
            return False, "Compra invalida."
        compras = self.listar()
        filtradas = [compra for compra in compras if compra.id != compra_id]
        if len(filtradas) == len(compras):
            return False, "Compra nao encontrada."
        self._salvar(filtradas)
        return True, None

    def remover_por_posicao(self, posicao_id: str) -> None:
        posicao_id = (posicao_id or "").strip()
        if not posicao_id:
            return
        compras = [compra for compra in self.listar() if compra.posicao_id != posicao_id]
        self._salvar(compras)

    def criar_compra_de_posicao(self, posicao: PosicaoCarteira) -> CompraCarteira:
        return CompraCarteira(
            id=uuid.uuid4().hex[:12],
            posicao_id=posicao.id,
            simbolo=posicao.simbolo,
            tipo_ativo=posicao.tipo_ativo,
            quantidade=posicao.quantidade,
            preco_compra=posicao.preco_compra,
            data_compra=posicao.data_compra,
        )

    def _ler_arquivo(self) -> dict:
        if not self._caminho_arquivo.exists():
            return {"compras": []}

        try:
            with open(self._caminho_arquivo, encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
        except (json.JSONDecodeError, OSError) as exc:
            self._log.erro(f"Falha ao ler compras da carteira: {exc}")
            return {"compras": []}

        if not isinstance(conteudo, dict):
            return {"compras": []}

        brutos = conteudo.get("compras", [])
        if not isinstance(brutos, list):
            return {"compras": []}

        validos: list[CompraCarteira] = []
        for bruto in brutos:
            compra = self._parse_compra(bruto)
            if compra is not None:
                validos.append(compra)
        return {"compras": validos}

    def _parse_compra(self, bruto: object) -> CompraCarteira | None:
        if not isinstance(bruto, dict):
            return None

        compra_id = str(bruto.get("id", "")).strip()
        posicao_id = str(bruto.get("posicao_id", "")).strip()
        simbolo = str(bruto.get("simbolo", "")).strip()
        tipo = str(bruto.get("tipo_ativo", "acoes")).strip().lower()
        if not compra_id or not posicao_id or not simbolo or tipo not in TIPOS_ATIVO_CARTEIRA:
            return None

        try:
            quantidade = float(bruto.get("quantidade", 0))
            preco_compra = float(bruto.get("preco_compra", 0))
        except (TypeError, ValueError):
            return None

        if quantidade <= 0 or preco_compra <= 0:
            return None

        data_compra = str(bruto.get("data_compra", "")).strip()
        if validar_data_ptbr(data_compra)[1]:
            return None

        tipo_ativo: TipoAtivoCarteira = tipo  # type: ignore[assignment]
        return CompraCarteira(
            id=compra_id,
            posicao_id=posicao_id,
            simbolo=simbolo,
            tipo_ativo=tipo_ativo,
            quantidade=round(quantidade, 8),
            preco_compra=round(preco_compra, 4),
            data_compra=data_compra,
        )

    def _salvar(self, compras: list[CompraCarteira]) -> None:
        payload = {
            "compras": [
                {
                    "id": c.id,
                    "posicao_id": c.posicao_id,
                    "simbolo": c.simbolo,
                    "tipo_ativo": c.tipo_ativo,
                    "quantidade": c.quantidade,
                    "preco_compra": c.preco_compra,
                    "data_compra": c.data_compra,
                }
                for c in compras
            ]
        }
        try:
            with open(self._caminho_arquivo, "w", encoding="utf-8") as arquivo:
                json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar compras da carteira: {exc}")
            raise
