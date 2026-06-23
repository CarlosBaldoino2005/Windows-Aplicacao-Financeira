"""Modal para editar compra registrada na carteira."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import ROTULOS_TIPO_CARTEIRA, CompraCarteira
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import (
    centralizar_janela_sobre_referencia,
    configurar_janela_filha_modal,
    liberar_modal_janela_filha,
)
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr, formatar_centavos_ptbr
from src.View.tabela_carteira_helper import _formatar_quantidade
from src.View.tema import CORES

_LARGURA = 440
_ALTURA_MINIMA = 520
_MARGEM_ALTURA_EXTRA_PX = 28


def _texto_moeda(valor: float) -> str:
    centavos = max(0, int(round(valor * 100)))
    return f"R$ {formatar_centavos_ptbr(centavos)}"


def abrir_editar_compra_carteira(
    pai: ctk.CTk | ctk.CTkToplevel,
    controlador: ControladorCarteira,
    compra: CompraCarteira,
    *,
    moeda: str = "BRL",
    na_carteira: bool = True,
    ao_salvar: Callable[[], None] | None = None,
) -> None:
    """Abre formulario para corrigir dados de uma compra ja registrada."""
    if not pai.winfo_exists():
        return

    dialogo = ctk.CTkToplevel(pai)
    dialogo.title(f"Editar compra — {codigo_exibicao(compra.simbolo)}")
    dialogo.configure(fg_color=CORES["fundo"])
    dialogo.resizable(False, False)
    dialogo.grid_columnconfigure(0, weight=1)
    dialogo.grid_rowconfigure(0, weight=1)

    painel = ctk.CTkFrame(dialogo, fg_color=CORES["superficie"], corner_radius=12)
    painel.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 8))
    painel.grid_rowconfigure(1, weight=1)
    painel.grid_columnconfigure(0, weight=1)

    cabecalho = ctk.CTkFrame(painel, fg_color="transparent")
    cabecalho.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

    ctk.CTkLabel(
        cabecalho,
        text=f"Editar compra — {codigo_exibicao(compra.simbolo)}",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=CORES["texto"],
    ).pack(anchor="w")

    situacao = "Na carteira" if na_carteira else "Fora da carteira (posicao ja vendida ou removida)"
    ctk.CTkLabel(
        cabecalho,
        text=(
            "Corrija quantidade, data e preco desta compra. "
            f"Situacao atual: {situacao}."
        ),
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
        wraplength=_LARGURA - 56,
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    ctk.CTkLabel(
        cabecalho,
        text=f"Tipo: {ROTULOS_TIPO_CARTEIRA.get(compra.tipo_ativo, compra.tipo_ativo)}",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w", pady=(6, 0))

    area_campos = ctk.CTkScrollableFrame(
        painel,
        fg_color=CORES["fundo"],
        label_text="",
        height=280,
    )
    area_campos.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _rotulo_campo(texto: str) -> None:
        ctk.CTkLabel(
            area_campos,
            text=texto,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", pady=(0, 4))

    _rotulo_campo("Quantidade comprada")
    entrada_qtd = ctk.CTkEntry(area_campos, width=240, placeholder_text="Ex.: 50")
    entrada_qtd.pack(anchor="w", pady=(0, 8))
    entrada_qtd.insert(0, _formatar_quantidade(compra.quantidade))

    _rotulo_campo("Data da compra (dd/mm/aaaa)")
    entrada_data = ctk.CTkEntry(area_campos, width=240)
    entrada_data.pack(anchor="w", pady=(0, 8))
    entrada_data.insert(0, compra.data_compra)

    modo_valor_compra = {"valor": "por_cota"}

    ctk.CTkLabel(
        area_campos,
        text="Valor da compra",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=CORES["texto"],
    ).pack(anchor="w", pady=(0, 4))

    seletor_modo = ctk.CTkSegmentedButton(
        area_campos,
        values=["Por cota", "Valor total"],
        command=lambda valor: _atualizar_modo_valor(valor),
        selected_color=CORES["primaria"],
        unselected_color=CORES["superficie"],
        text_color=CORES.get("textoInverso", "#FFFFFF"),
    )
    seletor_modo.set("Por cota")
    seletor_modo.pack(anchor="w", pady=(0, 8))

    rotulo_preco = ctk.CTkLabel(
        area_campos,
        text="Preco de compra (por cota)",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    )
    rotulo_preco.pack(anchor="w", pady=(0, 4))

    entrada_preco = ctk.CTkEntry(area_campos, width=240, placeholder_text="R$ 0,00")
    entrada_preco.pack(anchor="w", pady=(0, 8))
    entrada_preco.insert(0, _texto_moeda(compra.preco_compra))
    aplicar_mascara_moeda_ptbr(entrada_preco)

    def _atualizar_modo_valor(valor: str) -> None:
        if valor == "Valor total":
            modo_valor_compra["valor"] = "valor_total"
            rotulo_preco.configure(text="Valor total pago na negociacao")
            total = round(compra.preco_compra * compra.quantidade, 2)
            entrada_preco.delete(0, "end")
            entrada_preco.insert(0, _texto_moeda(total))
        else:
            modo_valor_compra["valor"] = "por_cota"
            rotulo_preco.configure(text="Preco de compra (por cota)")
            entrada_preco.delete(0, "end")
            entrada_preco.insert(0, _texto_moeda(compra.preco_compra))

    entrada_qtd.focus_set()

    def fechar_dialogo() -> None:
        liberar_modal_janela_filha(dialogo)
        dialogo.destroy()

    def salvar() -> None:
        ok, erro = controlador.atualizar_compra(
            compra.id,
            entrada_qtd.get(),
            entrada_preco.get(),
            entrada_data.get(),
            modo_valor_compra=modo_valor_compra["valor"],
        )
        if erro:
            messagebox.showwarning("Editar compra", erro, parent=dialogo)
            return
        if ao_salvar is not None:
            ao_salvar()
        fechar_dialogo()

    barra = ctk.CTkFrame(dialogo, fg_color=CORES["fundo"])
    barra.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
    ctk.CTkButton(
        barra,
        text="Cancelar",
        command=fechar_dialogo,
        fg_color=CORES["primaria"],
        hover_color=CORES["primariaHover"],
        text_color=CORES.get("textoInverso", "#FFFFFF"),
        width=110,
    ).pack(side="right")
    ctk.CTkButton(
        barra,
        text="Salvar",
        command=salvar,
        fg_color=CORES["primaria"],
        hover_color=CORES["primariaHover"],
        text_color=CORES.get("textoInverso", "#FFFFFF"),
        width=110,
    ).pack(side="right", padx=(0, 8))

    for entrada in (entrada_qtd, entrada_data, entrada_preco):
        entrada.bind("<Return>", lambda _e: salvar())

    def aplicar_tamanho() -> None:
        try:
            dialogo.update_idletasks()
            altura = max(_ALTURA_MINIMA, int(dialogo.winfo_reqheight()) + _MARGEM_ALTURA_EXTRA_PX)
            dialogo.minsize(_LARGURA, altura)
            dialogo.geometry(f"{_LARGURA}x{altura}")
            centralizar_janela_sobre_referencia(dialogo, pai, _LARGURA, altura)
        except Exception:
            pass

    aplicar_tamanho()
    configurar_janela_filha_modal(dialogo, pai)
    dialogo.protocol("WM_DELETE_WINDOW", fechar_dialogo)
    dialogo.after(120, aplicar_tamanho)
    dialogo.focus_force()
