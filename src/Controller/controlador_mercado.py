"""Coordena a interface com o servico de mercado (camada Controller)."""
from datetime import datetime

from src.Service.busca_acoes_servico import BuscaAcoesServico
from src.Service.detalhes_acao_servico import DetalhesAcaoServico
from src.Service.favoritos_servico import FavoritosServico
from src.Service.mercado_servico import MercadoServico
from src.Model.acoes_universo import QUANTIDADE_PADRAO_PAINEL
from src.Tool.validadores import normalizar_simbolo, validar_data_ptbr, validar_lista_simbolos


class ControladorMercado:
    """Metodos usados pela interface desktop."""

    def __init__(self) -> None:
        self._servico = MercadoServico()
        self._busca = BuscaAcoesServico()
        self._favoritos = FavoritosServico()
        self._detalhes = DetalhesAcaoServico()

    def pesquisar_acoes(self, termo: str) -> tuple[list, str | None]:
        return self._busca.buscar(termo)

    def obter_painel(self, quantidade: int = QUANTIDADE_PADRAO_PAINEL) -> dict:
        return {
            "em_alta": self._servico.listar_em_alta(quantidade),
            "em_queda": self._servico.listar_em_queda(quantidade),
            "todas": self._servico.listar_todas_monitoradas(quantidade),
            "quantidade": quantidade,
        }

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
            return None, "Dados insuficientes para comparar as acoes."
        return resultado, None
