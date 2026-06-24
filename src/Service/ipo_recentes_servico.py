"""Busca IPOs dos ultimos 30 dias (Brasil via CVM e mundo via StockAnalysis)."""
from __future__ import annotations

import io
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from urllib import request

import pandas as pd
import yfinance as yf

from src.Model.ipo_recente import LinhaIpoRecente
from src.Service.provedores.util_provedor import USER_AGENT, eh_acao_b3
from src.Tool.bdrs_helper import eh_bdr_b3
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo

_DIAS_JANELA = 30
_URL_STOCKANALYSIS = "https://stockanalysis.com/ipos/"
_URL_CVM_ZIP = "https://dados.cvm.gov.br/dados/OFERTA/DISTRIB/DADOS/oferta_distribuicao.zip"
_REGEX_IPO_SA = re.compile(
    r'\{s:"(?P<s>[^"]+)",n:"(?P<n>[^"]*)",ipoDate:"(?P<ipoDate>\d{4}-\d{2}-\d{2})"(?P<rest>[^}]*)\}'
)


@dataclass(frozen=True)
class _IpoBruto:
    simbolo: str
    nome: str
    mercado: str
    data_ipo: date
    preco_ipo: float | None
    moeda: str
    preco_referencia_fonte: float | None = None
    variacao_ipo_pct_fonte: float | None = None


class IpoRecentesServico:
    """Agrega fontes publicas e enriquece cotacoes do dia via Yahoo."""

    def __init__(self) -> None:
        self._log = RegistradorLog()
        self._cache_bdr: dict[str, str | None] = {}

    def listar_ultimos_30_dias(self) -> tuple[list[LinhaIpoRecente], str | None]:
        self._cache_bdr.clear()
        limite = date.today() - timedelta(days=_DIAS_JANELA)
        brutos: dict[str, _IpoBruto] = {}

        for item in self._buscar_ipos_globais_stockanalysis(limite):
            brutos[item.simbolo.upper()] = item

        for item in self._buscar_ipos_brasil_cvm(limite):
            chave = item.simbolo.upper()
            if chave not in brutos:
                brutos[chave] = item

        if not brutos:
            return [], (
                "Nenhum IPO encontrado nos ultimos 30 dias. "
                "Tente atualizar mais tarde."
            )

        lista_bruta = sorted(brutos.values(), key=lambda x: x.data_ipo, reverse=True)
        enriquecidas = self._enriquecer_em_lote(lista_bruta)
        enriquecidas.sort(key=lambda linha: linha.data_ipo, reverse=True)
        return enriquecidas, None

    def _buscar_ipos_globais_stockanalysis(self, limite: date) -> list[_IpoBruto]:
        html = self._baixar_texto(_URL_STOCKANALYSIS)
        if not html:
            return []

        saida: list[_IpoBruto] = []
        for match in _REGEX_IPO_SA.finditer(html):
            resto = match.group("rest")
            data_ipo = date.fromisoformat(match.group("ipoDate"))
            if data_ipo < limite:
                continue
            preco_ipo = self._extrair_numero_campo(resto, "ipoPrice")
            preco_ref = self._extrair_numero_campo(resto, "ippc")
            var_ipo = self._extrair_numero_campo(resto, "ipr")
            simbolo = match.group("s").strip().upper()
            if not simbolo:
                continue
            saida.append(
                _IpoBruto(
                    simbolo=simbolo,
                    nome=match.group("n").strip(),
                    mercado="EUA / Global",
                    data_ipo=data_ipo,
                    preco_ipo=preco_ipo,
                    moeda="USD",
                    preco_referencia_fonte=preco_ref,
                    variacao_ipo_pct_fonte=var_ipo,
                )
            )
        return saida

    def _buscar_ipos_brasil_cvm(self, limite: date) -> list[_IpoBruto]:
        try:
            dados_zip = self._baixar_bytes(_URL_CVM_ZIP)
            if not dados_zip:
                return []
        except Exception as exc:
            self._log.aviso(f"CVM IPO: falha ao baixar ofertas ({exc}).")
            return []

        saida: list[_IpoBruto] = []
        vistos: set[str] = set()

        try:
            with zipfile.ZipFile(io.BytesIO(dados_zip)) as arquivo_zip:
                with arquivo_zip.open("oferta_resolucao_160.csv") as arquivo_csv:
                    import csv

                    leitor = csv.DictReader(
                        io.TextIOWrapper(arquivo_csv, encoding="latin-1"),
                        delimiter=";",
                    )
                    for linha in leitor:
                        if not self._eh_oferta_acoes(linha.get("Valor_Mobiliario")):
                            continue
                        data_enc = self._parse_data(linha.get("Data_Encerramento"))
                        if data_enc is None or data_enc < limite:
                            continue
                        nome = (linha.get("Nome_Emissor") or "").strip()
                        if not nome:
                            continue
                        chave_nome = nome.upper()
                        if chave_nome in vistos:
                            continue
                        vistos.add(chave_nome)

                        simbolo = self._resolver_ticker_b3(nome)
                        if not simbolo:
                            continue

                        preco_ipo = self._calcular_preco_unitario_cvm(linha)
                        saida.append(
                            _IpoBruto(
                                simbolo=simbolo,
                                nome=nome,
                                mercado="B3",
                                data_ipo=data_enc,
                                preco_ipo=preco_ipo,
                                moeda="BRL",
                            )
                        )
        except Exception as exc:
            self._log.aviso(f"CVM IPO: falha ao ler CSV ({exc}).")
            return []

        return saida

    def _enriquecer_em_lote(self, brutos: list[_IpoBruto]) -> list[LinhaIpoRecente]:
        resultado: list[LinhaIpoRecente] = []
        workers = min(6, max(1, len(brutos)))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futuros = {
                executor.submit(self._enriquecer_linha, bruto): bruto for bruto in brutos
            }
            for futuro in as_completed(futuros):
                try:
                    linha = futuro.result()
                    if linha is not None:
                        resultado.append(linha)
                except Exception as exc:
                    bruto = futuros[futuro]
                    self._log.aviso(f"IPO {bruto.simbolo}: falha ao enriquecer ({exc}).")
        return resultado

    def _enriquecer_linha(self, bruto: _IpoBruto) -> LinhaIpoRecente | None:
        simbolo_yahoo = bruto.simbolo
        if bruto.mercado == "B3" and not simbolo_yahoo.endswith(".SA"):
            simbolo_ok, _ = normalizar_simbolo(simbolo_yahoo)
            simbolo_yahoo = simbolo_ok or f"{bruto.simbolo}.SA"

        ticker = yf.Ticker(simbolo_yahoo)
        preco_atual: float | None = None
        preco_fechamento: float | None = None
        preco_abertura_dia: float | None = None
        preco_baixa: float | None = None
        preco_alta: float | None = None
        hora_baixa: str | None = None
        hora_alta: str | None = None
        moeda = bruto.moeda

        try:
            intraday = ticker.history(period="1d", interval="5m", auto_adjust=True)
            if intraday is not None and not intraday.empty:
                preco_abertura_dia = float(intraday["Open"].iloc[0])
                preco_fechamento = float(intraday["Close"].iloc[-1])
                preco_atual = preco_fechamento
                idx_alta = intraday["High"].idxmax()
                idx_baixa = intraday["Low"].idxmin()
                preco_alta = float(intraday.loc[idx_alta, "High"])
                preco_baixa = float(intraday.loc[idx_baixa, "Low"])
                hora_alta = self._formatar_hora_cotacao(idx_alta)
                hora_baixa = self._formatar_hora_cotacao(idx_baixa)
        except Exception:
            pass

        if preco_atual is None:
            try:
                preco_atual = self._obter_preco_fast_info(ticker.fast_info)
                if preco_atual:
                    preco_fechamento = preco_atual
            except Exception:
                pass

        if preco_atual is None and bruto.preco_referencia_fonte:
            preco_atual = bruto.preco_referencia_fonte
            preco_fechamento = preco_atual

        if preco_atual is None:
            return None

        preco_ipo = bruto.preco_ipo
        if preco_ipo is None and preco_abertura_dia:
            preco_ipo = self._buscar_preco_ipo_historico(simbolo_yahoo, bruto.data_ipo)
        if preco_ipo is None:
            preco_ipo = preco_abertura_dia

        variacao_ipo_pct = None
        variacao_ipo_valor = None
        if preco_ipo and preco_ipo > 0:
            variacao_ipo_valor = preco_atual - preco_ipo
            variacao_ipo_pct = (variacao_ipo_valor / preco_ipo) * 100
        elif bruto.variacao_ipo_pct_fonte is not None:
            variacao_ipo_pct = bruto.variacao_ipo_pct_fonte

        variacao_baixa_pct = None
        variacao_alta_pct = None
        base_dia = preco_abertura_dia or preco_ipo
        if base_dia and base_dia > 0:
            if preco_baixa is not None:
                variacao_baixa_pct = ((preco_baixa - base_dia) / base_dia) * 100
            if preco_alta is not None:
                variacao_alta_pct = ((preco_alta - base_dia) / base_dia) * 100

        if eh_acao_b3(simbolo_yahoo):
            moeda = "BRL"

        simbolo_b3, na_b3 = self._resolver_listagem_b3(bruto, simbolo_yahoo)

        return LinhaIpoRecente(
            simbolo=simbolo_yahoo,
            nome=bruto.nome,
            mercado=bruto.mercado,
            na_b3=na_b3,
            simbolo_b3=simbolo_b3,
            data_ipo=bruto.data_ipo,
            abriu_hoje=bruto.data_ipo == date.today(),
            preco_abertura_capital=preco_ipo,
            preco_atual=preco_atual,
            variacao_desde_ipo_pct=variacao_ipo_pct,
            variacao_desde_ipo_valor=variacao_ipo_valor,
            preco_baixa_dia=preco_baixa,
            hora_baixa_dia=hora_baixa,
            variacao_baixa_dia_pct=variacao_baixa_pct,
            preco_alta_dia=preco_alta,
            hora_alta_dia=hora_alta,
            variacao_alta_dia_pct=variacao_alta_pct,
            preco_fechamento_dia=preco_fechamento,
            moeda=moeda,
        )

    def _resolver_listagem_b3(
        self,
        bruto: _IpoBruto,
        simbolo_yahoo: str,
    ) -> tuple[str | None, bool]:
        """Retorna ticker na B3 (acao ou BDR) e se ha listagem local."""
        if bruto.mercado == "B3" or eh_acao_b3(simbolo_yahoo):
            simbolo_b3 = simbolo_yahoo
            if not simbolo_b3.endswith(".SA"):
                simbolo_ok, _ = normalizar_simbolo(simbolo_b3)
                simbolo_b3 = simbolo_ok or f"{bruto.simbolo}.SA"
            return simbolo_b3, True

        bdr = self._buscar_bdr_b3_para_ipo_global(bruto.simbolo, bruto.nome)
        return bdr, bdr is not None

    def _buscar_bdr_b3_para_ipo_global(self, simbolo: str, nome: str) -> str | None:
        """Localiza BDR na B3 para IPO de mercado internacional (ex.: SPCX -> SPCX34.SA)."""
        chave_cache = f"{simbolo.upper()}|{nome.strip().upper()[:60]}"
        if chave_cache in self._cache_bdr:
            return self._cache_bdr[chave_cache]

        encontrado: str | None = None
        base = re.sub(r"[^A-Z0-9]", "", (simbolo or "").upper())
        if len(base) >= 4:
            prefixo = base[:4]
            for sufixo in ("34", "35"):
                candidato = f"{prefixo}{sufixo}.SA"
                if eh_bdr_b3(candidato) and self._ticker_negociado_b3(candidato):
                    encontrado = candidato
                    break

        if encontrado is None and len(nome.strip()) >= 3:
            encontrado = self._buscar_bdr_por_nome_empresa(nome)

        self._cache_bdr[chave_cache] = encontrado
        return encontrado

    def _buscar_bdr_por_nome_empresa(self, nome: str) -> str | None:
        try:
            busca = yf.Search(nome.strip(), max_results=12)
            busca.search()
            for item in busca.quotes or []:
                if item.get("quoteType") != "EQUITY":
                    continue
                simbolo = str(item.get("symbol", "")).strip().upper()
                if not simbolo.endswith(".SA"):
                    continue
                if not eh_bdr_b3(simbolo):
                    continue
                if self._ticker_negociado_b3(simbolo):
                    return simbolo
        except Exception as exc:
            self._log.aviso(f"Busca BDR para IPO ({nome[:40]}): {exc}")
        return None

    @staticmethod
    def _obter_preco_fast_info(info) -> float | None:
        preco = getattr(info, "last_price", None) or getattr(info, "regular_market_price", None)
        if preco is None:
            try:
                preco = info.get("last_price") or info.get("regular_market_price")
            except AttributeError:
                pass
        try:
            return float(preco) if preco is not None and float(preco) > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _ticker_negociado_b3(simbolo: str) -> bool:
        try:
            return IpoRecentesServico._obter_preco_fast_info(yf.Ticker(simbolo).fast_info) is not None
        except Exception:
            return False

    @staticmethod
    def _buscar_preco_ipo_historico(simbolo: str, data_ipo: date) -> float | None:
        try:
            inicio = data_ipo - timedelta(days=3)
            fim = data_ipo + timedelta(days=10)
            dados = yf.download(
                simbolo,
                start=inicio.isoformat(),
                end=(fim + timedelta(days=1)).isoformat(),
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            if dados is None or dados.empty or "Open" not in dados.columns:
                return None
            serie = dados["Open"].dropna()
            if serie.empty:
                return None
            return float(serie.iloc[0])
        except Exception:
            return None

    @staticmethod
    def _formatar_hora_cotacao(indice) -> str | None:
        try:
            if hasattr(indice, "tz_convert"):
                local = indice.tz_convert(None)
            else:
                local = indice
            return pd.Timestamp(local).strftime("%H:%M")
        except Exception:
            return None

    @staticmethod
    def _eh_oferta_acoes(valor_mobiliario: str | None) -> bool:
        texto = (valor_mobiliario or "").strip().upper()
        texto = texto.replace("Ç", "C").replace("Ã", "A")
        return texto in ("ACOES", "ACAO") or texto.startswith("ACOES ")

    @staticmethod
    def _calcular_preco_unitario_cvm(linha: dict) -> float | None:
        try:
            qtde = float((linha.get("Qtde_Total_Registrada") or "0").replace(",", "."))
            valor = float((linha.get("Valor_Total_Registrado") or "0").replace(",", "."))
            if qtde > 0 and valor > 0:
                return round(valor / qtde, 4)
        except (TypeError, ValueError):
            pass
        return None

    def _resolver_ticker_b3(self, nome_empresa: str) -> str | None:
        termo = nome_empresa.strip()
        if len(termo) < 3:
            return None
        try:
            busca = yf.Search(termo, max_results=8)
            busca.search()
            for item in busca.quotes or []:
                simbolo = str(item.get("symbol", "")).strip().upper()
                if simbolo.endswith(".SA"):
                    simbolo_ok, _ = normalizar_simbolo(simbolo)
                    return simbolo_ok
        except Exception as exc:
            self._log.aviso(f"Busca ticker B3 para IPO ({termo[:40]}): {exc}")
        return None

    @staticmethod
    def _parse_data(valor: str | None) -> date | None:
        texto = (valor or "").strip()[:10]
        if not texto:
            return None
        try:
            return date.fromisoformat(texto)
        except ValueError:
            return None

    @staticmethod
    def _extrair_numero_campo(resto: str, campo: str) -> float | None:
        match = re.search(rf"{campo}:([-0-9.]+)", resto)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _baixar_texto(url: str) -> str | None:
        try:
            requisicao = request.Request(url, headers={"User-Agent": USER_AGENT})
            with request.urlopen(requisicao, timeout=25) as resposta:
                return resposta.read().decode("utf-8", errors="replace")
        except Exception:
            return None

    @staticmethod
    def _baixar_bytes(url: str) -> bytes | None:
        requisicao = request.Request(url, headers={"User-Agent": USER_AGENT})
        with request.urlopen(requisicao, timeout=90) as resposta:
            return resposta.read()
