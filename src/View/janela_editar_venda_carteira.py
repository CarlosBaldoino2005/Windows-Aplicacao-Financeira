"""Modal para editar venda registrada na carteira."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import ROTULOS_TIPO_CARTEIRA, VendaCarteira
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
_ALTURA_MINIMA = 700
_MARGEM_ALTURA_EXTRA_PX = 28


def _texto_moeda(valor: float) -> str:
    centavos = max(0, int(round(valor * 100)))
    return f"R$ {formatar_centavos_ptbr(centavos)}"


def abrir_editar_venda_carteira(
    pai: ctk.CTk | ctk.CTkToplevel,
    controlador: ControladorCarteira,
    venda: VendaCarteira,
    *,
    moeda: str = "BRL",
    ao_salvar: Callable[[], None] | None = None,
) -> None:
    """Abre formulario para corrigir dados de uma venda ja registrada."""
    if not pai.winfo_exists():
        return

    dialogo = ctk.CTkToplevel(pai)
    dialogo.title(f"Editar venda — {codigo_exibicao(venda.simbolo)}")
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
        text=f"Editar venda — {codigo_exibicao(venda.simbolo)}",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=CORES["texto"],
    ).pack(anchor="w")

    ctk.CTkLabel(
        cabecalho,
        text=(
            "Corrija compra, venda, quantidade e dividendos desta operacao. "
            "As alteracoes afetam apenas o historico da venda."
        ),
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
        wraplength=_LARGURA - 56,
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    ctk.CTkLabel(
        cabecalho,
        text=f"Tipo: {ROTULOS_TIPO_CARTEIRA.get(venda.tipo_ativo, venda.tipo_ativo)}",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    ).pack(anchor="w", pady=(6, 0))

    area_campos = ctk.CTkScrollableFrame(
        painel,
        fg_color=CORES["fundo"],
        label_text="",
        height=380,
    )
    area_campos.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _rotulo_campo(texto: str) -> None:
        ctk.CTkLabel(
            area_campos,
            text=texto,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", pady=(0, 4))

    def _secao(titulo: str) -> None:
        ctk.CTkLabel(
            area_campos,
            text=titulo,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["primaria"],
        ).pack(anchor="w", pady=(12, 6))

    _secao("Operacao")
    qtd_inteira = venda.tipo_ativo != "cripto"
    _rotulo_campo(
        "Quantidade vendida" + (" (apenas inteiros)" if qtd_inteira else "")
    )
    entrada_qtd = ctk.CTkEntry(
        area_campos,
        width=240,
        placeholder_text="Ex.: 0,5" if not qtd_inteira else "Ex.: 50",
    )
    entrada_qtd.pack(anchor="w", pady=(0, 8))
    entrada_qtd.insert(0, _formatar_quantidade(venda.quantidade))

    _secao("Compra")
    _rotulo_campo("Data da compra (dd/mm/aaaa)")
    entrada_data_compra = ctk.CTkEntry(area_campos, width=240)
    entrada_data_compra.pack(anchor="w", pady=(0, 8))
    entrada_data_compra.insert(0, venda.data_compra)

    _rotulo_campo("Preco de compra (por cota)")
    entrada_preco_compra = ctk.CTkEntry(area_campos, width=240, placeholder_text="R$ 0,00")
    entrada_preco_compra.pack(anchor="w", pady=(0, 8))
    entrada_preco_compra.insert(0, _texto_moeda(venda.preco_compra))
    aplicar_mascara_moeda_ptbr(entrada_preco_compra)

    _secao("Venda")
    _rotulo_campo("Data da venda (dd/mm/aaaa)")
    entrada_data_venda = ctk.CTkEntry(area_campos, width=240)
    entrada_data_venda.pack(anchor="w", pady=(0, 8))
    entrada_data_venda.insert(0, venda.data_venda)

    modo_valor_venda = {"valor": "por_cota"}

    ctk.CTkLabel(
        area_campos,
        text="Valor da venda",
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

    rotulo_preco_venda = ctk.CTkLabel(
        area_campos,
        text="Preco de venda (por cota)",
        font=ctk.CTkFont(size=12),
        text_color=CORES["textoSecundario"],
    )
    rotulo_preco_venda.pack(anchor="w", pady=(0, 4))

    entrada_preco_venda = ctk.CTkEntry(area_campos, width=240, placeholder_text="R$ 0,00")
    entrada_preco_venda.pack(anchor="w", pady=(0, 8))
    entrada_preco_venda.insert(0, _texto_moeda(venda.preco_venda))
    aplicar_mascara_moeda_ptbr(entrada_preco_venda)

    def _atualizar_modo_valor(valor: str) -> None:
        if valor == "Valor total":
            modo_valor_venda["valor"] = "valor_total"
            rotulo_preco_venda.configure(text="Valor total recebido na negociacao")
            total = round(venda.preco_venda * venda.quantidade, 2)
            entrada_preco_venda.delete(0, "end")
            entrada_preco_venda.insert(0, _texto_moeda(total))
        else:
            modo_valor_venda["valor"] = "por_cota"
            rotulo_preco_venda.configure(text="Preco de venda (por cota)")
            entrada_preco_venda.delete(0, "end")
            entrada_preco_venda.insert(0, _texto_moeda(venda.preco_venda))

    _secao("Resultado")
    _rotulo_campo("Dividendos recebidos no periodo")
    entrada_dividendos = ctk.CTkEntry(area_campos, width=240, placeholder_text="R$ 0,00")
    entrada_dividendos.pack(anchor="w", pady=(0, 8))
    if venda.dividendos_recebidos > 0:
        entrada_dividendos.insert(0, _texto_moeda(venda.dividendos_recebidos))
    aplicar_mascara_moeda_ptbr(entrada_dividendos)

    entrada_qtd.focus_set()

    def fechar_dialogo() -> None:
        liberar_modal_janela_filha(dialogo)
        dialogo.destroy()

    def salvar() -> None:
        ok, erro = controlador.atualizar_venda(
            venda.id,
            entrada_qtd.get(),
            entrada_preco_compra.get(),
            entrada_data_compra.get(),
            entrada_preco_venda.get(),
            entrada_data_venda.get(),
            entrada_dividendos.get(),
            modo_valor_venda=modo_valor_venda["valor"],
        )
        if erro:
            messagebox.showwarning("Editar venda", erro, parent=dialogo)
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

    for entrada in (
        entrada_qtd,
        entrada_data_compra,
        entrada_preco_compra,
        entrada_data_venda,
        entrada_preco_venda,
        entrada_dividendos,
    ):
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
    dialogo.after(280, aplicar_tamanho)
    dialogo.focus_force()
