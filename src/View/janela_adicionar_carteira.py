"""Modal para registrar ou editar compra na carteira."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import ROTULOS_TIPO_CARTEIRA, TIPOS_ATIVO_CARTEIRA, PosicaoCarteira, TipoAtivoCarteira
from src.Model.resultado_busca import ResultadoBusca
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_filha_modal, executar_em_thread, liberar_modal_janela_filha
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto
from src.View.tema import CORES

_LARGURA = 520
_ALTURA = 560


class JanelaAdicionarCarteira(ctk.CTkToplevel):
    """Formulario de compra na carteira."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        controlador: ControladorCarteira,
        ao_salvar: Callable[[], None],
        *,
        posicao: PosicaoCarteira | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._ao_salvar = ao_salvar
        self._posicao = posicao
        self._editando = posicao is not None
        self._simbolo_selecionado: str | None = posicao.simbolo if posicao else None
        self._tipo_selecionado: TipoAtivoCarteira = posicao.tipo_ativo if posicao else "acoes"

        self.title("Editar posicao" if self._editando else "Registrar compra")
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(_LARGURA, _ALTURA)

        self._montar_interface()
        self._aplicar_preenchimento_inicial()
        self._ajustar_tamanho_conteudo(pai)
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _centralizar_sobre_pai(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            pai.update_idletasks()
            x = int(pai.winfo_rootx() + max(0, (pai.winfo_width() - _LARGURA) / 2))
            y = int(pai.winfo_rooty() + max(0, (pai.winfo_height() - _ALTURA) / 2))
            self.geometry(f"{_LARGURA}x{_ALTURA}+{x}+{y}")
        except Exception:
            pass

    def _ajustar_tamanho_conteudo(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            altura_necessaria = int(self.winfo_reqheight())
            altura = max(_ALTURA, altura_necessaria)
            self.minsize(_LARGURA, altura)
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
            text="Editar posicao" if self._editando else "Registrar compra",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            painel,
            text=(
                "Ao salvar, o ativo entra no monitoramento com limites de ±"
                f"{self._controlador.carregar_variacao_monitoramento_pct():.0f}% "
                "sobre o preco de compra."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=_LARGURA - 80,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        bloco_tipo = ctk.CTkFrame(painel, fg_color="transparent")
        bloco_tipo.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(
            bloco_tipo,
            text="Tipo de ativo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")
        self._combo_tipo = ctk.CTkComboBox(
            bloco_tipo,
            values=[ROTULOS_TIPO_CARTEIRA[t] for t in TIPOS_ATIVO_CARTEIRA],
            width=220,
            command=lambda _v: self._limpar_selecao(),
        )
        self._combo_tipo.set(ROTULOS_TIPO_CARTEIRA["acoes"])
        self._combo_tipo.pack(anchor="w", pady=(6, 0))

        if not self._editando:
            self._montar_busca_ativo(painel)
        else:
            self._label_ativo_fixo = ctk.CTkLabel(
                painel,
                text="",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=CORES["texto"],
            )
            self._label_ativo_fixo.pack(anchor="w", padx=16, pady=(0, 10))

        self._montar_campos_compra(painel)
        self._montar_botoes(painel)

    def _montar_busca_ativo(self, painel: ctk.CTkFrame) -> None:
        bloco_busca = ctk.CTkFrame(painel, fg_color="transparent")
        bloco_busca.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(
            bloco_busca,
            text="Codigo ou nome",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        linha_busca = ctk.CTkFrame(bloco_busca, fg_color="transparent")
        linha_busca.pack(fill="x", pady=(6, 0))
        self._entrada_busca = ctk.CTkEntry(linha_busca, width=280, placeholder_text="Ex.: PETR4, BTC, HGLG11")
        self._entrada_busca.pack(side="left", padx=(0, 8))
        self._entrada_busca.bind("<Return>", lambda _e: self._pesquisar())
        self._entrada_codigo = ctk.CTkEntry(
            linha_busca,
            width=100,
            placeholder_text="Opcional",
        )
        self._entrada_codigo.pack(side="left", padx=(0, 8))
        self._entrada_codigo.bind("<Return>", lambda _e: self._confirmar_busca_ou_codigo())
        ctk.CTkButton(
            linha_busca,
            text="Buscar",
            command=self._pesquisar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=90,
        ).pack(side="left")

        self._frame_resultados = ctk.CTkScrollableFrame(
            painel,
            height=100,
            fg_color=CORES["fundo"],
            label_text="Resultados",
        )
        self._frame_resultados.pack(fill="x", padx=16, pady=(0, 10))

        self._label_selecionado = ctk.CTkLabel(
            painel,
            text="Nenhum ativo selecionado.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_selecionado.pack(anchor="w", padx=16, pady=(0, 10))

    def _montar_campos_compra(self, painel: ctk.CTkFrame) -> None:
        bloco = ctk.CTkFrame(painel, fg_color="transparent")
        bloco.pack(fill="x", padx=16, pady=(0, 8))

        linha1 = ctk.CTkFrame(bloco, fg_color="transparent")
        linha1.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(linha1, text="Quantidade").pack(side="left", padx=(0, 8))
        self._entrada_quantidade = ctk.CTkEntry(linha1, width=120, placeholder_text="Ex.: 100")
        self._entrada_quantidade.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(linha1, text="Preco de compra").pack(side="left", padx=(0, 8))
        self._entrada_preco = ctk.CTkEntry(linha1, width=140, placeholder_text="R$ 0,00")
        self._entrada_preco.pack(side="left")
        aplicar_mascara_moeda_ptbr(self._entrada_preco)

        linha2 = ctk.CTkFrame(bloco, fg_color="transparent")
        linha2.pack(fill="x")
        ctk.CTkLabel(linha2, text="Data da compra").pack(side="left", padx=(0, 8))
        self._entrada_data = ctk.CTkEntry(linha2, width=120, placeholder_text="dd/mm/aaaa")
        self._entrada_data.pack(side="left")

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

    def _aplicar_preenchimento_inicial(self) -> None:
        if self._posicao is None:
            hoje = datetime.now().strftime("%d/%m/%Y")
            self._entrada_data.insert(0, hoje)
            return

        self._combo_tipo.set(ROTULOS_TIPO_CARTEIRA[self._posicao.tipo_ativo])
        self._combo_tipo.configure(state="disabled")

        if self._editando and hasattr(self, "_label_ativo_fixo"):
            self._label_ativo_fixo.configure(
                text=f"{codigo_exibicao(self._posicao.simbolo)} ({ROTULOS_TIPO_CARTEIRA[self._posicao.tipo_ativo]})"
            )

        qtd = f"{self._posicao.quantidade:.8f}".rstrip("0").rstrip(".")
        self._entrada_quantidade.insert(0, qtd.replace(".", ","))
        preco_texto = f"{self._posicao.preco_compra:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        self._entrada_preco.insert(0, preco_texto)
        self._entrada_data.insert(0, self._posicao.data_compra)

    def _tipo_da_combo(self) -> TipoAtivoCarteira:
        rotulo = self._combo_tipo.get().strip()
        for chave, texto in ROTULOS_TIPO_CARTEIRA.items():
            if texto == rotulo:
                return chave
        return "acoes"

    def _limpar_selecao(self) -> None:
        self._simbolo_selecionado = None
        self._tipo_selecionado = self._tipo_da_combo()
        if hasattr(self, "_label_selecionado"):
            self._label_selecionado.configure(
                text="Nenhum ativo selecionado.",
                text_color=CORES["textoSecundario"],
            )
        if hasattr(self, "_frame_resultados"):
            for widget in self._frame_resultados.winfo_children():
                widget.destroy()

    def _termo_busca(self) -> str:
        termo = self._entrada_busca.get().strip()
        if termo:
            return termo
        return self._entrada_codigo.get().strip()

    def _normalizar_codigo_direto(self, codigo: str) -> tuple[str | None, str | None]:
        tipo = self._tipo_da_combo()
        if tipo == "cripto":
            return normalizar_simbolo_cripto(codigo)
        return normalizar_simbolo(codigo)

    def _confirmar_busca_ou_codigo(self) -> None:
        """Enter no campo opcional: busca pelo texto principal ou usa codigo digitado."""
        codigo = self._entrada_codigo.get().strip()
        if not codigo:
            self._pesquisar()
            return
        self._usar_codigo_direto()

    def _pesquisar(self) -> None:
        termo = self._termo_busca()
        if not termo:
            messagebox.showwarning("Buscar", "Digite o codigo ou nome do ativo.", parent=self)
            return

        tipo = self._tipo_da_combo()
        self._label_selecionado.configure(text="Buscando...", text_color=CORES["textoSecundario"])

        def tarefa():
            return self._controlador.pesquisar_ativos(tipo, termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_selecionado.configure(text=erro, text_color=CORES["erro"])
                return
            if not resultado:
                self._exibir_resultados([], tipo)
                return
            resultados, msg = resultado
            if msg:
                self._label_selecionado.configure(text=msg, text_color=CORES["erro"])
                return
            self._exibir_resultados(resultados or [], tipo)

        executar_em_thread(self, tarefa, ao_concluir)

    @staticmethod
    def _simbolo_do_resultado(item) -> str:
        if isinstance(item, ResultadoBusca):
            return item.simbolo
        simbolo = getattr(item, "simbolo", None)
        if simbolo:
            return str(simbolo)
        if isinstance(item, dict):
            return str(item.get("simbolo", ""))
        return str(item)

    def _exibir_resultados(self, resultados: list, tipo: TipoAtivoCarteira) -> None:
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()

        if not resultados:
            self._label_selecionado.configure(
                text="Nenhum resultado encontrado.",
                text_color=CORES["aviso"],
            )
            return

        unico_resultado = len(resultados) == 1
        simbolo_unico = (
            self._simbolo_do_resultado(resultados[0]) if unico_resultado else None
        )

        for item in resultados[:12]:
            simbolo = self._simbolo_do_resultado(item)
            rotulo = codigo_exibicao(simbolo)
            destacado = unico_resultado and simbolo == simbolo_unico

            ctk.CTkButton(
                self._frame_resultados,
                text=rotulo,
                anchor="w",
                fg_color=CORES["primaria"] if destacado else CORES["fundo"],
                hover_color=CORES["primariaHover"] if destacado else CORES["zebraEscura"],
                text_color=CORES.get("textoInverso", "#FFFFFF")
                if destacado
                else CORES["texto"],
                command=lambda s=simbolo, t=tipo: self._selecionar_ativo(s, t),
            ).pack(fill="x", pady=2)

        if unico_resultado and simbolo_unico:
            self._selecionar_ativo(simbolo_unico, tipo)
        else:
            self._label_selecionado.configure(
                text=f"{len(resultados)} resultado(s). Clique para selecionar.",
                text_color=CORES["textoSecundario"],
            )

    def _selecionar_ativo(self, simbolo: str, tipo: TipoAtivoCarteira) -> None:
        self._simbolo_selecionado = simbolo
        self._tipo_selecionado = tipo
        self._entrada_codigo.delete(0, "end")
        self._entrada_codigo.insert(0, codigo_exibicao(simbolo))
        self._label_selecionado.configure(
            text=f"Selecionado: {codigo_exibicao(simbolo)}",
            text_color=CORES["sucesso"],
        )

    def _usar_codigo_direto(self) -> None:
        codigo = self._entrada_codigo.get().strip() or self._entrada_busca.get().strip()
        if not codigo:
            messagebox.showwarning("Codigo", "Digite o codigo ou nome do ativo.", parent=self)
            return
        simbolo_ok, erro = self._normalizar_codigo_direto(codigo)
        if erro or not simbolo_ok:
            messagebox.showwarning("Codigo", erro or "Codigo invalido.", parent=self)
            return
        self._selecionar_ativo(simbolo_ok, self._tipo_da_combo())

    def _resolver_simbolo(self) -> str | None:
        if self._editando and self._posicao:
            return self._posicao.simbolo
        if self._simbolo_selecionado:
            return self._simbolo_selecionado
        codigo = ""
        if hasattr(self, "_entrada_codigo"):
            codigo = self._entrada_codigo.get().strip()
        if not codigo and hasattr(self, "_entrada_busca"):
            codigo = self._entrada_busca.get().strip()
        if not codigo:
            return None
        simbolo_ok, _ = self._normalizar_codigo_direto(codigo)
        return simbolo_ok

    def _salvar(self) -> None:
        simbolo = self._resolver_simbolo()
        if not simbolo:
            messagebox.showwarning("Carteira", "Selecione ou informe o ativo.", parent=self)
            return

        tipo = self._posicao.tipo_ativo if self._editando and self._posicao else self._tipo_selecionado
        quantidade = self._entrada_quantidade.get()
        preco = self._entrada_preco.get()
        data = self._entrada_data.get().strip()

        if self._editando and self._posicao:
            _, erro = self._controlador.atualizar_posicao(
                self._posicao.id,
                simbolo,
                tipo,
                quantidade,
                preco,
                data,
            )
        else:
            _, erro = self._controlador.adicionar_posicao(
                simbolo,
                tipo,
                quantidade,
                preco,
                data,
            )

        if erro:
            messagebox.showwarning("Carteira", erro, parent=self)
            return

        self._ao_salvar()
        self._ao_fechar()


def abrir_adicionar_carteira(
    pai: ctk.CTk | ctk.CTkToplevel,
    controlador: ControladorCarteira,
    ao_salvar: Callable[[], None],
    *,
    posicao: PosicaoCarteira | None = None,
) -> JanelaAdicionarCarteira | None:
    if not pai.winfo_exists():
        return None
    return JanelaAdicionarCarteira(pai, controlador, ao_salvar, posicao=posicao)
