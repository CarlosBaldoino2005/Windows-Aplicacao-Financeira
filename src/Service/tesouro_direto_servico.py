"""Carga de cotacoes oficiais do Tesouro Direto (CSV Tesouro Transparente)."""
from __future__ import annotations

import csv
import io
import ssl
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

from src.Model.tesouro_informacoes import (
    montar_identificador_titulo,
    obter_familia_por_tipo,
)
from src.Model.titulo_tesouro import (
    DetalhesTituloTesouro,
    HistoricoPuTesouro,
    PainelTesouro,
    TituloTesouro,
)
from src.Tool.registrador_log import RegistradorLog

URL_CSV_TESOURO = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/precotaxatesourodireto.csv"
)
TIMEOUT_SEGUNDOS = 90
USER_AGENT = "Financeiro-Desktop/1.0"
DIAS_HISTORICO_VOLATILIDADE = 90


def _parse_data_ptbr(texto: str) -> date | None:
    texto = (texto or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


def _parse_numero_ptbr(texto: str) -> float | None:
    texto = (texto or "").strip()
    if not texto or texto == "-":
        return None
    limpo = texto.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


class TesouroDiretoServico:
    """Baixa e interpreta o CSV oficial de precos do Tesouro Direto."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._linhas_brutas: list[dict[str, str]] | None = None
        self._data_download: datetime | None = None
        self._pasta_cache = Path(__file__).resolve().parents[2] / "dados"
        self._arquivo_cache = self._pasta_cache / "cache_tesouro_precos.csv"

    def obter_painel(self, forcar_atualizacao: bool = False) -> tuple[PainelTesouro | None, str | None]:
        """Lista titulos com cotacao na data base mais recente do CSV."""
        linhas, erro = self._carregar_linhas(forcar_atualizacao)
        if erro:
            return None, erro
        if not linhas:
            return None, "Nenhum dado de Tesouro Direto disponivel no momento."

        datas_base = [
            _parse_data_ptbr(linha.get("Data Base", ""))
            for linha in linhas
        ]
        datas_validas = [d for d in datas_base if d is not None]
        if not datas_validas:
            return None, "Data base invalida no arquivo oficial do Tesouro."

        data_base = max(datas_validas)
        hoje = date.today()
        titulos: list[TituloTesouro] = []

        for linha in linhas:
            data_linha = _parse_data_ptbr(linha.get("Data Base", ""))
            if data_linha != data_base:
                continue

            tipo = (linha.get("Tipo Titulo") or "").strip()
            venc_texto = (linha.get("Data Vencimento") or "").strip()
            vencimento = _parse_data_ptbr(venc_texto)
            if not tipo or vencimento is None:
                continue
            if vencimento < hoje:
                continue

            titulos.append(
                TituloTesouro(
                    identificador=montar_identificador_titulo(tipo, venc_texto),
                    tipo_titulo=tipo,
                    familia=obter_familia_por_tipo(tipo),
                    data_vencimento=vencimento,
                    data_vencimento_texto=venc_texto,
                    data_base=data_base,
                    data_base_texto=data_base.strftime("%d/%m/%Y"),
                    taxa_compra=_parse_numero_ptbr(linha.get("Taxa Compra Manha", "")),
                    taxa_venda=_parse_numero_ptbr(linha.get("Taxa Venda Manha", "")),
                    pu_compra=_parse_numero_ptbr(linha.get("PU Compra Manha", "")),
                    pu_venda=_parse_numero_ptbr(linha.get("PU Venda Manha", "")),
                    pu_base=_parse_numero_ptbr(linha.get("PU Base Manha", "")),
                )
            )

        titulos.sort(key=lambda t: (t.familia, t.data_vencimento, t.tipo_titulo))
        familias = sorted({t.familia for t in titulos})

        aviso = (
            "Cotacoes oficiais (Tesouro Transparente). Uso educacional — "
            "nao e recomendacao de investimento."
        )
        return (
            PainelTesouro(
                titulos=titulos,
                data_base_texto=data_base.strftime("%d/%m/%Y"),
                familias=familias,
                aviso=aviso,
            ),
            None,
        )

    def obter_detalhes(self, identificador: str) -> tuple[DetalhesTituloTesouro | None, str | None]:
        """Detalhes de um titulo, com historico recente de PU para volatilidade indicativa."""
        if not identificador or "|" not in identificador:
            return None, "Titulo invalido."

        tipo, venc_texto = identificador.split("|", 1)
        tipo = tipo.strip()
        venc_texto = venc_texto.strip()
        if not tipo or not venc_texto:
            return None, "Titulo invalido."

        painel, erro = self.obter_painel()
        if erro or painel is None:
            return None, erro or "Painel indisponivel."

        titulo = next((t for t in painel.titulos if t.identificador == identificador), None)
        if titulo is None:
            return None, "Titulo nao encontrado na cotacao mais recente."

        linhas, erro_hist = self._carregar_linhas(False)
        if erro_hist or not linhas:
            return DetalhesTituloTesouro(titulo=titulo), None

        historico: list[HistoricoPuTesouro] = []
        for linha in linhas:
            if (linha.get("Tipo Titulo") or "").strip() != tipo:
                continue
            if (linha.get("Data Vencimento") or "").strip() != venc_texto:
                continue
            data_base = _parse_data_ptbr(linha.get("Data Base", ""))
            if data_base is None:
                continue
            historico.append(
                HistoricoPuTesouro(
                    data_base_texto=data_base.strftime("%d/%m/%Y"),
                    pu_base=_parse_numero_ptbr(linha.get("PU Base Manha", "")),
                )
            )

        historico.sort(key=lambda h: datetime.strptime(h.data_base_texto, "%d/%m/%Y"))
        historico = self._filtrar_historico_recente(historico, DIAS_HISTORICO_VOLATILIDADE)
        volatilidade, amplitude = self._calcular_volatilidade_indicativa(historico)

        return (
            DetalhesTituloTesouro(
                titulo=titulo,
                historico_pu=historico,
                volatilidade_indicativa_pct=volatilidade,
                amplitude_pu_pct=amplitude,
            ),
            None,
        )

    def _filtrar_historico_recente(
        self,
        historico: list[HistoricoPuTesouro],
        dias: int,
    ) -> list[HistoricoPuTesouro]:
        if not historico:
            return []
        ultima = datetime.strptime(historico[-1].data_base_texto, "%d/%m/%Y").date()
        limite = ultima - timedelta(days=dias)
        filtrado: list[HistoricoPuTesouro] = []
        for ponto in historico:
            data_ponto = datetime.strptime(ponto.data_base_texto, "%d/%m/%Y").date()
            if data_ponto >= limite:
                filtrado.append(ponto)
        return filtrado

    def _calcular_volatilidade_indicativa(
        self,
        historico: list[HistoricoPuTesouro],
    ) -> tuple[float | None, float | None]:
        valores = [p.pu_base for p in historico if p.pu_base is not None and p.pu_base > 0]
        if len(valores) < 2:
            return None, None

        media = sum(valores) / len(valores)
        if media <= 0:
            return None, None

        variancia = sum((v - media) ** 2 for v in valores) / len(valores)
        desvio = variancia ** 0.5
        volatilidade_pct = (desvio / media) * 100

        minimo = min(valores)
        maximo = max(valores)
        amplitude_pct = ((maximo - minimo) / media) * 100

        return round(volatilidade_pct, 2), round(amplitude_pct, 2)

    def _carregar_linhas(
        self,
        forcar_atualizacao: bool,
    ) -> tuple[list[dict[str, str]] | None, str | None]:
        if (
            not forcar_atualizacao
            and self._linhas_brutas is not None
            and self._data_download is not None
            and datetime.now() - self._data_download < timedelta(hours=4)
        ):
            return self._linhas_brutas, None

        if not forcar_atualizacao and self._arquivo_cache.exists():
            try:
                idade = datetime.now() - datetime.fromtimestamp(self._arquivo_cache.stat().st_mtime)
                if idade < timedelta(hours=12):
                    texto = self._arquivo_cache.read_text(encoding="latin-1")
                    linhas = self._parse_csv(texto)
                    if linhas:
                        self._linhas_brutas = linhas
                        self._data_download = datetime.now()
                        return linhas, None
            except OSError as exc:
                self._log.aviso(f"Cache local Tesouro indisponivel: {exc}")

        texto, erro = self._baixar_csv()
        if erro:
            if self._arquivo_cache.exists():
                try:
                    texto_cache = self._arquivo_cache.read_text(encoding="latin-1")
                    linhas = self._parse_csv(texto_cache)
                    if linhas:
                        self._linhas_brutas = linhas
                        self._data_download = datetime.now()
                        self._log.aviso("Usando cache local do Tesouro apos falha no download.")
                        return linhas, None
                except OSError:
                    pass
            return None, erro

        linhas = self._parse_csv(texto or "")
        if not linhas:
            return None, "Arquivo oficial do Tesouro veio vazio ou em formato inesperado."

        self._linhas_brutas = linhas
        self._data_download = datetime.now()
        self._salvar_cache(texto or "")
        return linhas, None

    def _parse_csv(self, texto: str) -> list[dict[str, str]]:
        leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
        return [dict(linha) for linha in leitor if any(linha.values())]

    def _salvar_cache(self, texto: str) -> None:
        try:
            self._pasta_cache.mkdir(parents=True, exist_ok=True)
            self._arquivo_cache.write_text(texto, encoding="latin-1")
        except OSError as exc:
            self._log.aviso(f"Nao foi possivel gravar cache Tesouro: {exc}")

    def _baixar_csv(self) -> tuple[str | None, str | None]:
        contexto_ssl = ssl.create_default_context()
        requisicao = urllib.request.Request(
            URL_CSV_TESOURO,
            headers={"User-Agent": USER_AGENT},
        )
        try:
            with urllib.request.urlopen(
                requisicao,
                timeout=TIMEOUT_SEGUNDOS,
                context=contexto_ssl,
            ) as resposta:
                return resposta.read().decode("latin-1"), None
        except ssl.SSLError:
            contexto_inseguro = ssl.create_default_context()
            contexto_inseguro.check_hostname = False
            contexto_inseguro.verify_mode = ssl.CERT_NONE
            try:
                with urllib.request.urlopen(
                    requisicao,
                    timeout=TIMEOUT_SEGUNDOS,
                    context=contexto_inseguro,
                ) as resposta:
                    self._log.aviso("Download Tesouro com verificacao SSL relaxada.")
                    return resposta.read().decode("latin-1"), None
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                self._log.erro(f"Falha ao baixar CSV Tesouro: {exc}")
                return None, (
                    "Nao foi possivel baixar cotacoes do Tesouro Direto. "
                    "Verifique sua conexao e tente novamente."
                )
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            self._log.erro(f"Falha ao baixar CSV Tesouro: {exc}")
            return None, (
                "Nao foi possivel baixar cotacoes do Tesouro Direto. "
                "Verifique sua conexao e tente novamente."
            )
