"""Opcoes de exibicao de fotos nas noticias (INI e interface)."""
from dataclasses import dataclass

# Valores aceitos em dados/painel.ini (chave fotos_noticias).
FOTOS_NENHUM = "nenhum"
FOTOS_PEQUENO = "pequeno"
FOTOS_MEDIO = "medio"
FOTOS_GRANDE = "grande"
FOTOS_PADRAO = FOTOS_MEDIO

ROTULOS_FOTOS: dict[str, str] = {
    FOTOS_NENHUM: "Nenhum",
    FOTOS_PEQUENO: "Pequeno",
    FOTOS_MEDIO: "Medio",
    FOTOS_GRANDE: "Grande",
}

# Largura e altura maxima da miniatura em cada modo.
DIMENSOES_FOTOS: dict[str, tuple[int, int]] = {
    FOTOS_NENHUM: (0, 0),
    FOTOS_PEQUENO: (120, 90),
    FOTOS_MEDIO: (170, 128),
    FOTOS_GRANDE: (240, 180),
}


@dataclass(frozen=True)
class OpcoesFotosNoticias:
    """Configuracao resolvida para desenhar ou ocultar imagens."""

    modo: str
    exibir: bool
    largura: int
    altura: int

    @classmethod
    def a_partir_modo(cls, modo: str) -> "OpcoesFotosNoticias":
        chave = modo if modo in DIMENSOES_FOTOS else FOTOS_PADRAO
        largura, altura = DIMENSOES_FOTOS[chave]
        return cls(
            modo=chave,
            exibir=chave != FOTOS_NENHUM and largura > 0,
            largura=largura,
            altura=altura,
        )
