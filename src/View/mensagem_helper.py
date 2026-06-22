"""Caixas de mensagem com as cores do tema claro/escuro do aplicativo."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import customtkinter as ctk

from src.Tool.janela_helper import configurar_janela_filha_modal, liberar_modal_janela_filha, centralizar_janela_na_tela, centralizar_janela_sobre_referencia
from src.View.tema import CORES

TipoMensagem = Literal["info", "aviso", "erro", "pergunta"]
ModoDialogo = Literal["ok", "sim_nao", "abrir_fechar"]

_LARGURA_MINIMA = 440
_LARGURA_MAXIMA = 560
_ALTURA_MINIMA = 160
_ALTURA_MINIMA_COM_BOTOES = 220
_MARGEM_JANELA = 32
_MARGEM_PAINEL = 16


def _obter_estilo(tipo: TipoMensagem) -> tuple[str, str, str]:
    """Le cores atuais do tema no momento da exibicao."""
    mapa: dict[TipoMensagem, tuple[str, str, str]] = {
        "info": ("i", CORES["info"], CORES["infoFundo"]),
        "aviso": ("!", CORES["aviso"], CORES["avisoFundo"]),
        "erro": ("×", CORES["erro"], CORES["erroFundo"]),
        "pergunta": ("?", CORES["info"], CORES["infoFundo"]),
    }
    return mapa[tipo]


def _estimar_largura(titulo: str, mensagem: str) -> int:
    """Define largura do dialogo conforme o texto, sem cortar linhas curtas."""
    linhas = [titulo, *mensagem.splitlines()]
    maior_linha = max(len(linha) for linha in linhas if linha) if linhas else 0
    estimada = 120 + (maior_linha * 8)
    return max(_LARGURA_MINIMA, min(_LARGURA_MAXIMA, estimada))


def showinfo(titulo: str, mensagem: str, *, parent: ctk.CTk | ctk.CTkToplevel | None = None) -> None:
    """Exibe mensagem informativa no tema atual."""
    _exibir_dialogo(titulo, mensagem, "info", parent, modo="ok")


def showinfo_com_abrir_arquivo(
    titulo: str,
    mensagem: str,
    caminho_arquivo: str,
    *,
    parent: ctk.CTk | ctk.CTkToplevel | None = None,
    texto_abrir: str = "Abrir arquivo",
    texto_fechar: str = "Fechar",
) -> None:
    """Mensagem de sucesso com opcoes para abrir o arquivo ou fechar."""
    _exibir_dialogo(
        titulo,
        mensagem,
        "info",
        parent,
        modo="abrir_fechar",
        caminho_arquivo=caminho_arquivo,
        texto_abrir=texto_abrir,
        texto_fechar=texto_fechar,
    )


def showwarning(titulo: str, mensagem: str, *, parent: ctk.CTk | ctk.CTkToplevel | None = None) -> None:
    """Exibe mensagem de aviso no tema atual."""
    _exibir_dialogo(titulo, mensagem, "aviso", parent, modo="ok")


def showerror(titulo: str, mensagem: str, *, parent: ctk.CTk | ctk.CTkToplevel | None = None) -> None:
    """Exibe mensagem de erro no tema atual."""
    _exibir_dialogo(titulo, mensagem, "erro", parent, modo="ok")


def askyesno(titulo: str, mensagem: str, *, parent: ctk.CTk | ctk.CTkToplevel | None = None) -> bool:
    """Pergunta Sim/Nao e retorna True quando o usuario confirma."""
    return bool(_exibir_dialogo(titulo, mensagem, "pergunta", parent, modo="sim_nao"))


def _resolver_pai(pai: ctk.CTk | ctk.CTkToplevel | None) -> ctk.CTk | ctk.CTkToplevel | None:
    if pai is None:
        return None
    try:
        if pai.winfo_exists():
            return pai
    except Exception:
        pass
    return None


def _obter_pai_para_dialogo(pai: ctk.CTk | ctk.CTkToplevel | None) -> ctk.CTk | ctk.CTkToplevel | None:
    """
    Usa a filha modal mais recente como pai quando existir.
    Evita mensagem ficar atras de telas como definir limites.
    """
    pai_ref = _resolver_pai(pai)
    if pai_ref is None:
        return None

    filhas = getattr(pai_ref, "_financeiro_filhas_modais", None) or []
    for filha in reversed(filhas):
        try:
            if filha.winfo_exists():
                return filha
        except Exception:
            continue
    return pai_ref


def _exibir_dialogo(
    titulo: str,
    mensagem: str,
    tipo: TipoMensagem,
    pai: ctk.CTk | ctk.CTkToplevel | None,
    *,
    modo: ModoDialogo,
    caminho_arquivo: str | None = None,
    texto_abrir: str = "Abrir arquivo",
    texto_fechar: str = "Fechar",
) -> bool | None:
    pai_ref = _obter_pai_para_dialogo(pai)
    janela = _DialogoMensagem(
        pai_ref,
        titulo,
        mensagem,
        tipo,
        modo,
        caminho_arquivo=caminho_arquivo,
        texto_abrir=texto_abrir,
        texto_fechar=texto_fechar,
    )
    return janela.resultado


def _abrir_arquivo_no_sistema(caminho: str) -> str | None:
    """Abre o arquivo com o aplicativo padrao do Windows."""
    arquivo = Path(caminho)
    if not arquivo.is_file():
        return "Arquivo nao encontrado."
    try:
        os.startfile(str(arquivo.resolve()))
        return None
    except OSError as exc:
        return f"Nao foi possivel abrir o arquivo: {exc}"


class _DialogoMensagem(ctk.CTkToplevel):
    """Janela modal compacta alinhada ao tema global."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel | None,
        titulo: str,
        mensagem: str,
        tipo: TipoMensagem,
        modo: ModoDialogo,
        *,
        caminho_arquivo: str | None = None,
        texto_abrir: str = "Abrir arquivo",
        texto_fechar: str = "Fechar",
    ) -> None:
        super().__init__(pai)
        self.resultado: bool | None = None
        self._modo = modo
        self._caminho_arquivo = caminho_arquivo
        self._texto_abrir = texto_abrir
        self._texto_fechar = texto_fechar
        self._largura = _estimar_largura(titulo, mensagem)
        self._altura = _ALTURA_MINIMA

        self.title(titulo)
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)

        self._montar_conteudo(titulo, mensagem, tipo)
        self._aplicar_geometria(pai)
        if pai is not None:
            configurar_janela_filha_modal(self, pai)

        self.protocol("WM_DELETE_WINDOW", self._fechar_padrao)
        self.bind("<Escape>", lambda _e: self._fechar_padrao())

        try:
            self.grab_set()
        except Exception:
            pass
        try:
            if pai is not None:
                self.lift(pai)
                self.attributes("-topmost", True)
                self.update_idletasks()
                self.attributes("-topmost", False)
        except Exception:
            pass
        self.focus_force()
        self.wait_window(self)

    def _montar_conteudo(self, titulo: str, mensagem: str, tipo: TipoMensagem) -> None:
        wrap = self._largura - (_MARGEM_JANELA * 2) - (_MARGEM_PAINEL * 2)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=_MARGEM_JANELA, pady=_MARGEM_JANELA)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=0)

        painel = ctk.CTkFrame(container, fg_color=CORES["superficie"], corner_radius=12)
        painel.grid(row=0, column=0, sticky="nsew")

        cabecalho = ctk.CTkFrame(painel, fg_color="transparent")
        cabecalho.pack(fill="x", padx=_MARGEM_PAINEL, pady=(_MARGEM_PAINEL, 8))

        simbolo, cor_icone, cor_fundo_icone = _obter_estilo(tipo)
        icone = ctk.CTkFrame(
            cabecalho,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=cor_fundo_icone,
        )
        icone.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="n")
        icone.grid_propagate(False)
        ctk.CTkLabel(
            icone,
            text=simbolo,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=cor_icone,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            cabecalho,
            text=titulo,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
            justify="left",
            wraplength=max(240, wrap - 52),
        ).grid(row=0, column=1, sticky="ew")

        cabecalho.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            painel,
            text=mensagem,
            font=ctk.CTkFont(size=13),
            text_color=CORES["textoSecundario"],
            wraplength=max(280, wrap),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=_MARGEM_PAINEL, pady=(0, _MARGEM_PAINEL))

        barra = ctk.CTkFrame(container, fg_color=CORES["superficie"], corner_radius=12)
        barra.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        barra_inner = ctk.CTkFrame(barra, fg_color="transparent")
        barra_inner.pack(fill="x", padx=_MARGEM_PAINEL, pady=12)

        if self._modo == "sim_nao":
            ctk.CTkButton(
                barra_inner,
                text="Sim",
                width=100,
                command=lambda: self._fechar(True),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(side="right")
            ctk.CTkButton(
                barra_inner,
                text="Nao",
                width=100,
                command=lambda: self._fechar(False),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(side="right", padx=(0, 8))
        elif self._modo == "abrir_fechar":
            ctk.CTkButton(
                barra_inner,
                text=self._texto_fechar,
                width=110,
                height=36,
                command=lambda: self._fechar(True),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(side="right")
            ctk.CTkButton(
                barra_inner,
                text=self._texto_abrir,
                width=130,
                height=36,
                command=self._abrir_arquivo_e_manter,
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(side="right", padx=(0, 8))
        else:
            ctk.CTkButton(
                barra_inner,
                text="OK",
                width=100,
                command=lambda: self._fechar(True),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(side="right")

        self.update_idletasks()

    def _medir_altura_necessaria(self) -> int:
        """Mede altura real sem prender a janela em tamanho que corta os botoes."""
        self.update_idletasks()
        altura = int(self.winfo_reqheight())
        if altura <= _ALTURA_MINIMA:
            altura = 0
            for widget in self.winfo_children():
                self.update_idletasks()
                altura += int(widget.winfo_reqheight())
            altura += _MARGEM_JANELA * 2

        minima = _ALTURA_MINIMA
        if self._modo == "abrir_fechar":
            minima = _ALTURA_MINIMA_COM_BOTOES
        return max(minima, altura + 16)

    def _aplicar_geometria(self, pai: ctk.CTk | ctk.CTkToplevel | None) -> None:
        try:
            largura = self._largura
            self.minsize(largura, _ALTURA_MINIMA)
            self.geometry(f"{largura}x{_ALTURA_MINIMA_COM_BOTOES}")
            self.update_idletasks()
            altura = self._medir_altura_necessaria()
            self._altura = altura
            self.minsize(largura, altura)
            self.geometry(f"{largura}x{altura}")

            if pai is not None:
                centralizar_janela_sobre_referencia(self, pai, largura, altura, reagendar=False)
            else:
                centralizar_janela_na_tela(self, largura, altura)
        except Exception:
            self.geometry(f"{self._largura}x{max(self._altura, _ALTURA_MINIMA_COM_BOTOES)}")

    def _fechar_padrao(self) -> None:
        if self._modo == "sim_nao":
            self._fechar(False)
        else:
            self._fechar(True)

    def _abrir_arquivo_e_manter(self) -> None:
        if not self._caminho_arquivo:
            return
        erro = _abrir_arquivo_no_sistema(self._caminho_arquivo)
        if erro:
            showerror("Abrir arquivo", erro, parent=self)

    def _fechar(self, valor: bool) -> None:
        self.resultado = valor if self._modo == "sim_nao" else None
        liberar_modal_janela_filha(self)
        self.destroy()
