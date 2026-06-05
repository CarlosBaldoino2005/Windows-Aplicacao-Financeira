"""Coordena a interface com o servico de mercado (camada Controller)."""
from datetime import datetime

from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Service.detalhes_acao_servico import DetalhesAcaoServico
from src.Service.favoritos_servico import FavoritosServico
from src.Service.mercado_servico import MercadoServico
from src.Service.painel_periodo_servico import PainelPeriodoServico
from src.Service.noticias_mercado_servico import NoticiasMercadoServico
from src.Service.traducao_noticias_servico import TraducaoNoticiasServico
from src.Model.acoes_universo import QUANTIDADE_PADRAO_PAINEL
from src.Model.desvalorizacao import AnaliseDesvalorizacao
from src.Tool.desvalorizacao_helper import analisar_desvalorizacoes_periodo
from src.Tool.validadores import normalizar_simbolo, validar_data_ptbr, validar_lista_simbolos


class ControladorMercado:
    """Metodos usados pela interface desktop."""

    def __init__(self) -> None:
        self._servico = MercadoServico()
        self._busca = BuscaAcoesServico()
        self._favoritos = FavoritosServico()
        self._detalhes = DetalhesAcaoServico()
        self._noticias = NoticiasMercadoServico()
        self._traducao_noticias = TraducaoNoticiasServico()
        self._painel_periodo = PainelPeriodoServico(self._servico)

    def pesquisar_acoes(self, termo: str) -> tuple[list, str | None]:
        return self._busca.buscar(termo)

    def obter_noticias_mercado(self) -> tuple[list, str | None]:
        """Lista principais noticias de mercado (Brasil e EUA)."""
        return self._noticias.listar_principais()

    def pesquisar_noticias(self, termo: str) -> tuple[list, str | None]:
        """Busca noticias por acao, empresa ou palavra-chave."""
        return self._noticias.pesquisar(termo)

    def traduzir_noticias_para_portugues(
        self, noticias: list
    ) -> tuple[dict[str, tuple[str, str]], str | None]:
        """Traduz titulo e resumo das noticias para exibicao em portugues."""
        return self._traducao_noticias.traduzir_lote(noticias)

    def obter_painel(self, quantidade: int = QUANTIDADE_PADRAO_PAINEL) -> dict:
        return {
            "em_alta": self._servico.listar_em_alta(quantidade),
            "em_queda": self._servico.listar_em_queda(quantidade),
            "todas": self._servico.listar_todas_monitoradas(quantidade),
            "quantidade": quantidade,
        }

    def obter_painel_periodo(
        self,
        quantidade: int,
        periodo: str,
        data_inicio_texto: str | None = None,
        data_fim_texto: str | None = None,
    ) -> tuple[dict | None, str | None]:
        """Painel alta/queda/todas com variacao no periodo (nao apenas no dia)."""
        dt_inicio = None
        dt_fim = None
        if periodo == "personalizado":
            dt_inicio, err_i = validar_data_ptbr(data_inicio_texto or "")
            if err_i:
                return None, err_i
            dt_fim, err_f = validar_data_ptbr(data_fim_texto or "")
            if err_f:
                return None, err_f

        dados = self._painel_periodo.obter_painel(
            quantidade, periodo, dt_inicio, dt_fim
        )
        if dados["total_com_dados"] == 0:
            return None, (
                f"Nenhuma acao com historico no periodo "
                f"({dados['periodo_rotulo']}). Tente outro intervalo."
            )
        return dados, None

    def listar_simbolos_favoritos(self) -> list[str]:
        return self._favoritos.listar()

    def adicionar_favorito(self, simbolo: str) -> tuple[bool, str | None]:
        return self._favoritos.adicionar(simbolo)

    def remover_favorito(self, simbolo: str) -> tuple[bool, str | None]:
        return self._favoritos.remover(simbolo)

    def obter_cotacoes_favoritas(self) -> tuple[list, str | None]:
        simbolos = self._favoritos.listar()
        if not simbolos:
            return [], None
        resumos = self._servico.buscar_resumos(simbolos)
        return resumos, None

    def obter_cotacao(self, simbolo: str) -> tuple[object | None, str | None]:
        """Busca cotacao atual de uma acao especifica pelo codigo ou nome."""
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return None, erro

        resumos = self._servico.buscar_resumos([simbolo_ok])
        if not resumos:
            return None, "Cotacao indisponivel. Verifique o codigo e tente novamente."

        return resumos[0], None

    def obter_detalhes_acao(self, simbolo: str):
        """Carrega perfil, demonstrativos e concorrentes da acao."""
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return None, erro
        return self._detalhes.obter_detalhes(simbolo_ok)

    def obter_historico(
        self,
        simbolo: str,
        periodo: str,
        data_inicio_texto: str | None = None,
        data_fim_texto: str | None = None,
    ) -> tuple[object | None, str | None]:
        simbolo_ok, erro = normalizar_simbolo(simbolo)
        if erro:
            return None, erro

        dt_inicio = None
        dt_fim = None
        if periodo == "personalizado":
            dt_inicio, err_i = validar_data_ptbr(data_inicio_texto or "")
            if err_i:
                return None, err_i
            dt_fim, err_f = validar_data_ptbr(data_fim_texto or "")
            if err_f:
                return None, err_f

        serie = self._servico.buscar_historico(simbolo_ok, periodo, dt_inicio, dt_fim)
        if not serie:
            return None, "Historico indisponivel para este periodo."
        return serie, None

    def obter_desvalorizacoes_periodo(
        self,
        simbolo: str,
        periodo: str,
        data_inicio_texto: str | None = None,
        data_fim_texto: str | None = None,
    ) -> tuple[AnaliseDesvalorizacao | None, str | None]:
        """Identifica quedas de preco (pico → fundo) no historico do periodo."""
        serie, erro = self.obter_historico(
            simbolo, periodo, data_inicio_texto, data_fim_texto
        )
        if erro or serie is None:
            return None, erro or "Historico indisponivel para este periodo."

        moeda = "BRL" if serie.simbolo.endswith(".SA") else "USD"
        analise = analisar_desvalorizacoes_periodo(
            serie.pontos,
            serie.simbolo,
            serie.periodo,
            moeda,
        )
        if analise.ultima is None:
            return None, (
                f"Nenhuma desvalorizacao identificada no periodo ({analise.periodo_rotulo}). "
                "O preco pode ter subido ou permanecido estavel."
            )
        return analise, None

    def comparar(
        self,
        simbolos: list[str],
        periodo: str,
        data_inicio_texto: str | None = None,
        data_fim_texto: str | None = None,
    ) -> tuple[dict | None, str | None]:
        normalizados, erro = validar_lista_simbolos(simbolos)
        if erro:
            return None, erro

        dt_inicio = None
        dt_fim = None
        if periodo == "personalizado":
            dt_inicio, err_i = validar_data_ptbr(data_inicio_texto or "")
            if err_i:
                return None, err_i
            dt_fim, err_f = validar_data_ptbr(data_fim_texto or "")
            if err_f:
                return None, err_f

        resultado = self._servico.comparar_acoes(normalizados, periodo, dt_inicio, dt_fim)
        if len(resultado["simbolos"]) < 2:
            avisos = resultado.get("avisos") or []
            if avisos:
                return None, avisos[0]
            return None, "Dados insuficientes para comparar as acoes."
        return resultado, None
