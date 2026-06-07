"""Modal para editar limites de um item ja cadastrado no monitoramento."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Model.monitoramento import ROTULOS_TIPO_ATIVO, MonitoramentoItem
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_filha_modal, liberar_modal_janela_filha
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.Tool.validadores import validar_limites_monitoramento, validar_valor_monetario_opcional
from src.View import mensagem_helper as messagebox
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.janela_calcular_limites_monitoramento import abrir_calcular_limites_monitoramento
from src.View.limites_monitoramento_ui_helper import preencher_entrada_moeda, valor_para_campo_moeda
from src.View.tema import CORES

_LARGURA = 440
_ALTURA = 420


def _valor_para_campo_moeda(valor: float | None) -> str:
    return valor_para_campo_moeda(valor)


class JanelaEditarMonitoramento(ctk.CTkToplevel):
    """Altera valor baixo e valor alto de um ativo monitorado."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        controlador: ControladorMonitoramento,
        item: MonitoramentoItem,
        ao_salvar: Callable[[], None],
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._item = item
        self._ao_salvar = ao_salvar
        self._cotacao, _ = controlador.obter_cotacao_ativo(item.simbolo, item.tipo_ativo)
        self._janela_calcular = None
        self._largura = _LARGURA
        self._altura = _ALTURA

        codigo = codigo_exibicao(item.simbolo)
        self.title(f"Editar limites — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(self._largura, self._altura)

        self._montar_interface()
        self._ajustar_tamanho_conteudo(pai)
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self._entrada_valor_baixo.focus_set()

    def _centralizar_sobre_pai(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            pai.update_idletasks()
            x = int(pai.winfo_rootx() + max(0, (pai.winfo_width() - self._largura) / 2))
            y = int(pai.winfo_rooty() + max(0, (pai.winfo_height() - self._altura) / 2))
            self.geometry(f"{self._largura}x{self._altura}+{x}+{y}")
        except Exception:
            pass

    def _ajustar_tamanho_conteudo(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            altura_necessaria = int(self.winfo_reqheight())
            if altura_necessaria > self._altura:
                self._altura = altura_necessaria
            self.minsize(self._largura, self._altura)
            self._centralizar_sobre_pai(pai)
        except Exception:
            self._centralizar_sobre_pai(pai)

    def _ao_fechar(self) -> None:
        liberar_modal_janela_filha(self)
        self.destroy()

    def _montar_interface(self) -> None:
        painel = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            painel,
            text="Editar limites",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            painel,
            text="Ajuste os limites de preco. A validacao usa a cotacao atual do ativo.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=_LARGURA - 80,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self._montar_resumo_ativo(painel)
        self._montar_limites(painel)
        self._montar_botoes(painel)

    def _montar_resumo_ativo(self, painel: ctk.CTkFrame) -> None:
        codigo = codigo_exibicao(self._item.simbolo)
        tipo_rotulo = ROTULOS_TIPO_ATIVO.get(self._item.tipo_ativo, self._item.tipo_ativo)

        card = ctk.CTkFrame(
            painel,
            fg_color=CORES["fundo"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        card.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(
            card,
            text=f"{codigo}  ({tipo_rotulo})",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=12, pady=(10, 2))

        if self._cotacao is not None and self._cotacao.nome:
            nome = self._cotacao.nome
            if nome.upper() != codigo.upper():
                ctk.CTkLabel(
                    card,
                    text=nome,
                    font=ctk.CTkFont(size=12),
                    text_color=CORES["textoSecundario"],
                ).pack(anchor="w", padx=12, pady=(0, 2))

        if self._cotacao is not None and self._cotacao.preco > 0:
            preco = formatar_moeda(self._cotacao.preco, self._cotacao.moeda)
            variacao = formatar_variacao(
                self._cotacao.variacao_valor,
                self._cotacao.variacao_percentual,
                self._cotacao.moeda,
            )
            ctk.CTkLabel(
                card,
                text=f"Preco atual: {preco}  ({variacao})",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=CORES["primaria"],
            ).pack(anchor="w", padx=12, pady=(4, 10))
        else:
            ctk.CTkLabel(
                card,
                text="Preco atual indisponivel no momento.",
                font=ctk.CTkFont(size=12),
                text_color=CORES["aviso"],
            ).pack(anchor="w", padx=12, pady=(4, 10))

    def _montar_limites(self, painel: ctk.CTkFrame) -> None:
        bloco_limites = ctk.CTkFrame(painel, fg_color="transparent")
        bloco_limites.pack(fill="x", padx=16, pady=(0, 8))

        linha_titulo = ctk.CTkFrame(bloco_limites, fg_color="transparent")
        linha_titulo.pack(fill="x")
        ctk.CTkLabel(
            linha_titulo,
            text="Limites de preco",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")
        ctk.CTkButton(
            linha_titulo,
            text="Calcular",
            command=self._abrir_calcular_limites,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=90,
            height=28,
        ).pack(side="right")

        linha_limites = ctk.CTkFrame(bloco_limites, fg_color="transparent")
        linha_limites.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(linha_limites, text="Valor baixo").pack(side="left", padx=(0, 8))
        self._entrada_valor_baixo = ctk.CTkEntry(linha_limites, width=140, placeholder_text="Opcional")
        self._entrada_valor_baixo.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(linha_limites, text="Valor alto").pack(side="left", padx=(0, 8))
        self._entrada_valor_alto = ctk.CTkEntry(linha_limites, width=140, placeholder_text="Opcional")
        self._entrada_valor_alto.pack(side="left")

        if self._item.valor_baixo is not None:
            self._entrada_valor_baixo.insert(0, _valor_para_campo_moeda(self._item.valor_baixo))
        if self._item.valor_alto is not None:
            self._entrada_valor_alto.insert(0, _valor_para_campo_moeda(self._item.valor_alto))

        aplicar_mascara_moeda_ptbr(self._entrada_valor_baixo)
        aplicar_mascara_moeda_ptbr(self._entrada_valor_alto)

    def _abrir_calcular_limites(self) -> None:
        if self._cotacao is None or self._cotacao.preco <= 0:
            messagebox.showwarning(
                "Calcular limites",
                "Cotacao indisponivel para calcular os limites.",
                parent=self,
            )
            return

        if self._janela_calcular is not None:
            try:
                if self._janela_calcular.winfo_exists():
                    self._janela_calcular.focus_force()
                    self._janela_calcular.lift()
                    return
            except Exception:
                pass

        def ao_aplicar(valor_baixo: float, valor_alto: float) -> None:
            preencher_entrada_moeda(self._entrada_valor_baixo, valor_baixo)
            preencher_entrada_moeda(self._entrada_valor_alto, valor_alto)

        self._janela_calcular = abrir_calcular_limites_monitoramento(
            self,
            self._cotacao.preco,
            self._cotacao.moeda,
            ao_aplicar,
            titulo_ativo=codigo_exibicao(self._item.simbolo),
        )

    def _montar_botoes(self, painel: ctk.CTkFrame) -> None:
        barra = ctk.CTkFrame(painel, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=(12, 16))
        ctk.CTkButton(
            barra,
            text="Cancelar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        ).pack(side="right")
        ctk.CTkButton(
            barra,
            text="Salvar",
            command=self._salvar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        ).pack(side="right", padx=(0, 8))

    def _ler_valor_campo(self, entry: ctk.CTkEntry) -> tuple[float | None, str | None]:
        return validar_valor_monetario_opcional(entry.get())

    def _salvar(self) -> None:
        valor_baixo, erro_baixo = self._ler_valor_campo(self._entrada_valor_baixo)
        if erro_baixo:
            messagebox.showwarning("Valor baixo", erro_baixo, parent=self)
            return
        valor_alto, erro_alto = self._ler_valor_campo(self._entrada_valor_alto)
        if erro_alto:
            messagebox.showwarning("Valor alto", erro_alto, parent=self)
            return

        preco_atual = self._cotacao.preco if self._cotacao is not None else None
        moeda = self._cotacao.moeda if self._cotacao is not None else "BRL"
        erro_limites = validar_limites_monitoramento(
            valor_baixo,
            valor_alto,
            preco_atual,
            moeda,
        )
        if erro_limites:
            messagebox.showwarning("Limites", erro_limites, parent=self)
            return

        _, erro = self._controlador.atualizar_limites_item(
            self._item.id,
            valor_baixo,
            valor_alto,
        )
        if erro:
            messagebox.showwarning("Monitoramento", erro, parent=self)
            return

        ao_salvar = self._ao_salvar
        self._ao_fechar()
        ao_salvar()


def abrir_editar_monitoramento(
    pai: ctk.CTk | ctk.CTkToplevel,
    controlador: ControladorMonitoramento,
    item: MonitoramentoItem,
    ao_salvar: Callable[[], None],
) -> JanelaEditarMonitoramento | None:
    if not pai.winfo_exists():
        return None
    return JanelaEditarMonitoramento(pai, controlador, item, ao_salvar)
