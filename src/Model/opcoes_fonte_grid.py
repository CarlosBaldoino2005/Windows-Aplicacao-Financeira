"""Tamanho da fonte das grids (INI e interface) — pequeno, medio ou grande."""
from dataclasses import dataclass

FONTE_PEQUENO = "pequeno"
FONTE_MEDIO = "medio"
FONTE_GRANDE = "grande"
FONTE_GRID_PADRAO = FONTE_MEDIO

ROTULOS_FONTE_GRID: dict[str, str] = {
    FONTE_PEQUENO: "Pequeno",
    FONTE_MEDIO: "Medio",
    FONTE_GRANDE: "Grande",
}

_MODOS_VALIDOS = (FONTE_PEQUENO, FONTE_MEDIO, FONTE_GRANDE)


@dataclass(frozen=True)
class OpcoesFonteGrid:
    """Metricas de fonte e layout para Treeview e tabelas zebradas."""

    modo: str
    fonte_tree: int
    fonte_cabecalho_tree: int
    altura_linha: int
    larguras_colunas: tuple[int, int, int, int]
    fonte_celula: int
    fonte_cabecalho_ctk: int
    fonte_titulo_card: int
    fonte_mensagem_vazio: int
    largura_wrap: int
    padding_celula_y: int

    @classmethod
    def a_partir_modo(cls, modo: str) -> "OpcoesFonteGrid":
        chave = modo if modo in _MODOS_VALIDOS else FONTE_GRID_PADRAO
        return _POR_MODO[chave]


_POR_MODO: dict[str, OpcoesFonteGrid] = {
    FONTE_PEQUENO: OpcoesFonteGrid(
        modo=FONTE_PEQUENO,
        fonte_tree=10,
        fonte_cabecalho_tree=10,
        altura_linha=28,
        larguras_colunas=(85, 200, 110, 170),
        fonte_celula=11,
        fonte_cabecalho_ctk=11,
        fonte_titulo_card=15,
        fonte_mensagem_vazio=12,
        largura_wrap=150,
        padding_celula_y=5,
    ),
    FONTE_MEDIO: OpcoesFonteGrid(
        modo=FONTE_MEDIO,
        fonte_tree=12,
        fonte_cabecalho_tree=11,
        altura_linha=34,
        larguras_colunas=(95, 240, 130, 200),
        fonte_celula=13,
        fonte_cabecalho_ctk=12,
        fonte_titulo_card=17,
        fonte_mensagem_vazio=14,
        largura_wrap=180,
        padding_celula_y=6,
    ),
    FONTE_GRANDE: OpcoesFonteGrid(
        modo=FONTE_GRANDE,
        fonte_tree=14,
        fonte_cabecalho_tree=13,
        altura_linha=42,
        larguras_colunas=(110, 280, 150, 230),
        fonte_celula=15,
        fonte_cabecalho_ctk=14,
        fonte_titulo_card=19,
        fonte_mensagem_vazio=15,
        largura_wrap=220,
        padding_celula_y=8,
    ),
}
