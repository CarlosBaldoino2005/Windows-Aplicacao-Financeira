"""Mascaras de entrada no formato pt-BR (milhar . e decimal ,)."""
from __future__ import annotations

import customtkinter as ctk


def _agrupar_milhar_parte_inteira(digitos: str) -> str:
    """Agrupa digitos da parte inteira com ponto a cada tres casas."""
    if not digitos:
        return "0"
    grupos: list[str] = []
    restante = digitos
    while restante:
        grupos.append(restante[-3:])
        restante = restante[:-3]
    return ".".join(reversed(grupos))


def formatar_centavos_ptbr(total_centavos: int) -> str:
    """Converte centavos digitados em texto 1.234,56."""
    if total_centavos < 0:
        total_centavos = 0
    reais = total_centavos // 100
    centavos = total_centavos % 100
    inteiro = _agrupar_milhar_parte_inteira(str(reais))
    return f"{inteiro},{centavos:02d}"


def _extrair_digitos(texto: str, prefixo: str) -> str:
    """Mantem apenas numeros, ignorando prefixo e pontuacao da mascara."""
    limpo = str(texto or "")
    if prefixo and limpo.upper().startswith(prefixo.upper()):
        limpo = limpo[len(prefixo) :]
    return "".join(caractere for caractere in limpo if caractere.isdigit())


def _aplicar_texto_mascarado(entry: ctk.CTkEntry, prefixo: str, digitos: str) -> None:
    """Reescreve o campo com o valor formatado e cursor no final."""
    if not digitos:
        texto = prefixo.strip()
    else:
        texto = f"{prefixo}{formatar_centavos_ptbr(int(digitos))}"

    entry.delete(0, "end")
    entry.insert(0, texto)
    entry.icursor("end")


def aplicar_mascara_moeda_ptbr(
    entry: ctk.CTkEntry,
    prefixo: str = "R$ ",
) -> None:
    """
    Aplica mascara monetaria pt-BR enquanto o usuario digita.
    Cada tecla numerica entra da direita para a esquerda (centavos).
    Ex.: 1 -> 0,01 | 123456 -> 1.234,56
    """
    prefixo = prefixo if prefixo.endswith(" ") else f"{prefixo} "

    def ao_pressionar_tecla(evento) -> str | None:
        # Permite atalhos e navegacao.
        if evento.keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End", "Tab"):
            return None
        if evento.state & 0x4 and evento.keysym.lower() in ("a", "c", "v", "x"):
            return None
        if evento.char and evento.char.isdigit():
            return None
        if evento.keysym == "Return":
            return None
        return "break"

    def ao_soltar_tecla(_evento=None) -> None:
        digitos = _extrair_digitos(entry.get(), prefixo)
        _aplicar_texto_mascarado(entry, prefixo, digitos)

    def ao_focar(_evento=None) -> None:
        if not entry.get().strip():
            entry.insert(0, prefixo.strip())

    entry.bind("<KeyPress>", ao_pressionar_tecla, add=True)
    entry.bind("<KeyRelease>", ao_soltar_tecla, add=True)
    entry.bind("<FocusIn>", ao_focar, add=True)


def formatar_inteiro_ptbr(valor: int) -> str:
    """Formata inteiro com separador de milhar (ex.: 2000 -> 2.000)."""
    if valor < 0:
        valor = 0
    return _agrupar_milhar_parte_inteira(str(valor))


def _extrair_apenas_digitos(texto: str) -> str:
    return "".join(caractere for caractere in str(texto or "") if caractere.isdigit())


def _tecla_permitida_mascara(evento) -> str | None:
    if evento.keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End", "Tab"):
        return None
    if evento.state & 0x4 and evento.keysym.lower() in ("a", "c", "v", "x"):
        return None
    if evento.char and evento.char.isdigit():
        return None
    if evento.keysym == "Return":
        return None
    return "break"


def aplicar_mascara_inteiro_ptbr(entry: ctk.CTkEntry) -> None:
    """
    Mascara para quantidade inteira (acoes/cotas): apenas numeros com milhar.
    Ex.: 2000 -> 2.000 | 1234567 -> 1.234.567
    """

    def ao_soltar_tecla(_evento=None) -> None:
        digitos = _extrair_apenas_digitos(entry.get())
        if not digitos:
            entry.delete(0, "end")
            return
        texto = formatar_inteiro_ptbr(int(digitos))
        entry.delete(0, "end")
        entry.insert(0, texto)
        entry.icursor("end")

    entry.bind("<KeyPress>", _tecla_permitida_mascara, add=True)
    entry.bind("<KeyRelease>", ao_soltar_tecla, add=True)
