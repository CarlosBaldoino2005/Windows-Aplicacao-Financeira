"""Normaliza CTkButton em src/View para o padrao azul unico."""
from __future__ import annotations

import re
from pathlib import Path

VIEW = Path(__file__).resolve().parents[1] / "src" / "View"

ESTILO_AZUL = """fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),"""

# Secundario com borda (multiline com varias indentacoes)
SECUNDARIO_RE = re.compile(
    r'fg_color=CORES\["superficie"\],\s*\n\s*hover_color=CORES\["zebraEscura"\],\s*\n'
    r'(?:\s*border_width=1,\s*\n\s*border_color=CORES\["borda"\],\s*\n)?'
    r'\s*text_color=CORES\["texto"\],',
    re.MULTILINE,
)

# Primario sem text_color
PRIMARIO_SEM_TEXTO_RE = re.compile(
    r'(fg_color=CORES\["primaria"\],\s*\n\s*hover_color=CORES\["primariaHover"\],)'
    r'(?!\s*\n\s*text_color=)',
    re.MULTILINE,
)

BORDA_BOTAO_RE = re.compile(
    r'fg_color=CORES\["borda"\],\s*\n\s*hover_color=CORES\["zebraEscura"\],',
    re.MULTILINE,
)

TRANSP_ENGRENAGEM_RE = re.compile(
    r'fg_color="transparent",\s*\n\s*hover_color=CORES\["primariaHover"\],\s*\n\s*text_color=CORES\["texto"\],',
    re.MULTILINE,
)


def normalizar_conteudo(texto: str) -> str:
    texto = SECUNDARIO_RE.sub(ESTILO_AZUL, texto)
    texto = PRIMARIO_SEM_TEXTO_RE.sub(
        r'\1\n            text_color=CORES.get("textoInverso", "#FFFFFF"),',
        texto,
    )
    texto = BORDA_BOTAO_RE.sub(
        'fg_color=CORES["primaria"],\n            hover_color=CORES["primariaHover"],\n            text_color=CORES.get("textoInverso", "#FFFFFF"),',
        texto,
    )
    texto = TRANSP_ENGRENAGEM_RE.sub(ESTILO_AZUL, texto)
    return texto


def main() -> None:
    alterados: list[str] = []
    for caminho in sorted(VIEW.rglob("*.py")):
        if caminho.name == "botao_helper.py":
            continue
        original = caminho.read_text(encoding="utf-8")
        novo = normalizar_conteudo(original)
        if novo != original:
            caminho.write_text(novo, encoding="utf-8")
            alterados.append(str(caminho.relative_to(VIEW.parent)))
    print(f"Arquivos alterados: {len(alterados)}")
    for item in alterados:
        print(f"  - {item}")


if __name__ == "__main__":
    main()
