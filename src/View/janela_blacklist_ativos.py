"""Janela para gerenciar a Black List de ativos."""
from __future__ import annotations

import customtkinter as ctk

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import ResultadoBuscaCarteira
from src.Service.blacklist_ativos_servico import BlacklistAtivosServico
from src.Tool.blacklist_ativos_helper import (
    rotulo_resultado_busca_blacklist,
    validar_ativo_existe_blacklist,
)
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import (
    configurar_janela_filha_modal,
    centralizar_janela_sobre_referencia,
    executar_em_thread,
    liberar_modal_janela_filha,
)
from src.View import mensagem_helper as messagebox
from src.View.tema import CORES

_LARGURA = 520
_ALTURA = 600


class JanelaBlacklistAtivos(ctk.CTkToplevel):
    """Lista ativos bloqueados com aviso ao tentar cadastrar."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        *,
        simbolo_sugerido: str | None = None,
    ) -> None:
        super().__init__(pai)
        self._janela_pai = pai
        self._servico = BlacklistAtivosServico()
        self._controlador = ControladorCarteira()
        self._simbolo_sugerido = simbolo_sugerido
        self._simbolo_selecionado: str | None = None
        self._frame_lista: ctk.CTkScrollableFrame | None = None
        self._frame_resultados: ctk.CTkScrollableFrame | None = None
        self._label_selecionado: ctk.CTkLabel | None = None

        self.title("Black List de ativos")
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(_LARGURA, _ALTURA)

        self._montar_interface()
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self._atualizar_lista()
        self._centralizar_sobre_pai(pai)

    def _centralizar_sobre_pai(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            largura = max(_LARGURA, int(self.winfo_reqwidth()))
            altura = max(_ALTURA, int(self.winfo_reqheight()))
            centralizar_janela_sobre_referencia(self, pai, largura, altura)
        except Exception:
            pass

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Black List de ativos",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Ativos nesta lista geram aviso ao cadastrar compra, nova compra "
                "ou monitoramento. Voce ainda pode continuar se desejar."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=470,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=16, pady=12)

        bloco_busca = ctk.CTkFrame(corpo, fg_color="transparent")
        bloco_busca.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            bloco_busca,
            text="Buscar ativo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        linha_busca = ctk.CTkFrame(bloco_busca, fg_color="transparent")
        linha_busca.pack(fill="x", pady=(6, 0))

        self._entrada_busca = ctk.CTkEntry(
            linha_busca,
            width=280,
            placeholder_text="Codigo ou nome (ex.: PETR4)",
        )
        self._entrada_busca.pack(side="left", padx=(0, 8))
        self._entrada_busca.bind("<Return>", lambda _e: self._pesquisar())

        ctk.CTkButton(
            linha_busca,
            text="Buscar",
            command=self._pesquisar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="left")

        ctk.CTkButton(
            bloco_busca,
            text="Adicionar à Black List",
            command=self._adicionar_selecionado,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        ).pack(anchor="w", pady=(8, 0))

        self._frame_resultados = ctk.CTkScrollableFrame(
            corpo,
            height=100,
            fg_color=CORES["fundo"],
            label_text="Resultados da busca",
        )
        self._frame_resultados.pack(fill="x", pady=(0, 8))

        self._label_selecionado = ctk.CTkLabel(
            corpo,
            text="Busque o ativo, selecione na lista e clique em Adicionar à Black List.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=470,
            justify="left",
        )
        self._label_selecionado.pack(anchor="w", pady=(0, 8))

        if self._simbolo_sugerido:
            codigo = codigo_exibicao(self._simbolo_sugerido)
            ctk.CTkButton(
                corpo,
                text=f"Adicionar ativo atual ({codigo}) à Black List",
                command=lambda: self._adicionar_simbolo_validado(self._simbolo_sugerido or ""),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(anchor="w", pady=(0, 8))

        self._frame_lista = ctk.CTkScrollableFrame(
            corpo,
            height=150,
            fg_color=CORES["fundo"],
            label_text="Ativos na Black List",
        )
        self._frame_lista.pack(fill="both", expand=True, pady=(0, 8))

        barra_fechar = ctk.CTkFrame(corpo, fg_color="transparent")
        barra_fechar.pack(fill="x")
        ctk.CTkButton(
            barra_fechar,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right")

    def _limpar_resultados_busca(self) -> None:
        if self._frame_resultados is None:
            return
        for filho in self._frame_resultados.winfo_children():
            filho.destroy()

    def _pesquisar(self) -> None:
        termo = self._entrada_busca.get().strip()
        if not termo:
            messagebox.showwarning("Black List", "Digite o codigo ou nome do ativo.", parent=self)
            return

        if self._label_selecionado is not None:
            self._label_selecionado.configure(
                text="Buscando...",
                text_color=CORES["textoSecundario"],
            )
        self._limpar_resultados_busca()

        def tarefa():
            return self._controlador.pesquisar_ativos_automatico(termo)

        def ao_concluir(resultado, erro):
            if erro:
                if self._label_selecionado is not None:
                    self._label_selecionado.configure(text=erro, text_color=CORES["erro"])
                return
            if not resultado:
                self._exibir_resultados([])
                return
            resultados, msg = resultado
            if msg and not resultados:
                if self._label_selecionado is not None:
                    self._label_selecionado.configure(text=msg, text_color=CORES["aviso"])
                return
            self._exibir_resultados(resultados or [])

        executar_em_thread(self, tarefa, ao_concluir)

    def _exibir_resultados(self, resultados: list[ResultadoBuscaCarteira]) -> None:
        self._limpar_resultados_busca()
        if self._frame_resultados is None or self._label_selecionado is None:
            return

        if not resultados:
            self._label_selecionado.configure(
                text="Nenhum ativo encontrado. Verifique o codigo ou o nome.",
                text_color=CORES["aviso"],
            )
            return

        unico = len(resultados) == 1
        item_unico = resultados[0] if unico else None

        for item in resultados[:12]:
            rotulo = rotulo_resultado_busca_blacklist(item)
            destacado = unico and item_unico is not None and item.simbolo == item_unico.simbolo
            ctk.CTkButton(
                self._frame_resultados,
                text=rotulo,
                anchor="w",
                fg_color=CORES["primaria"] if destacado else CORES["fundo"],
                hover_color=CORES["primariaHover"] if destacado else CORES["zebraEscura"],
                text_color=CORES.get("textoInverso", "#FFFFFF")
                if destacado
                else CORES["texto"],
                command=lambda s=item.simbolo: self._selecionar_ativo(s),
            ).pack(fill="x", pady=2)

        if unico and item_unico is not None:
            self._selecionar_ativo(item_unico.simbolo)
        else:
            self._label_selecionado.configure(
                text=f"{len(resultados)} resultado(s). Clique para selecionar.",
                text_color=CORES["textoSecundario"],
            )

    def _selecionar_ativo(self, simbolo: str) -> None:
        self._simbolo_selecionado = simbolo
        if self._label_selecionado is not None:
            self._label_selecionado.configure(
                text=f"Selecionado: {codigo_exibicao(simbolo)}",
                text_color=CORES["sucesso"],
            )

    def _limpar_lista_visual(self) -> None:
        if self._frame_lista is None:
            return
        for filho in self._frame_lista.winfo_children():
            filho.destroy()

    def _atualizar_lista(self) -> None:
        self._limpar_lista_visual()
        if self._frame_lista is None:
            return

        simbolos = self._servico.listar()
        if not simbolos:
            ctk.CTkLabel(
                self._frame_lista,
                text="Nenhum ativo na Black List.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for simbolo in simbolos:
            linha = ctk.CTkFrame(
                self._frame_lista,
                fg_color=CORES["superficie"],
                corner_radius=8,
            )
            linha.pack(fill="x", padx=4, pady=3)

            ctk.CTkLabel(
                linha,
                text=codigo_exibicao(simbolo),
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=CORES["texto"],
            ).pack(side="left", fill="x", expand=True, padx=10, pady=8)

            ctk.CTkButton(
                linha,
                text="Remover",
                width=90,
                command=lambda s=simbolo: self._remover_simbolo(s),
                fg_color=CORES["erro"],
                hover_color=CORES.get("erroHover", "#B91C1C"),
                text_color=CORES.get("textoInverso", "#FFFFFF"),
            ).pack(side="right", padx=8, pady=4)

    def _adicionar_selecionado(self) -> None:
        if self._simbolo_selecionado:
            self._adicionar_simbolo_validado(self._simbolo_selecionado)
            return

        termo = self._entrada_busca.get().strip()
        if not termo:
            messagebox.showwarning(
                "Black List",
                "Busque o ativo e selecione um resultado antes de adicionar.",
                parent=self,
            )
            return

        if self._label_selecionado is not None:
            self._label_selecionado.configure(
                text="Validando ativo...",
                text_color=CORES["textoSecundario"],
            )

        def tarefa():
            return validar_ativo_existe_blacklist(termo, controlador=self._controlador)

        def ao_concluir(resultado, erro):
            if erro:
                if self._label_selecionado is not None:
                    self._label_selecionado.configure(text=erro, text_color=CORES["erro"])
                messagebox.showwarning("Black List", erro, parent=self)
                return
            simbolo, msg_erro = resultado
            if msg_erro or not simbolo:
                texto = msg_erro or "Ativo nao encontrado."
                if self._label_selecionado is not None:
                    self._label_selecionado.configure(text=texto, text_color=CORES["erro"])
                messagebox.showwarning("Black List", texto, parent=self)
                return
            self._adicionar_simbolo_validado(simbolo)

        executar_em_thread(self, tarefa, ao_concluir)

    def _adicionar_simbolo_validado(self, simbolo: str) -> None:
        ok, erro = self._servico.adicionar(simbolo)
        if not ok:
            messagebox.showwarning("Black List", erro or "Nao foi possivel adicionar.", parent=self)
            return
        self._simbolo_selecionado = None
        self._entrada_busca.delete(0, "end")
        self._limpar_resultados_busca()
        if self._label_selecionado is not None:
            self._label_selecionado.configure(
                text="Ativo adicionado. Busque outro ou feche a janela.",
                text_color=CORES["sucesso"],
            )
        self._atualizar_lista()
        self._centralizar_sobre_pai(self._janela_pai)

    def _remover_simbolo(self, simbolo: str) -> None:
        ok, erro = self._servico.remover(simbolo)
        if not ok:
            messagebox.showwarning("Black List", erro or "Nao foi possivel remover.", parent=self)
            return
        self._atualizar_lista()

    def _ao_fechar(self) -> None:
        liberar_modal_janela_filha(self)
        self.destroy()


def abrir_blacklist_ativos(
    pai: ctk.CTk | ctk.CTkToplevel,
    *,
    simbolo_sugerido: str | None = None,
) -> JanelaBlacklistAtivos | None:
    """Abre a janela de gerenciamento da Black List."""
    if not pai.winfo_exists():
        return None
    return JanelaBlacklistAtivos(pai, simbolo_sugerido=simbolo_sugerido)
