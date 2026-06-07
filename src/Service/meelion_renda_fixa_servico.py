"""Consulta ofertas LCI/LCA/CDB via API publica Meelion (JSON-RPC)."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import date, datetime

from src.Model.oferta_renda_fixa_bancaria import OfertaRendaFixaBancaria, ResultadoConsultaOfertas
from src.Service.provedores.util_provedor import TIMEOUT_SEGUNDOS, USER_AGENT
from src.Tool.registrador_log import RegistradorLog

URL_MEELION_MCP = "https://mcp.meelion.com/"
LIMITE_PADRAO = 5

DISTRIBUIDORES_DISPONIVEIS = [
    "Banco Inter",
    "XP Investimentos",
    "Itaú",
    "BTG Pactual",
    "Nubank",
    "Bradesco",
    "Caixa",
    "Santander",
    "Banco do Brasil",
    "Rico",
    "Clear",
    "Genial Investimentos",
    "Modal",
]

OPCOES_PRAZO = [
    ("Todos os prazos", ""),
    ("Ate 1 ano", "prazo-ate-1-ano"),
    ("1 a 2 anos", "prazo-1-a-2-anos"),
    ("2 a 3 anos", "prazo-2-a-3-anos"),
    ("3 a 4 anos", "prazo-3-a-4-anos"),
    ("Acima de 4 anos", "prazo-acima-4-anos"),
]


class MeelionRendaFixaServico:
    """Busca rankings de renda fixa bancaria na Meelion."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    def obter_distribuidores(self) -> list[str]:
        return list(DISTRIBUIDORES_DISPONIVEIS)

    def obter_opcoes_prazo(self) -> list[tuple[str, str]]:
        return list(OPCOES_PRAZO)

    def buscar_ofertas(
        self,
        tipos_investimento: str,
        distribuidor: str,
        prazo_slug: str | None = None,
        apenas_emissor_igual_distribuidor: bool = False,
        limite: int = LIMITE_PADRAO,
    ) -> tuple[ResultadoConsultaOfertas | None, str | None]:
        distribuidor_limpo = (distribuidor or "").strip()
        if not distribuidor_limpo:
            return None, "Selecione onde investir (distribuidor/corretora)."

        tipos_limpos = (tipos_investimento or "").strip()
        if not tipos_limpos:
            return None, "Informe o tipo de produto (CDB, LCI ou LCA)."

        argumentos: dict = {
            "investment_types": tipos_limpos,
            "distributors": distribuidor_limpo,
            "limit": max(1, min(limite, 5)),
        }
        if prazo_slug and str(prazo_slug).strip():
            argumentos["prazo"] = str(prazo_slug).strip()

        resposta = self._chamar_meelion("get_best_investments", argumentos)
        if resposta is None:
            return None, "Nao foi possivel consultar ofertas na Meelion. Verifique sua conexao."

        conteudo = self._extrair_structured_content(resposta)
        if conteudo is None:
            return None, "Resposta invalida da Meelion."

        ofertas: list[OfertaRendaFixaBancaria] = []
        for item in conteudo.get("investments") or []:
            if not isinstance(item, dict):
                continue
            oferta = _mapear_oferta(item)
            if oferta is not None:
                ofertas.append(oferta)

        if apenas_emissor_igual_distribuidor:
            ofertas = [
                o for o in ofertas if _nomes_instituicao_compativel(o.emissor, distribuidor_limpo)
            ]

        see_more = conteudo.get("seeMoreOnSite") or {}
        url_comparador = see_more.get("url") if isinstance(see_more, dict) else None
        if not url_comparador:
            url_comparador = "https://www.meelion.com/renda-fixa/comparar-investimentos/"

        mensagem = (
            f"{len(ofertas)} oferta(s) exibida(s) para {distribuidor_limpo}. "
            "Ranking parcial — confirme taxas no app do banco."
        )
        if see_more and isinstance(see_more, dict) and see_more.get("message"):
            mensagem = str(see_more["message"])

        resultado = ResultadoConsultaOfertas(
            ofertas=ofertas,
            total_retornado=len(ofertas),
            mensagem=mensagem,
            url_comparador=url_comparador,
            fonte=(conteudo.get("source") or {}).get("name", "Meelion")
            if isinstance(conteudo.get("source"), dict)
            else "Meelion",
            disclaimer=str(conteudo.get("disclaimer") or ""),
            atualizado_em=str(conteudo.get("updatedAt") or ""),
        )
        return resultado, None

    def _chamar_meelion(self, nome_tool: str, argumentos: dict) -> dict | None:
        corpo = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": nome_tool, "arguments": argumentos},
        }
        dados_bytes = json.dumps(corpo).encode("utf-8")
        requisicao = urllib.request.Request(
            URL_MEELION_MCP,
            data=dados_bytes,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta:
                return json.loads(resposta.read().decode("utf-8"))
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            json.JSONDecodeError,
            TimeoutError,
        ) as exc:
            self._log.aviso(f"Falha Meelion MCP: {exc}")
            return None

    @staticmethod
    def _extrair_structured_content(resposta: dict) -> dict | None:
        if not isinstance(resposta, dict):
            return None
        if "error" in resposta:
            return None
        result = resposta.get("result")
        if not isinstance(result, dict):
            return None
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
        content = result.get("content")
        if isinstance(content, list) and content:
            primeiro = content[0]
            if isinstance(primeiro, dict) and isinstance(primeiro.get("text"), str):
                try:
                    return json.loads(primeiro["text"])
                except json.JSONDecodeError:
                    return None
        return None


def _mapear_oferta(item: dict) -> OfertaRendaFixaBancaria | None:
    try:
        id_oferta = int(item.get("id") or 0)
    except (TypeError, ValueError):
        return None
    if id_oferta <= 0:
        return None

    bruto = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    indexador = str(item.get("financialIndex") or bruto.get("financial_index") or "").strip()
    pct_cdi, taxa_prefix = _extrair_taxas(item, bruto, indexador)
    vencimento_iso = str(item.get("maturityDate") or bruto.get("maturity_date") or "")
    vencimento_texto, dias = _formatar_vencimento(vencimento_iso)

    minimo = item.get("minimumInvestment")
    if minimo is None and bruto.get("minimum_investment") is not None:
        try:
            minimo = float(str(bruto["minimum_investment"]).replace(",", "."))
        except (TypeError, ValueError):
            minimo = None

    taxa_rotulo = _montar_rotulo_taxa(pct_cdi, taxa_prefix, indexador, item, bruto)

    return OfertaRendaFixaBancaria(
        id=id_oferta,
        nome=str(item.get("name") or "").strip(),
        tipo=str(item.get("investmentType") or bruto.get("investment_type") or "").strip().upper(),
        emissor=str(item.get("issuer") or bruto.get("issuer") or "").strip(),
        distribuidor=str(item.get("distributor") or bruto.get("distributor") or "").strip(),
        indexador=indexador or "—",
        taxa_rotulo=taxa_rotulo,
        percentual_cdi=pct_cdi,
        taxa_prefixada_aa=taxa_prefix,
        investimento_minimo=float(minimo) if minimo is not None else None,
        data_vencimento_texto=vencimento_texto,
        dias_ate_vencimento=dias,
        taxa_liquida_aa=_para_float(item.get("netAnnualRate")),
        taxa_bruta_aa=_para_float(item.get("grossAnnualRate")),
        url_detalhe=str(item.get("detailUrl") or "").strip(),
    )


def _extrair_taxas(item: dict, bruto: dict, indexador: str) -> tuple[float | None, float | None]:
    indexador_upper = indexador.upper()
    if "CDI" in indexador_upper or indexador_upper in ("DI", "SELIC"):
        valor = bruto.get("profitability_rate") or bruto.get("rate_value")
        pct = _para_float(valor)
        if pct is None:
            nome = str(item.get("name") or "")
            match = re.search(r"(\d{1,3}(?:[.,]\d+)?)\s*%\s*CDI", nome, re.IGNORECASE)
            if match:
                pct = _para_float(match.group(1))
        return pct, None

    taxa = _para_float(item.get("grossAnnualRate"))
    if taxa is None:
        taxa = _para_float(bruto.get("taxa_anual_percent_gross"))
    return None, taxa


def _montar_rotulo_taxa(
    pct_cdi: float | None,
    taxa_prefix: float | None,
    indexador: str,
    item: dict,
    bruto: dict,
) -> str:
    if pct_cdi is not None:
        texto = f"{pct_cdi:.2f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{texto}% CDI"
    if taxa_prefix is not None:
        texto = f"{taxa_prefix:.2f}".replace(".", ",")
        return f"{texto}% a.a."
    if indexador:
        return indexador
    return str(item.get("name") or bruto.get("name") or "—")[:40]


def _formatar_vencimento(iso: str) -> tuple[str, int | None]:
    if not iso or not str(iso).strip():
        return "—", None
    texto = str(iso).strip()[:10]
    try:
        data_venc = datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return texto, None
    dias = (data_venc - date.today()).days
    if dias < 0:
        dias = 0
    return data_venc.strftime("%d/%m/%Y"), dias


def _para_float(valor) -> float | None:
    if valor is None:
        return None
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _nomes_instituicao_compativel(emissor: str, distribuidor: str) -> bool:
    """Comparacao aproximada emissor x distribuidor (nao ha filtro nativo na API)."""
    emissor_norm = _normalizar_nome_instituicao(emissor)
    distrib_norm = _normalizar_nome_instituicao(distribuidor)
    if not emissor_norm or not distrib_norm:
        return False
    return emissor_norm in distrib_norm or distrib_norm in emissor_norm


def _normalizar_nome_instituicao(nome: str) -> str:
    texto = (nome or "").lower()
    texto = re.sub(r"[^a-z0-9]", "", texto)
    for sufixo in ("sa", "s/a", "banco", "investimentos", "pactual"):
        texto = texto.replace(sufixo, "")
    return texto
