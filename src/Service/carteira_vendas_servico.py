"""Persistencia local do historico de vendas da carteira."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from src.Model.carteira import TIPOS_ATIVO_CARTEIRA, TipoAtivoCarteira, VendaCarteira
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import validar_data_ptbr

_ARQUIVO_NOME = "carteira_vendas.json"


class CarteiraVendasServico:
    """Grava e le vendas em dados/carteira_vendas.json."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_arquivo = self._pasta_dados / _ARQUIVO_NOME
        self._log = RegistradorLog(raiz)

    def listar(self) -> list[VendaCarteira]:
        dados = self._ler_arquivo()
        return list(dados.get("vendas", []))

    def registrar(self, venda: VendaCarteira) -> None:
        vendas = self.listar()
        vendas.insert(0, venda)
        self._salvar(vendas)

    def obter(self, venda_id: str) -> VendaCarteira | None:
        venda_id = (venda_id or "").strip()
        if not venda_id:
            return None
        return next((venda for venda in self.listar() if venda.id == venda_id), None)

    def atualizar(self, venda: VendaCarteira) -> tuple[bool, str | None]:
        vendas = self.listar()
        indice = next((i for i, item in enumerate(vendas) if item.id == venda.id), -1)
        if indice < 0:
            return False, "Venda nao encontrada."
        vendas[indice] = venda
        self._salvar(vendas)
        return True, None

    def remover(self, venda_id: str) -> tuple[bool, str | None]:
        venda_id = (venda_id or "").strip()
        if not venda_id:
            return False, "Venda invalida."
        vendas = self.listar()
        filtradas = [venda for venda in vendas if venda.id != venda_id]
        if len(filtradas) == len(vendas):
            return False, "Venda nao encontrada."
        self._salvar(filtradas)
        return True, None

    def criar_venda(
        self,
        *,
        posicao_id: str,
        simbolo: str,
        tipo_ativo: TipoAtivoCarteira,
        quantidade: float,
        preco_compra: float,
        preco_venda: float,
        data_compra: str,
        data_venda: str,
        dividendos_recebidos: float = 0.0,
    ) -> VendaCarteira:
        return VendaCarteira(
            id=uuid.uuid4().hex[:12],
            posicao_id=posicao_id,
            simbolo=simbolo,
            tipo_ativo=tipo_ativo,
            quantidade=round(quantidade, 8),
            preco_compra=round(preco_compra, 4),
            preco_venda=round(preco_venda, 4),
            data_compra=data_compra.strip(),
            data_venda=data_venda.strip(),
            dividendos_recebidos=round(dividendos_recebidos, 4),
        )

    def _ler_arquivo(self) -> dict:
        if not self._caminho_arquivo.exists():
            return {"vendas": []}

        try:
            with open(self._caminho_arquivo, encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
        except (json.JSONDecodeError, OSError) as exc:
            self._log.erro(f"Falha ao ler vendas da carteira: {exc}")
            return {"vendas": []}

        if not isinstance(conteudo, dict):
            return {"vendas": []}

        brutos = conteudo.get("vendas", [])
        if not isinstance(brutos, list):
            return {"vendas": []}

        validos: list[VendaCarteira] = []
        for bruto in brutos:
            venda = self._parse_venda(bruto)
            if venda is not None:
                validos.append(venda)
        return {"vendas": validos}

    def _parse_venda(self, bruto: object) -> VendaCarteira | None:
        if not isinstance(bruto, dict):
            return None

        venda_id = str(bruto.get("id", "")).strip()
        posicao_id = str(bruto.get("posicao_id", "")).strip()
        simbolo = str(bruto.get("simbolo", "")).strip()
        tipo = str(bruto.get("tipo_ativo", "acoes")).strip().lower()
        if not venda_id or not posicao_id or not simbolo or tipo not in TIPOS_ATIVO_CARTEIRA:
            return None

        try:
            quantidade = float(bruto.get("quantidade", 0))
            preco_compra = float(bruto.get("preco_compra", 0))
            preco_venda = float(bruto.get("preco_venda", 0))
            dividendos = float(bruto.get("dividendos_recebidos", 0))
        except (TypeError, ValueError):
            return None

        if quantidade <= 0 or preco_compra <= 0 or preco_venda <= 0:
            return None

        data_compra = str(bruto.get("data_compra", "")).strip()
        data_venda = str(bruto.get("data_venda", "")).strip()
        if validar_data_ptbr(data_compra)[1] or validar_data_ptbr(data_venda)[1]:
            return None

        tipo_ativo: TipoAtivoCarteira = tipo  # type: ignore[assignment]
        return VendaCarteira(
            id=venda_id,
            posicao_id=posicao_id,
            simbolo=simbolo,
            tipo_ativo=tipo_ativo,
            quantidade=round(quantidade, 8),
            preco_compra=round(preco_compra, 4),
            preco_venda=round(preco_venda, 4),
            data_compra=data_compra,
            data_venda=data_venda,
            dividendos_recebidos=round(dividendos, 4),
        )

    def _salvar(self, vendas: list[VendaCarteira]) -> None:
        payload = {
            "vendas": [
                {
                    "id": v.id,
                    "posicao_id": v.posicao_id,
                    "simbolo": v.simbolo,
                    "tipo_ativo": v.tipo_ativo,
                    "quantidade": v.quantidade,
                    "preco_compra": v.preco_compra,
                    "preco_venda": v.preco_venda,
                    "data_compra": v.data_compra,
                    "data_venda": v.data_venda,
                    "dividendos_recebidos": v.dividendos_recebidos,
                }
                for v in vendas
            ]
        }
        try:
            with open(self._caminho_arquivo, "w", encoding="utf-8") as arquivo:
                json.dump(payload, arquivo, ensure_ascii=False, indent=2)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar vendas da carteira: {exc}")
            raise
