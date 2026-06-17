"""Leitura e gravacao de configuracoes do painel e do grafico em dados/painel.ini."""
from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

from src.Model.opcoes_atualizacao_automatica import (
    ATUALIZACAO_AUTOMATICA_HABILITADA_PADRAO,
    CARTEIRA_ATUALIZACAO_AUTOMATICA_HABILITADA_PADRAO,
    CARTEIRA_INTERVALO_PADRAO_SEGUNDOS,
    INTERVALO_MAXIMO_SEGUNDOS,
    INTERVALO_MINIMO_SEGUNDOS,
    INTERVALO_PADRAO_SEGUNDOS,
    OpcoesAtualizacaoAutomatica,
)
from src.Model.opcoes_relatorio_automatico_carteira import (
    RELATORIO_AUTOMATICO_HABILITADO_PADRAO,
    RELATORIO_AUTOMATICO_HORARIOS_PADRAO,
    OpcoesRelatorioAutomaticoCarteira,
)
from src.Model.acoes_universo import QUANTIDADE_PADRAO_PAINEL
from src.Model.cripto_universo import QUANTIDADE_PADRAO_CRIPTO
from src.Tool.registrador_log import RegistradorLog
from src.Model.opcoes_fonte_grid import FONTE_GRID_PADRAO, OpcoesFonteGrid
from src.Model.opcoes_fotos_noticias import FOTOS_PADRAO, OpcoesFotosNoticias
from src.Tool.validadores import (
    validar_fonte_grid,
    validar_fotos_noticias,
    validar_intervalo_atualizacao_segundos,
    validar_modo_aparencia,
    validar_quantidade_acoes,
    validar_quantidade_cotas,
    validar_quantidade_cripto,
    validar_sim_nao_config,
)
from src.Model.provedores_noticias import (
    CATEGORIA_CRIPTO,
    CATEGORIA_MERCADO,
    PROVEDOR_PADRAO_CRIPTO,
    PROVEDOR_PADRAO_MERCADO,
)
from src.View.tema import MODO_PADRAO

SECAO_PAINEL = "PAINEL"
SECAO_JANELA = "JANELA"
CHAVE_MONITOR_DISPOSITIVO = "monitor_dispositivo"
CHAVE_PROVEDOR_NOTICIAS = "provedor_noticias"
CHAVE_PROVEDOR_NOTICIAS_CRIPTO = "provedor_noticias_cripto"
CHAVE_QUANTIDADE_ACOES = "quantidade_acoes"
CHAVE_QUANTIDADE_COTAS_GRAFICO = "quantidade_cotas_grafico"
CHAVE_MODO_APARENCIA = "modo_aparencia"
CHAVE_FOTOS_NOTICIAS = "fotos_noticias"
CHAVE_FONTE_GRID = "fonte_grid"
CHAVE_QUANTIDADE_CRIPTO = "quantidade_cripto"
CHAVE_VALOR_SIMULACAO_RENDA_FIXA = "valor_simulacao_renda_fixa"
CHAVE_VALOR_DISPONIVEL_CALCULAR_QUANTIDADE = "valor_disponivel_calcular_quantidade"
CHAVE_ATUALIZACAO_AUTOMATICA = "atualizacao_automatica"
CHAVE_INTERVALO_ATUALIZACAO_SEGUNDOS = "atualizacao_automatica_intervalo_segundos"
CHAVE_MONITORAMENTO_ATUALIZACAO_AUTOMATICA = "monitoramento_atualizacao_automatica"
CHAVE_MONITORAMENTO_INTERVALO_ATUALIZACAO_SEGUNDOS = (
    "monitoramento_atualizacao_intervalo_segundos"
)
CHAVE_MONITORAMENTO_PAUSADO = "monitoramento_pausado"
CHAVE_CARTEIRA_VARIACAO_MONITORAMENTO_PCT = "carteira_variacao_monitoramento_pct"
CHAVE_CARTEIRA_ATUALIZACAO_AUTOMATICA = "carteira_atualizacao_automatica"
CHAVE_CARTEIRA_INTERVALO_ATUALIZACAO_SEGUNDOS = "carteira_atualizacao_intervalo_segundos"
CHAVE_CARTEIRA_RELATORIO_AUTOMATICO = "carteira_relatorio_automatico"
CHAVE_CARTEIRA_RELATORIO_HORARIOS = "carteira_relatorio_horarios"
CHAVE_CARTEIRA_RELATORIO_EMAILS = "carteira_relatorio_emails"
SECAO_AGORA_ALERTAS = "AGORA_ALERTAS"
CARTEIRA_VARIACAO_PADRAO_PCT = 10.0
QUANTIDADE_PADRAO_COTAS_GRAFICO = 100
VALOR_PADRAO_SIMULACAO_RENDA_FIXA = 10000.0
VALOR_PADRAO_DISPONIVEL_CALCULAR_QUANTIDADE = 10000.0
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

    def padrao_valor_simulacao_renda_fixa(self) -> float:
        return VALOR_PADRAO_SIMULACAO_RENDA_FIXA

    def padrao_valor_disponivel_calcular_quantidade(self) -> float:
        return VALOR_PADRAO_DISPONIVEL_CALCULAR_QUANTIDADE

    def padrao_atualizacao_automatica_habilitada(self) -> bool:
        return ATUALIZACAO_AUTOMATICA_HABILITADA_PADRAO

    def padrao_intervalo_atualizacao_segundos(self) -> int:
        return INTERVALO_PADRAO_SEGUNDOS

    def carregar_atualizacao_automatica(self) -> OpcoesAtualizacaoAutomatica:
        """Atualizacao periodica global de cotacoes (painel, hubs e favoritos)."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_ATUALIZACAO_AUTOMATICA in secao:
            habilitada, _ = validar_sim_nao_config(
                secao.get(CHAVE_ATUALIZACAO_AUTOMATICA, ""),
                padrao=self.padrao_atualizacao_automatica_habilitada(),
            )
            intervalo, _ = validar_intervalo_atualizacao_segundos(
                secao.get(CHAVE_INTERVALO_ATUALIZACAO_SEGUNDOS, ""),
                padrao=self.padrao_intervalo_atualizacao_segundos(),
            )
            return OpcoesAtualizacaoAutomatica(
                habilitada=habilitada,
                intervalo_segundos=intervalo or self.padrao_intervalo_atualizacao_segundos(),
            )

        habilitada = self.padrao_atualizacao_automatica_habilitada()
        intervalo = self.padrao_intervalo_atualizacao_segundos()
        self.salvar_atualizacao_automatica(habilitada, intervalo)
        return OpcoesAtualizacaoAutomatica(habilitada=habilitada, intervalo_segundos=intervalo)

    def salvar_atualizacao_automatica(
        self,
        habilitada: bool,
        intervalo_segundos: int,
    ) -> None:
        intervalo_ok, _ = validar_intervalo_atualizacao_segundos(
            str(intervalo_segundos),
            padrao=self.padrao_intervalo_atualizacao_segundos(),
        )
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_ATUALIZACAO_AUTOMATICA] = "sim" if habilitada else "nao"
        parser[SECAO_PAINEL][CHAVE_INTERVALO_ATUALIZACAO_SEGUNDOS] = str(
            intervalo_ok or self.padrao_intervalo_atualizacao_segundos()
        )
        self._gravar(parser)

    def carregar_atualizacao_automatica_monitoramento(self) -> OpcoesAtualizacaoAutomatica:
        """Atualizacao periodica exclusiva da tela de monitoramento de precos."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_MONITORAMENTO_ATUALIZACAO_AUTOMATICA in secao:
            habilitada, _ = validar_sim_nao_config(
                secao.get(CHAVE_MONITORAMENTO_ATUALIZACAO_AUTOMATICA, ""),
                padrao=self.padrao_atualizacao_automatica_habilitada(),
            )
            intervalo, _ = validar_intervalo_atualizacao_segundos(
                secao.get(CHAVE_MONITORAMENTO_INTERVALO_ATUALIZACAO_SEGUNDOS, ""),
                padrao=self.padrao_intervalo_atualizacao_segundos(),
            )
            return OpcoesAtualizacaoAutomatica(
                habilitada=habilitada,
                intervalo_segundos=intervalo or self.padrao_intervalo_atualizacao_segundos(),
            )

        habilitada = self.padrao_atualizacao_automatica_habilitada()
        intervalo = self.padrao_intervalo_atualizacao_segundos()
        self.salvar_atualizacao_automatica_monitoramento(habilitada, intervalo)
        return OpcoesAtualizacaoAutomatica(habilitada=habilitada, intervalo_segundos=intervalo)

    def salvar_atualizacao_automatica_monitoramento(
        self,
        habilitada: bool,
        intervalo_segundos: int,
    ) -> None:
        intervalo_ok, _ = validar_intervalo_atualizacao_segundos(
            str(intervalo_segundos),
            padrao=self.padrao_intervalo_atualizacao_segundos(),
        )
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_MONITORAMENTO_ATUALIZACAO_AUTOMATICA] = (
            "sim" if habilitada else "nao"
        )
        parser[SECAO_PAINEL][CHAVE_MONITORAMENTO_INTERVALO_ATUALIZACAO_SEGUNDOS] = str(
            intervalo_ok or self.padrao_intervalo_atualizacao_segundos()
        )
        self._gravar(parser)

    def padrao_monitoramento_pausado(self) -> bool:
        return False

    def carregar_monitoramento_pausado(self) -> bool:
        """Indica se o monitoramento esta pausado (sem atualizacao automatica de alertas)."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_MONITORAMENTO_PAUSADO in secao:
            pausado, _ = validar_sim_nao_config(
                secao.get(CHAVE_MONITORAMENTO_PAUSADO, ""),
                padrao=self.padrao_monitoramento_pausado(),
            )
            return pausado

        pausado = self.padrao_monitoramento_pausado()
        self.salvar_monitoramento_pausado(pausado)
        return pausado

    def salvar_monitoramento_pausado(self, pausado: bool) -> None:
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_MONITORAMENTO_PAUSADO] = "sim" if pausado else "nao"
        self._gravar(parser)

    def padrao_carteira_variacao_monitoramento_pct(self) -> float:
        return CARTEIRA_VARIACAO_PADRAO_PCT

    def carregar_carteira_variacao_monitoramento_pct(self) -> float:
        """Percentual de variacao para limites de monitoramento ao cadastrar na carteira."""
        from src.Tool.validadores import validar_percentual_carteira

        secao = self._ler_ou_criar_secao()
        if CHAVE_CARTEIRA_VARIACAO_MONITORAMENTO_PCT in secao:
            pct, _ = validar_percentual_carteira(
                secao.get(CHAVE_CARTEIRA_VARIACAO_MONITORAMENTO_PCT, ""),
                padrao=self.padrao_carteira_variacao_monitoramento_pct(),
            )
            return pct or self.padrao_carteira_variacao_monitoramento_pct()

        padrao = self.padrao_carteira_variacao_monitoramento_pct()
        self.salvar_carteira_variacao_monitoramento_pct(padrao)
        return padrao

    def salvar_carteira_variacao_monitoramento_pct(self, valor: float) -> None:
        from src.Tool.validadores import validar_percentual_carteira

        pct, _ = validar_percentual_carteira(
            str(valor),
            padrao=self.padrao_carteira_variacao_monitoramento_pct(),
        )
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_CARTEIRA_VARIACAO_MONITORAMENTO_PCT] = str(
            pct or self.padrao_carteira_variacao_monitoramento_pct()
        )
        self._gravar(parser)

    def padrao_carteira_atualizacao_automatica_habilitada(self) -> bool:
        return CARTEIRA_ATUALIZACAO_AUTOMATICA_HABILITADA_PADRAO

    def padrao_carteira_intervalo_atualizacao_segundos(self) -> int:
        return CARTEIRA_INTERVALO_PADRAO_SEGUNDOS

    def carregar_atualizacao_automatica_carteira(self) -> OpcoesAtualizacaoAutomatica:
        """Atualizacao periodica exclusiva da tela de carteira de investimentos."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_CARTEIRA_ATUALIZACAO_AUTOMATICA in secao:
            habilitada, _ = validar_sim_nao_config(
                secao.get(CHAVE_CARTEIRA_ATUALIZACAO_AUTOMATICA, ""),
                padrao=self.padrao_carteira_atualizacao_automatica_habilitada(),
            )
            intervalo, _ = validar_intervalo_atualizacao_segundos(
                secao.get(CHAVE_CARTEIRA_INTERVALO_ATUALIZACAO_SEGUNDOS, ""),
                padrao=self.padrao_carteira_intervalo_atualizacao_segundos(),
            )
            return OpcoesAtualizacaoAutomatica(
                habilitada=habilitada,
                intervalo_segundos=intervalo or self.padrao_carteira_intervalo_atualizacao_segundos(),
            )

        habilitada = self.padrao_carteira_atualizacao_automatica_habilitada()
        intervalo = self.padrao_carteira_intervalo_atualizacao_segundos()
        self.salvar_atualizacao_automatica_carteira(habilitada, intervalo)
        return OpcoesAtualizacaoAutomatica(habilitada=habilitada, intervalo_segundos=intervalo)

    def salvar_atualizacao_automatica_carteira(
        self,
        habilitada: bool,
        intervalo_segundos: int,
    ) -> None:
        intervalo_ok, _ = validar_intervalo_atualizacao_segundos(
            str(intervalo_segundos),
            padrao=self.padrao_carteira_intervalo_atualizacao_segundos(),
        )
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_CARTEIRA_ATUALIZACAO_AUTOMATICA] = (
            "sim" if habilitada else "nao"
        )
        parser[SECAO_PAINEL][CHAVE_CARTEIRA_INTERVALO_ATUALIZACAO_SEGUNDOS] = str(
            intervalo_ok or self.padrao_carteira_intervalo_atualizacao_segundos()
        )
        self._gravar(parser)

    def padrao_relatorio_automatico_carteira_habilitado(self) -> bool:
        return RELATORIO_AUTOMATICO_HABILITADO_PADRAO

    def padrao_relatorio_automatico_carteira_horarios(self) -> tuple[str, ...]:
        return RELATORIO_AUTOMATICO_HORARIOS_PADRAO

    def carregar_relatorio_automatico_carteira(self) -> OpcoesRelatorioAutomaticoCarteira:
        """Relatorio PDF agendado da carteira (horarios fixos HH:MM)."""
        from src.Tool.validadores import (
            validar_lista_emails_relatorio,
            validar_lista_horarios_relatorio,
        )

        secao = self._ler_ou_criar_secao()
        if CHAVE_CARTEIRA_RELATORIO_AUTOMATICO in secao:
            habilitado, _ = validar_sim_nao_config(
                secao.get(CHAVE_CARTEIRA_RELATORIO_AUTOMATICO, ""),
                padrao=self.padrao_relatorio_automatico_carteira_habilitado(),
            )
            bruto_horarios = secao.get(CHAVE_CARTEIRA_RELATORIO_HORARIOS, "").strip()
            if not bruto_horarios:
                horarios = self.padrao_relatorio_automatico_carteira_horarios()
            else:
                lista, _ = validar_lista_horarios_relatorio(bruto_horarios.replace(";", ","))
                horarios = lista if lista else self.padrao_relatorio_automatico_carteira_horarios()

            bruto_emails = secao.get(CHAVE_CARTEIRA_RELATORIO_EMAILS, "").strip()
            emails: tuple[str, ...] = ()
            if bruto_emails:
                lista_emails, _ = validar_lista_emails_relatorio(bruto_emails.replace(";", ","))
                emails = lista_emails or ()

            return OpcoesRelatorioAutomaticoCarteira(
                habilitado=habilitado,
                horarios=horarios,
                emails_destinatarios=emails,
            )

        habilitado = self.padrao_relatorio_automatico_carteira_habilitado()
        horarios = self.padrao_relatorio_automatico_carteira_horarios()
        self.salvar_relatorio_automatico_carteira(habilitado, horarios, ())
        return OpcoesRelatorioAutomaticoCarteira(
            habilitado=habilitado,
            horarios=horarios,
            emails_destinatarios=(),
        )

    def salvar_relatorio_automatico_carteira(
        self,
        habilitado: bool,
        horarios: tuple[str, ...],
        emails_destinatarios: tuple[str, ...],
    ) -> None:
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_CARTEIRA_RELATORIO_AUTOMATICO] = (
            "sim" if habilitado else "nao"
        )
        parser[SECAO_PAINEL][CHAVE_CARTEIRA_RELATORIO_HORARIOS] = ";".join(horarios)
        parser[SECAO_PAINEL][CHAVE_CARTEIRA_RELATORIO_EMAILS] = ";".join(emails_destinatarios)
        self._gravar(parser)

    def carregar_valor_simulacao_renda_fixa(self) -> float:
        """Valor padrao para simulacoes de renda fixa (LCI, LCA, CDB, Tesouro)."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_VALOR_SIMULACAO_RENDA_FIXA in secao:
            return self._ler_valor_monetario_ini(
                secao.get(CHAVE_VALOR_SIMULACAO_RENDA_FIXA),
                self.padrao_valor_simulacao_renda_fixa(),
            )
        valor = self.padrao_valor_simulacao_renda_fixa()
        self.salvar_valor_simulacao_renda_fixa(valor)
        return valor

    def salvar_valor_simulacao_renda_fixa(self, valor: float) -> None:
        if valor <= 0:
            return
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_VALOR_SIMULACAO_RENDA_FIXA] = f"{round(valor, 2):.2f}"
        self._gravar(parser)

    def carregar_valor_disponivel_calcular_quantidade(self) -> float:
        """Valor disponivel na tela Calcular quantidade (padrao R$ 10.000,00)."""
        secao = self._ler_ou_criar_secao()
        if CHAVE_VALOR_DISPONIVEL_CALCULAR_QUANTIDADE in secao:
            return self._ler_valor_monetario_ini(
                secao.get(CHAVE_VALOR_DISPONIVEL_CALCULAR_QUANTIDADE),
                self.padrao_valor_disponivel_calcular_quantidade(),
            )
        valor = self.padrao_valor_disponivel_calcular_quantidade()
        self.salvar_valor_disponivel_calcular_quantidade(valor)
        return valor

    def salvar_valor_disponivel_calcular_quantidade(self, valor: float) -> None:
        if valor <= 0:
            return
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][CHAVE_VALOR_DISPONIVEL_CALCULAR_QUANTIDADE] = (
            f"{round(valor, 2):.2f}"
        )
        self._gravar(parser)

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

    def carregar_monitor_janela(self) -> str | None:
        """Identificador do monitor salvo (ex.: DISPLAY2) ou None se nunca gravado."""
        parser = self._ler_parser()
        if SECAO_JANELA not in parser:
            return None
        texto = (parser[SECAO_JANELA].get(CHAVE_MONITOR_DISPOSITIVO) or "").strip()
        if not texto:
            return None
        return texto.upper()

    def carregar_provedor_noticias(self) -> str:
        """Chave do servidor de noticias de mercado (ex.: brasil_ibovespa)."""
        return self._carregar_chave_provedor(
            CHAVE_PROVEDOR_NOTICIAS,
            PROVEDOR_PADRAO_MERCADO,
            CATEGORIA_MERCADO,
        )

    def salvar_provedor_noticias(self, chave: str) -> None:
        self._salvar_chave_provedor(
            CHAVE_PROVEDOR_NOTICIAS,
            chave,
            CATEGORIA_MERCADO,
        )

    def carregar_provedor_noticias_cripto(self) -> str:
        """Chave do servidor de noticias de criptomoedas."""
        return self._carregar_chave_provedor(
            CHAVE_PROVEDOR_NOTICIAS_CRIPTO,
            PROVEDOR_PADRAO_CRIPTO,
            CATEGORIA_CRIPTO,
        )

    def salvar_provedor_noticias_cripto(self, chave: str) -> None:
        self._salvar_chave_provedor(
            CHAVE_PROVEDOR_NOTICIAS_CRIPTO,
            chave,
            CATEGORIA_CRIPTO,
        )

    def _carregar_chave_provedor(
        self,
        chave_ini: str,
        padrao: str,
        categoria: str,
    ) -> str:
        from src.Tool.validadores import validar_provedor_noticias

        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            return padrao
        texto = (parser[SECAO_PAINEL].get(chave_ini) or "").strip()
        if not texto:
            return padrao
        chave_ok, _ = validar_provedor_noticias(texto, categoria)
        return chave_ok

    def _salvar_chave_provedor(
        self,
        chave_ini: str,
        chave_provedor: str,
        categoria: str,
    ) -> None:
        from src.Tool.validadores import validar_provedor_noticias

        chave_ok, _ = validar_provedor_noticias(chave_provedor, categoria)
        parser = self._ler_parser()
        if SECAO_PAINEL not in parser:
            parser[SECAO_PAINEL] = {}
        parser[SECAO_PAINEL][chave_ini] = chave_ok
        self._gravar(parser)

    def salvar_monitor_janela(self, dispositivo: str) -> None:
        """Grava o monitor onde a janela principal foi exibida pela ultima vez."""
        nome = (dispositivo or "").strip().upper()
        if not nome:
            return
        parser = self._ler_parser()
        if SECAO_JANELA not in parser:
            parser[SECAO_JANELA] = {}
        parser[SECAO_JANELA][CHAVE_MONITOR_DISPOSITIVO] = nome
        self._gravar(parser)

    def carregar_alerta_valorizacao_agora(self, simbolo: str) -> float | None:
        """Valor em reais de valorizacao para alerta de venda na tela Agora."""
        chave = self._chave_alerta_valorizacao_agora(simbolo)
        if not chave:
            return None
        parser = self._ler_parser()
        if SECAO_AGORA_ALERTAS not in parser:
            return None
        texto = parser[SECAO_AGORA_ALERTAS].get(chave, "").strip()
        if not texto:
            return None
        try:
            valor = float(texto.replace(",", "."))
        except ValueError:
            return None
        return round(valor, 2) if valor > 0 else None

    def salvar_alerta_valorizacao_agora(self, simbolo: str, valor: float | None) -> None:
        """Persiste o limite de valorizacao (R$) para alerta na tela Agora."""
        chave = self._chave_alerta_valorizacao_agora(simbolo)
        if not chave:
            return
        parser = self._ler_parser()
        if SECAO_AGORA_ALERTAS not in parser:
            parser[SECAO_AGORA_ALERTAS] = {}
        if valor is None or valor <= 0:
            parser[SECAO_AGORA_ALERTAS].pop(chave, None)
        else:
            parser[SECAO_AGORA_ALERTAS][chave] = f"{round(valor, 2):.2f}"
        self._gravar(parser)

    @staticmethod
    def _chave_alerta_valorizacao_agora(simbolo: str) -> str:
        texto = (simbolo or "").strip().upper()
        if not texto:
            return ""
        return texto.replace(".", "_").replace("-", "_")

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

    def _ler_valor_simulacao(self, texto: str) -> float:
        return self._ler_valor_monetario_ini(texto, self.padrao_valor_simulacao_renda_fixa())

    def _ler_valor_monetario_ini(self, texto: str, padrao: float) -> float:
        try:
            valor = float(str(texto or "").strip().replace(",", "."))
        except ValueError:
            return padrao
        if valor <= 0:
            return padrao
        return round(valor, 2)
