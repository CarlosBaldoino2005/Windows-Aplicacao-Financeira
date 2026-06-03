"""Busca noticias de mercado via Yahoo Finance (yfinance)."""
from __future__ import annotations

import unicodedata
from datetime import datetime, timezone

import yfinance as yf

from src.Model.noticia_mercado import NoticiaMercado
from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Tool.registrador_log import RegistradorLog
from src.Tool.validadores import normalizar_simbolo

# Fontes para noticias gerais (Brasil + EUA / mercado global).
_FONTES_MERCADO: list[tuple[str, str]] = [
    ("^BVSP", "Brasil"),
    ("EWZ", "Brasil"),
    ("SPY", "EUA"),
    ("^GSPC", "EUA"),
]

_LIMITE_POR_FONTE = 8
_LIMITE_TOTAL = 40
_LIMITE_POR_SIMBOLO_PESQUISA = 10
_LIMITE_SIMBOLOS_PESQUISA = 5
_LIMITE_TOTAL_PESQUISA = 35

# Termos comuns em portugues mapeados para palavras frequentes nas manchetes em ingles.
_TERMOS_BUSCA_EN: dict[str, str] = {
    "inflacao": "inflation",
    "inflação": "inflation",
    "juros": "interest rate",
    "selic": "brazil rate",
    "dolar": "dollar",
    "dólar": "dollar",
    "petroleo": "oil",
    "petróleo": "oil",
    "ouro": "gold",
    "bitcoin": "bitcoin",
    "crypto": "crypto",
    "cripto": "crypto",
    "fed": "fed",
    "bovespa": "bovespa",
    "ibovespa": "ibovespa",
}


class NoticiasMercadoServico:
    """Agrega e ordena noticias das principais referencias de mercado."""

    def __init__(
        self,
        fontes: list[tuple[str, str]] | None = None,
        busca=None,
    ) -> None:
        self._log = RegistradorLog()
        self._fontes = fontes or _FONTES_MERCADO
        self._busca_acoes = busca or BuscaAcoesServico()

    def listar_principais(self) -> tuple[list[NoticiaMercado], str | None]:
        """Retorna noticias recentes deduplicadas ou mensagem de erro."""
        vistos_ids: set[str] = set()
        vistos_titulos: set[str] = set()
        coletadas: list[NoticiaMercado] = []

        for simbolo, regiao in self._fontes:
            try:
                brutas = yf.Ticker(simbolo).news or []
            except Exception as exc:
                self._log.aviso(f"Noticias indisponiveis para {simbolo}: {exc}")
                continue

            adicionadas_fonte = 0
            for item in brutas:
                if adicionadas_fonte >= _LIMITE_POR_FONTE:
                    break
                noticia = self._converter_item(item, regiao)
                if noticia is None:
                    continue
                chave_titulo = self._normalizar_titulo(noticia.titulo)
                if noticia.id in vistos_ids or chave_titulo in vistos_titulos:
                    continue
                vistos_ids.add(noticia.id)
                vistos_titulos.add(chave_titulo)
                coletadas.append(noticia)
                adicionadas_fonte += 1

        if not coletadas:
            return [], "Nenhuma noticia disponivel no momento. Tente atualizar mais tarde."

        coletadas.sort(
            key=lambda n: n.data_publicacao or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return coletadas[:_LIMITE_TOTAL], None

    def pesquisar(self, termo: str) -> tuple[list[NoticiaMercado], str | None]:
        """Busca noticias por codigo, empresa ou palavra-chave no titulo/resumo."""
        texto = (termo or "").strip()
        if len(texto) < 2:
            return [], "Digite pelo menos 2 caracteres para pesquisar."

        fontes = self._resolver_fontes_pesquisa(texto)
        coletadas = self._coletar_de_simbolos(fontes, _LIMITE_POR_SIMBOLO_PESQUISA)

        termo_chave = self._normalizar_texto_busca(texto)
        extras = self._filtrar_por_palavra_chave(termo_chave, texto)
        if extras:
            coletadas = self._mesclar_sem_duplicar(coletadas, extras)

        if not coletadas:
            return [], (
                f"Nenhuma noticia encontrada para \"{texto}\". "
                "Tente um codigo (PETR4, AAPL), nome da empresa ou outro termo."
            )

        coletadas.sort(
            key=lambda n: n.data_publicacao or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return coletadas[:_LIMITE_TOTAL_PESQUISA], None

    def _resolver_fontes_pesquisa(self, termo: str) -> list[tuple[str, str, str]]:
        """Retorna lista (simbolo, regiao, referencia exibida)."""
        vistos: set[str] = set()
        fontes: list[tuple[str, str, str]] = []

        def incluir(simbolo: str, nome_exibicao: str) -> None:
            if not simbolo or simbolo in vistos:
                return
            vistos.add(simbolo)
            regiao = "Brasil" if simbolo.upper().endswith(".SA") else "EUA"
            fontes.append((simbolo, regiao, nome_exibicao))

        simbolo_direto, erro = normalizar_simbolo(termo)
        if not erro:
            rotulo = simbolo_direto.replace(".SA", "")
            incluir(simbolo_direto, rotulo)

        try:
            resultados, _msg = self._busca_acoes.buscar(termo)
        except Exception as exc:
            self._log.aviso(f"Busca de acoes para noticias falhou: {exc}")
            resultados = []

        for item in resultados[:_LIMITE_SIMBOLOS_PESQUISA]:
            codigo = item.simbolo.replace(".SA", "")
            rotulo = f"{codigo} — {item.nome}"
            incluir(item.simbolo, rotulo)

        return fontes[:_LIMITE_SIMBOLOS_PESQUISA]

    def _coletar_de_simbolos(
        self,
        fontes: list[tuple[str, str, str]],
        limite_por_fonte: int,
    ) -> list[NoticiaMercado]:
        vistos_ids: set[str] = set()
        vistos_titulos: set[str] = set()
        coletadas: list[NoticiaMercado] = []

        for simbolo, regiao, referencia in fontes:
            try:
                brutas = yf.Ticker(simbolo).news or []
            except Exception as exc:
                self._log.aviso(f"Noticias indisponiveis para {simbolo}: {exc}")
                continue

            adicionadas = 0
            for item in brutas:
                if adicionadas >= limite_por_fonte:
                    break
                noticia = self._converter_item(item, regiao, referencia)
                if noticia is None:
                    continue
                chave = self._normalizar_titulo(noticia.titulo)
                if noticia.id in vistos_ids or chave in vistos_titulos:
                    continue
                vistos_ids.add(noticia.id)
                vistos_titulos.add(chave)
                coletadas.append(noticia)
                adicionadas += 1

        return coletadas

    @staticmethod
    def _normalizar_texto_busca(texto: str) -> str:
        sem_acento = "".join(
            c
            for c in unicodedata.normalize("NFD", texto.lower())
            if unicodedata.category(c) != "Mn"
        )
        return sem_acento.strip()

    def _filtrar_por_palavra_chave(
        self, termo_chave: str, termo_original: str
    ) -> list[NoticiaMercado]:
        """Filtra manchetes gerais pelo texto digitado (pt-BR ou termos em ingles)."""
        gerais, erro = self.listar_principais()
        if erro or not gerais:
            return []

        chave_sem_acento = self._normalizar_texto_busca(termo_original)
        termos_busca = {termo_chave, chave_sem_acento}
        if chave_sem_acento in _TERMOS_BUSCA_EN:
            termos_busca.add(_TERMOS_BUSCA_EN[chave_sem_acento])
        if termo_original.lower() in _TERMOS_BUSCA_EN:
            termos_busca.add(_TERMOS_BUSCA_EN[termo_original.lower()])

        palavras: list[str] = []
        for termo in termos_busca:
            palavras.extend(p for p in termo.split() if len(p) >= 2)
        if not palavras:
            palavras = list(termos_busca)

        filtradas: list[NoticiaMercado] = []
        for noticia in gerais:
            texto = self._normalizar_texto_busca(f"{noticia.titulo} {noticia.resumo}")
            bate = any(termo in texto for termo in termos_busca if len(termo) >= 2)
            if not bate:
                bate = any(palavra in texto for palavra in palavras)
            if bate:
                copia = NoticiaMercado(
                    id=noticia.id,
                    titulo=noticia.titulo,
                    resumo=noticia.resumo,
                    data_publicacao=noticia.data_publicacao,
                    data_exibicao=noticia.data_exibicao,
                    fonte=noticia.fonte,
                    url=noticia.url,
                    regiao=noticia.regiao,
                    referencia="Mercado geral",
                    url_imagem=noticia.url_imagem,
                )
                filtradas.append(copia)
        return filtradas

    @staticmethod
    def _mesclar_sem_duplicar(
        base: list[NoticiaMercado],
        extras: list[NoticiaMercado],
    ) -> list[NoticiaMercado]:
        vistos = {n.id for n in base}
        titulos = {NoticiasMercadoServico._normalizar_titulo(n.titulo) for n in base}
        resultado = list(base)
        for noticia in extras:
            chave = NoticiasMercadoServico._normalizar_titulo(noticia.titulo)
            if noticia.id in vistos or chave in titulos:
                continue
            vistos.add(noticia.id)
            titulos.add(chave)
            resultado.append(noticia)
        return resultado

    @staticmethod
    def _normalizar_titulo(titulo: str) -> str:
        return " ".join(titulo.lower().split())[:120]

    def _converter_item(
        self, item: dict, regiao: str, referencia: str = ""
    ) -> NoticiaMercado | None:
        conteudo = item.get("content") if isinstance(item.get("content"), dict) else item
        if not isinstance(conteudo, dict):
            return None

        titulo = (conteudo.get("title") or "").strip()
        if not titulo:
            return None

        resumo = (
            (conteudo.get("summary") or conteudo.get("description") or "").strip()
        )
        if len(resumo) > 400:
            resumo = resumo[:397] + "..."

        data_pub = self._parsear_data(conteudo.get("pubDate") or conteudo.get("displayTime"))
        identificador = str(item.get("id") or conteudo.get("id") or titulo[:80])

        return NoticiaMercado(
            id=identificador,
            titulo=titulo,
            resumo=resumo,
            data_publicacao=data_pub,
            data_exibicao=self._formatar_data_ptbr(data_pub),
            fonte=self._extrair_fonte(conteudo),
            url=self._extrair_url(conteudo),
            regiao=regiao,
            referencia=referencia,
            url_imagem=self._extrair_url_imagem(conteudo),
        )

    @staticmethod
    def _parsear_data(valor: str | None) -> datetime | None:
        if not valor or not isinstance(valor, str):
            return None
        texto = valor.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(texto)
        except ValueError:
            return None

    @staticmethod
    def _formatar_data_ptbr(data: datetime | None) -> str:
        if data is None:
            return "Data nao informada"
        local = data.astimezone() if data.tzinfo else data
        return local.strftime("%d/%m/%Y %H:%M")

    @staticmethod
    def _extrair_fonte(conteudo: dict) -> str:
        provedor = conteudo.get("provider")
        if isinstance(provedor, dict):
            nome = (provedor.get("displayName") or "").strip()
            if nome:
                return nome
        return "Yahoo Finance"

    @staticmethod
    def _extrair_url_imagem(conteudo: dict) -> str:
        """URL da miniatura (Yahoo Finance) quando disponivel."""
        miniatura = conteudo.get("thumbnail")
        if not isinstance(miniatura, dict):
            return ""

        original = (miniatura.get("originalUrl") or "").strip()
        if original.startswith("http"):
            return original

        resolucoes = miniatura.get("resolutions")
        if isinstance(resolucoes, list):
            melhor = ""
            maior_largura = 0
            for item in resolucoes:
                if not isinstance(item, dict):
                    continue
                url = (item.get("url") or "").strip()
                largura = int(item.get("width") or 0)
                if url.startswith("http") and largura >= maior_largura:
                    maior_largura = largura
                    melhor = url
            if melhor:
                return melhor

        return ""

    @staticmethod
    def _extrair_url(conteudo: dict) -> str:
        for chave in ("clickThroughUrl", "canonicalUrl", "previewUrl"):
            valor = conteudo.get(chave)
            if isinstance(valor, dict):
                url = (valor.get("url") or "").strip()
                if url.startswith("http"):
                    return url
            elif isinstance(valor, str) and valor.startswith("http"):
                return valor
        return ""
