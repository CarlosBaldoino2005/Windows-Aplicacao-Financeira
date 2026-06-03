"""Leitura e gravacao de configuracoes do painel e do grafico em dados/painel.ini."""
from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

from src.Model.acoes_universo import QUANTIDADE_PADRAO_PAINEL
from src.Model.cripto_universo import QUANTIDADE_PADRAO_CRIPTO
from src.Tool.registrador_log import RegistradorLog
from src.Model.opcoes_fonte_grid import FONTE_GRID_PADRAO, OpcoesFonteGrid
from src.Model.opcoes_fotos_noticias import FOTOS_PADRAO, OpcoesFotosNoticias
from src.Tool.validadores import (
    validar_fonte_grid,
    validar_fotos_noticias,
    validar_modo_aparencia,
    validar_quantidade_acoes,
    validar_quantidade_cotas,
    validar_quantidade_cripto,
)
from src.View.tema import MODO_PADRAO

SECAO_PAINEL = "PAINEL"
CHAVE_QUANTIDADE_ACOES = "quantidade_acoes"
CHAVE_QUANTIDADE_COTAS_GRAFICO = "quantidade_cotas_grafico"
CHAVE_MODO_APARENCIA = "modo_aparencia"
CHAVE_FOTOS_NOTICIAS = "fotos_noticias"
CHAVE_FONTE_GRID = "fonte_grid"
CHAVE_QUANTIDADE_CRIPTO = "quantidade_cripto"
QUANTIDADE_PADRAO_COTAS_GRAFICO = 100
NOME_ARQUIVO = "painel.ini"


class ConfigPainelIni:
    """Gerencia dados/painel.ini — painel principal e simulacao no grafico."""

    def __init__(self, pasta_base: Path | None = None) -> None:
        raiz = pasta_base or Path(__file__).resolve().parents[2]
        self._pasta_dados = raiz / "dados"
        self._pasta_dados.mkdir(parents=True, exist_ok=True)
        self._caminho_ini = self._pasta_dados / NOME_ARQUIVO
        self._log = RegistradorLog(raiz)

    @property
    def caminho_arquivo(self) -> Path:
        return self._caminho_ini

    def padrao_painel(self) -> int:
        return QUANTIDADE_PADRAO_PAINEL

    def padrao_cotas_grafico(self) -> int:
        return QUANTIDADE_PADRAO_COTAS_GRAFICO

    def padrao_modo_aparencia(self) -> str:
        return MODO_PADRAO

    def padrao_fotos_noticias(self) -> str:
        return FOTOS_PADRAO

    def padrao_fonte_grid(self) -> str:
        return FONTE_GRID_PADRAO

    def padrao_quantidade_cripto(self) -> int:
        return QUANTIDADE_PADRAO_CRIPTO

    def carregar_quantidade_cripto(self) -> int:
        """Quantidade de criptos nas abas Em alta, Em queda e Todas."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_QUANTIDADE_CRIPTO in secao:
            return self._ler_quantidade_cripto(secao.get(CHAVE_QUANTIDADE_CRIPTO))
        valor = self.padrao_quantidade_cripto()
        self.salvar_quantidade_cripto(valor)
        return valor

    def salvar_quantidade_cripto(self, quantidade: int) -> None:
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_QUANTIDADE_CRIPTO] = str(quantidade)
        self._gravar(parser)

    def carregar_fotos_noticias(self) -> str:
        """Tamanho das miniaturas nas noticias: nenhum, pequeno, medio ou grande."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_FOTOS_NOTICIAS in secao:
            modo, _ = validar_fotos_noticias(secao.get(CHAVE_FOTOS_NOTICIAS, ""))
            return modo
        modo = self.padrao_fotos_noticias()
        self.salvar_fotos_noticias(modo)
        return modo

    def carregar_opcoes_fotos_noticias(self) -> OpcoesFotosNoticias:
        return OpcoesFotosNoticias.a_partir_modo(self.carregar_fotos_noticias())

    def salvar_fotos_noticias(self, modo: str) -> None:
        modo_ok, _ = validar_fotos_noticias(modo)
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_FOTOS_NOTICIAS] = modo_ok
        self._gravar(parser)

    def carregar_fonte_grid(self) -> str:
        """Tamanho da fonte nas grids: pequeno, medio ou grande."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_FONTE_GRID in secao:
            modo, _ = validar_fonte_grid(secao.get(CHAVE_FONTE_GRID, ""))
            return modo
        modo = self.padrao_fonte_grid()
        self.salvar_fonte_grid(modo)
        return modo

    def carregar_opcoes_fonte_grid(self) -> OpcoesFonteGrid:
        return OpcoesFonteGrid.a_partir_modo(self.carregar_fonte_grid())

    def salvar_fonte_grid(self, modo: str) -> None:
        modo_ok, _ = validar_fonte_grid(modo)
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_FONTE_GRID] = modo_ok
        self._gravar(parser)

    def carregar_modo_aparencia(self) -> str:
        """Modo visual: claro ou escuro."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_MODO_APARENCIA in secao:
            modo, _ = validar_modo_aparencia(secao.get(CHAVE_MODO_APARENCIA, ""))
            return modo
        modo = self.padrao_modo_aparencia()
        self.salvar_modo_aparencia(modo)
        return modo

    def salvar_modo_aparencia(self, modo: str) -> None:
        modo_ok, _ = validar_modo_aparencia(modo)
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_MODO_APARENCIA] = modo_ok
        self._gravar(parser)

    def carregar(self) -> int:
        """Quantidade de acoes listadas no painel (Em alta, Em queda, Todas)."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_QUANTIDADE_ACOES in secao:
            return self._ler_quantidade_acoes(secao.get(CHAVE_QUANTIDADE_ACOES))

        for chave_antiga in (
            "quantidade_todas",
            "quantidade_em_alta",
            "quantidade_em_baixa",
        ):
            if chave_antiga in secao:
                valor = self._ler_quantidade_acoes(secao.get(chave_antiga))
                self.salvar(valor)
                return valor

        valor = self.padrao_painel()
        self.salvar(valor)
        return valor

    def carregar_quantidade_cotas_grafico(self) -> int:
        """Quantidade de acoes/cotas na simulacao da janela de grafico."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_QUANTIDADE_COTAS_GRAFICO in secao:
            return self._ler_quantidade_cotas(secao.get(CHAVE_QUANTIDADE_COTAS_GRAFICO))
        valor = self.padrao_cotas_grafico()
        self.salvar_quantidade_cotas_grafico(valor)
        return valor

    def salvar(self, quantidade: int) -> None:
        """Grava quantidade do painel preservando demais chaves do INI."""
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_QUANTIDADE_ACOES] = str(quantidade)
        self._gravar(parser)

    def salvar_quantidade_cotas_grafico(self, quantidade: int) -> None:
        """Grava quantidade do grafico preservando demais chaves do INI."""
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_QUANTIDADE_COTAS_GRAFICO] = str(quantidade)
        self._gravar(parser)

    def _ler_ou_criar_secao(self) -> dict[str, str]:
        if not self._caminho_ini.exists():
            self.salvar(self.padrao_painel())
            self.salvar_quantidade_cotas_grafico(self.padrao_cotas_grafico())
            self.salvar_modo_aparencia(self.padrao_modo_aparencia())
            self.salvar_fotos_noticias(self.padrao_fotos_noticias())
            self.salvar_fonte_grid(self.padrao_fonte_grid())

        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            self.salvar(self.padrao_painel())
            self.salvar_quantidade_cotas_grafico(self.padrao_cotas_grafico())
            self.salvar_modo_aparencia(self.padrao_modo_aparencia())
            self.salvar_fotos_noticias(self.padrao_fotos_noticias())
            self.salvar_fonte_grid(self.padrao_fonte_grid())
            parser = self._ler_parser()

        return dict(parser[SECAO_PAINEL])

    def _ler_parser(self) -> ConfigParser:
        parser = ConfigParser()
        if self._caminho_ini.exists():
            try:
                parser.read(self._caminho_ini, encoding="utf-8")
            except Exception as exc:
                self._log.erro(f"Falha ao ler {NOME_ARQUIVO}: {exc}")
        return parser

    def _gravar(self, parser: ConfigParser) -> None:
        try:
            with open(self._caminho_ini, "w", encoding="utf-8") as arquivo:
                parser.write(arquivo)
        except OSError as exc:
            self._log.erro(f"Falha ao salvar {NOME_ARQUIVO}: {exc}")
            raise

    def _ler_quantidade_acoes(self, texto: str) -> int:
        valor, erro = validar_quantidade_acoes(texto)
        if erro or valor is None:
            return self.padrao_painel()
        return valor

    def _ler_quantidade_cripto(self, texto: str) -> int:
        valor, erro = validar_quantidade_cripto(texto)
        if erro or valor is None:
            return self.padrao_quantidade_cripto()
        return valor

    def _ler_quantidade_cotas(self, texto: str) -> int:
        valor, erro = validar_quantidade_cotas(
            texto,
            padrao=self.padrao_cotas_grafico(),
        )
        if erro or valor is None:
            return self.padrao_cotas_grafico()
        return valor
