"""Modal para registrar ou editar compra na carteira."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_carteira import ControladorCarteira
from src.Model.carteira import (
    ROTULOS_TIPO_CARTEIRA,
    PosicaoCarteira,
    ResultadoBuscaCarteira,
    TipoAtivoCarteira,
)
from src.Model.resultado_busca import ResultadoBusca
from src.Tool.blacklist_ativos_helper import confirmar_cadastro_blacklist
from src.Tool.carteira_ativo_helper import normalizar_simbolo_carteira
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import (
    agendar_na_ui,
    centralizar_janela_sobre_referencia,
    configurar_janela_filha_modal,
    executar_em_thread,
    liberar_modal_janela_filha,
)
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr, formatar_centavos_ptbr
from src.View.campo_data_calendario_helper import (
    CampoDataCalendario,
    data_de_texto_ptbr,
    montar_campo_data_calendario,
)
from src.View.tema import CORES

_LARGURA = 520
_ALTURA = 660
_ALTURA_COMPACTA = 520
_ALTURA_AREA_FORMULARIO = 480
_ALTURA_AREA_FORMULARIO_COMPACTA = 280
_MARGEM_ALTURA_EXTRA_PX = 32


def _texto_moeda(valor: float) -> str:
    centavos = max(0, int(round(valor * 100)))
    return f"R$ {formatar_centavos_ptbr(centavos)}"


class JanelaAdicionarCarteira(ctk.CTkToplevel):
    """Formulario de compra na carteira."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        controlador: ControladorCarteira,
        ao_salvar: Callable[[], None],
        *,
        posicao: PosicaoCarteira | None = None,
        preencher_ativo: tuple[str, TipoAtivoCarteira] | None = None,
        preco_compra_sugerido: float | None = None,
        quantidade_sugerida: float | None = None,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._ao_salvar = ao_salvar
        self._janela_pai_ref = pai
        self._posicao = posicao
        self._editando = posicao is not None
        self._preco_compra_sugerido = preco_compra_sugerido
        self._quantidade_sugerida = quantidade_sugerida
        self._nova_compra_ativo = preencher_ativo is not None and not self._editando
        if posicao is not None:
            self._simbolo_selecionado = posicao.simbolo
            self._tipo_selecionado = posicao.tipo_ativo
        elif preencher_ativo is not None:
            self._simbolo_selecionado, self._tipo_selecionado = preencher_ativo
        else:
            self._simbolo_selecionado = None
            self._tipo_selecionado = None

        if self._editando:
            titulo = "Editar posicao"
        elif self._nova_compra_ativo:
            titulo = "Nova compra do ativo"
        else:
            titulo = "Registrar compra"
        self.title(titulo)
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(_LARGURA, self._altura_minima_conteudo())

        self._montar_interface()
        self._aplicar_preenchimento_inicial()
        for entrada in (self._entrada_quantidade, self._entrada_preco, self._campo_data.entrada):
            entrada.bind("<Return>", lambda _e: self._salvar())
        self._ajustar_tamanho_conteudo(pai)
        configurar_janela_filha_modal(self, pai)
        self._agendar_reajuste_tamanho_ao_exibir()
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _centralizar_sobre_pai(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            altura = max(self._altura_minima_conteudo(), self._medir_altura_janela())
            centralizar_janela_sobre_referencia(self, pai, _LARGURA, altura)
        except Exception:
            pass

    def _altura_area_formulario(self) -> int:
        """Altura visivel da area rolavel com os campos do formulario."""
        if self._editando or self._nova_compra_ativo:
            return _ALTURA_AREA_FORMULARIO_COMPACTA
        return _ALTURA_AREA_FORMULARIO

    def _altura_minima_conteudo(self) -> int:
        """Altura minima da janela conforme o modo do formulario."""
        cabecalho = 130 if not (self._editando or self._nova_compra_ativo) else 96
        area_topo = 150 if not (self._editando or self._nova_compra_ativo) else 0
        return cabecalho + area_topo + self._altura_area_formulario() + 56 + _MARGEM_ALTURA_EXTRA_PX

    def _medir_altura_janela(self) -> int:
        """Soma cabecalho, area rolavel e barra de botoes sem comprimir o painel."""
        self.update_idletasks()
        altura_cabecalho = int(self._cabecalho.winfo_reqheight())
        altura_topo = 0
        if hasattr(self, "_area_topo") and self._area_topo.winfo_manager():
            altura_topo = int(self._area_topo.winfo_reqheight())
        altura_area = self._altura_area_formulario()
        altura_botoes = int(self._barra_botoes.winfo_reqheight())
        margens = 16 + 8 + 16 + 24
        return altura_cabecalho + altura_topo + altura_area + altura_botoes + margens + _MARGEM_ALTURA_EXTRA_PX

    def _rolar_para_campo_preco(self) -> None:
        """Garante que o campo de valor fique visivel na area rolavel."""
        try:
            self.update_idletasks()
            canvas = self._area_formulario._parent_canvas
            canvas.update_idletasks()
            y_widget = self._entrada_preco.winfo_rooty() - self._area_formulario.winfo_rooty()
            altura_visivel = max(1, self._area_formulario.winfo_height())
            fracao = max(0.0, min(1.0, (y_widget - altura_visivel * 0.35) / max(1, canvas.bbox("all")[3])))
            canvas.yview_moveto(fracao)
        except Exception:
            pass

    def _agendar_reajuste_tamanho_ao_exibir(self) -> None:
        """Recalcula altura apos exibir; evita cortar campos no primeiro paint."""

        def reajustar() -> None:
            self._ajustar_tamanho_conteudo(self._janela_pai_ref)
            self._rolar_para_campo_preco()

        agendar_na_ui(self, reajustar)

        def ao_exibir(_evento=None) -> None:
            agendar_na_ui(self, reajustar)

        try:
            self.bind("<Map>", ao_exibir, add=True)
        except Exception:
            pass

    def _ajustar_tamanho_conteudo(self, pai: ctk.CTk | ctk.CTkToplevel | None = None) -> None:
        referencia = pai or self._janela_pai_ref
        try:
            altura = max(self._altura_minima_conteudo(), self._medir_altura_janela())
            self.minsize(_LARGURA, altura)
            self.geometry(f"{_LARGURA}x{altura}")
            if referencia is not None:
                self._centralizar_sobre_pai(referencia)
        except Exception:
            if referencia is not None:
                self._centralizar_sobre_pai(referencia)

    def _ao_fechar(self) -> None:
        liberar_modal_janela_filha(self)
        self.destroy()

    def _montar_interface(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._painel = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        self._painel.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 8))
        self._painel.grid_columnconfigure(0, weight=1)
        self._painel.grid_rowconfigure(2, weight=1)

        if self._editando:
            titulo_form = "Editar posicao"
        elif self._nova_compra_ativo:
            titulo_form = "Nova compra do ativo"
        else:
            titulo_form = "Registrar compra"

        self._cabecalho = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._cabecalho.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))

        ctk.CTkLabel(
            self._cabecalho,
            text=titulo_form,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        if self._nova_compra_ativo:
            texto_ajuda = (
                "Cada compra vira uma linha separada na carteira. "
                "Informe quantidade, preco e data desta nova aquisicao."
            )
        elif self._editando:
            texto_ajuda = (
                "Altera somente esta linha da carteira. "
                "Para outra compra do mesmo ativo, use Nova compra do ativo."
            )
        else:
            texto_ajuda = (
                "Cada compra em data ou preco diferente pode ser registrada separadamente. "
                f"Ao salvar, o ativo entra no monitoramento com limites de ±"
                f"{self._controlador.carregar_variacao_monitoramento_pct():.0f}% "
                "sobre o preco medio de compra."
            )

        ctk.CTkLabel(
            self._cabecalho,
            text=texto_ajuda,
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=_LARGURA - 80,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        self._area_topo = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._area_topo.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        self._area_formulario = ctk.CTkScrollableFrame(
            self._painel,
            fg_color=CORES["fundo"],
            label_text="",
            height=self._altura_area_formulario(),
        )
        linha_scroll = 2 if not self._editando and not self._nova_compra_ativo else 1
        if self._editando or self._nova_compra_ativo:
            self._painel.grid_rowconfigure(1, weight=1)
        self._area_formulario.grid(row=linha_scroll, column=0, sticky="nsew", padx=12, pady=(0, 12))

        bloco_tipo = ctk.CTkFrame(
            self._area_topo if not self._editando and not self._nova_compra_ativo else self._area_formulario,
            fg_color="transparent",
        )
        bloco_tipo.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            bloco_tipo,
            text="Tipo de ativo",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")
        self._combo_tipo = ctk.CTkComboBox(
            bloco_tipo,
            values=list(ROTULOS_TIPO_CARTEIRA.values()),
            width=220,
        )
        self._combo_tipo.set("—")
        self._combo_tipo.pack(anchor="w", pady=(6, 0))
        if not self._editando:
            self._combo_tipo.configure(state="disabled")
            ctk.CTkLabel(
                bloco_tipo,
                text="Detectado automaticamente ao buscar ou informar o codigo.",
                font=ctk.CTkFont(size=11),
                text_color=CORES["textoSecundario"],
                wraplength=_LARGURA - 96,
                justify="left",
            ).pack(anchor="w", pady=(4, 0))

        if not self._editando and not self._nova_compra_ativo:
            self._montar_campo_busca(self._area_topo)
            self._montar_resultados_busca(self._area_formulario)
        else:
            try:
                self._area_topo.grid_remove()
            except Exception:
                pass
            self._label_ativo_fixo = ctk.CTkLabel(
                self._area_formulario,
                text="",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=CORES["texto"],
            )
            self._label_ativo_fixo.pack(anchor="w", pady=(0, 10))

        self._montar_campos_compra(self._area_formulario)
        self._barra_botoes = self._montar_botoes(self)

    def _montar_campo_busca(self, area: ctk.CTkFrame) -> None:
        """Campo e botao de busca ficam fora da area rolavel para nao serem cortados."""
        bloco_busca = ctk.CTkFrame(area, fg_color="transparent")
        bloco_busca.pack(fill="x")
        ctk.CTkLabel(
            bloco_busca,
            text="Codigo ou nome",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w")

        linha_busca = ctk.CTkFrame(bloco_busca, fg_color="transparent")
        linha_busca.pack(fill="x", pady=(6, 0))
        linha_busca.grid_columnconfigure(0, weight=1)

        self._entrada_busca = ctk.CTkEntry(
            linha_busca,
            placeholder_text="Ex.: PETR4, BTC, HGLG11",
        )
        self._entrada_busca.grid(row=0, column=0, columnspan=2, sticky="ew")
        self._entrada_busca.bind("<Return>", lambda _e: self._pesquisar())

        self._entrada_codigo = ctk.CTkEntry(
            linha_busca,
            placeholder_text="Codigo opcional",
        )
        self._entrada_codigo.grid(row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 8))
        self._entrada_codigo.bind("<Return>", lambda _e: self._confirmar_busca_ou_codigo())

        self._botao_buscar = ctk.CTkButton(
            linha_busca,
            text="Buscar",
            command=self._pesquisar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=110,
        )
        self._botao_buscar.grid(row=1, column=1, pady=(8, 0))

    def _montar_resultados_busca(self, area: ctk.CTkScrollableFrame) -> None:
        self._frame_resultados = ctk.CTkScrollableFrame(
            area,
            height=88,
            fg_color=CORES["superficie"],
            label_text="Resultados",
        )
        self._frame_resultados.pack(fill="x", pady=(0, 10))

        self._label_selecionado = ctk.CTkLabel(
            area,
            text="Nenhum ativo selecionado.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._label_selecionado.pack(anchor="w", pady=(0, 10))

    def _montar_campos_compra(self, area: ctk.CTkScrollableFrame) -> None:
        bloco = ctk.CTkFrame(area, fg_color="transparent")
        bloco.pack(fill="x", pady=(0, 8))

        linha1 = ctk.CTkFrame(bloco, fg_color="transparent")
        linha1.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(linha1, text="Quantidade").pack(side="left", padx=(0, 8))
        self._entrada_quantidade = ctk.CTkEntry(linha1, width=120, placeholder_text="Ex.: 100")
        self._entrada_quantidade.pack(side="left")

        self._modo_valor_compra = {"valor": "por_cota"}

        ctk.CTkLabel(
            bloco,
            text="Valor da compra",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", pady=(0, 4))

        self._seletor_modo_compra = ctk.CTkSegmentedButton(
            bloco,
            values=["Por cota", "Valor total"],
            command=self._atualizar_modo_valor_compra,
            fg_color=CORES["borda"],
            selected_color=CORES["primaria"],
            unselected_color=CORES["superficie"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        )
        self._seletor_modo_compra.set("Por cota")
        self._seletor_modo_compra.pack(anchor="w", pady=(0, 8))

        self._rotulo_preco_compra = ctk.CTkLabel(
            bloco,
            text="Preco de compra (por cota)",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        )
        self._rotulo_preco_compra.pack(anchor="w", pady=(0, 4))

        self._entrada_preco = ctk.CTkEntry(
            bloco,
            width=240,
            placeholder_text="R$ 0,00",
            fg_color=CORES["fundo"],
            border_color=CORES["borda"],
        )
        self._entrada_preco.pack(anchor="w", pady=(0, 8))
        aplicar_mascara_moeda_ptbr(self._entrada_preco)

        linha2 = ctk.CTkFrame(bloco, fg_color="transparent")
        linha2.pack(fill="x")
        ctk.CTkLabel(linha2, text="Data da compra").pack(side="left", padx=(0, 8))
        self._campo_data: CampoDataCalendario = montar_campo_data_calendario(
            linha2,
            valor_inicial=date.today(),
            largura_entrada=118,
        )

    def _atualizar_modo_valor_compra(self, valor: str) -> None:
        if valor == "Valor total":
            self._modo_valor_compra["valor"] = "valor_total"
            self._rotulo_preco_compra.configure(text="Valor total gasto na negociacao")
            self._entrada_preco.configure(placeholder_text="Ex.: 1.625,00")
            total = self._calcular_valor_total_compra_atual()
            if total is not None:
                self._entrada_preco.delete(0, "end")
                self._entrada_preco.insert(0, _texto_moeda(total))
            agendar_na_ui(self, self._rolar_para_campo_preco)
            return

        self._modo_valor_compra["valor"] = "por_cota"
        self._rotulo_preco_compra.configure(text="Preco de compra (por cota)")
        self._entrada_preco.configure(placeholder_text="R$ 0,00")
        if self._posicao is not None:
            self._entrada_preco.delete(0, "end")
            self._entrada_preco.insert(0, _texto_moeda(self._posicao.preco_compra))
            return

        from src.Tool.validadores import validar_quantidade_posicao, validar_valor_monetario_ptbr

        quantidade, _ = validar_quantidade_posicao(self._entrada_quantidade.get())
        total, _ = validar_valor_monetario_ptbr(self._entrada_preco.get())
        if quantidade and quantidade > 0 and total and total > 0:
            self._entrada_preco.delete(0, "end")
            self._entrada_preco.insert(0, _texto_moeda(round(total / quantidade, 4)))

    def _calcular_valor_total_compra_atual(self) -> float | None:
        from src.Tool.validadores import validar_quantidade_posicao, validar_valor_monetario_ptbr

        quantidade, erro_qtd = validar_quantidade_posicao(self._entrada_quantidade.get())
        if erro_qtd or quantidade is None or quantidade <= 0:
            if self._posicao is not None:
                return round(self._posicao.preco_compra * self._posicao.quantidade, 2)
            return None

        preco, erro_preco = validar_valor_monetario_ptbr(self._entrada_preco.get())
        if self._modo_valor_compra["valor"] == "por_cota" and not erro_preco and preco is not None:
            return round(preco * quantidade, 2)
        if self._posicao is not None:
            return round(self._posicao.preco_compra * self._posicao.quantidade, 2)
        return None

    def _montar_botoes(self, pai: ctk.CTkBaseClass) -> ctk.CTkFrame:
        barra = ctk.CTkFrame(pai, fg_color=CORES["fundo"])
        barra.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
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
        return barra

    def _aplicar_preenchimento_inicial(self) -> None:
        hoje = date.today()

        if self._nova_compra_ativo and self._tipo_selecionado and self._simbolo_selecionado:
            self._definir_tipo_automatico(self._tipo_selecionado)
            if hasattr(self, "_label_ativo_fixo"):
                self._label_ativo_fixo.configure(
                    text=(
                        f"{codigo_exibicao(self._simbolo_selecionado)} "
                        f"({ROTULOS_TIPO_CARTEIRA[self._tipo_selecionado]})"
                    )
                )
            self._campo_data.definir_data(hoje)
            if self._preco_compra_sugerido is not None and self._preco_compra_sugerido > 0:
                self._entrada_preco.insert(0, _texto_moeda(self._preco_compra_sugerido))
            if self._quantidade_sugerida is not None and self._quantidade_sugerida > 0:
                qtd = f"{self._quantidade_sugerida:.8f}".rstrip("0").rstrip(".")
                self._entrada_quantidade.insert(0, qtd.replace(".", ","))
            return

        if self._posicao is None:
            self._campo_data.definir_data(hoje)
            return

        self._combo_tipo.set(ROTULOS_TIPO_CARTEIRA[self._posicao.tipo_ativo])
        self._combo_tipo.configure(state="disabled")

        if self._editando and hasattr(self, "_label_ativo_fixo"):
            self._label_ativo_fixo.configure(
                text=f"{codigo_exibicao(self._posicao.simbolo)} ({ROTULOS_TIPO_CARTEIRA[self._posicao.tipo_ativo]})"
            )

        qtd = f"{self._posicao.quantidade:.8f}".rstrip("0").rstrip(".")
        self._entrada_quantidade.insert(0, qtd.replace(".", ","))
        self._entrada_preco.insert(0, _texto_moeda(self._posicao.preco_compra))
        data_posicao = data_de_texto_ptbr(self._posicao.data_compra)
        if data_posicao is not None:
            self._campo_data.definir_data(data_posicao)
        else:
            self._campo_data.definir_texto_ptbr(self._posicao.data_compra)

    def _definir_tipo_automatico(self, tipo: TipoAtivoCarteira) -> None:
        self._tipo_selecionado = tipo
        rotulo = ROTULOS_TIPO_CARTEIRA[tipo]
        if self._editando:
            self._combo_tipo.set(rotulo)
            return
        self._combo_tipo.configure(state="normal")
        self._combo_tipo.set(rotulo)
        self._combo_tipo.configure(state="disabled")

    def _termo_busca(self) -> str:
        termo = self._entrada_busca.get().strip()
        if termo:
            return termo
        return self._entrada_codigo.get().strip()

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

        self._label_selecionado.configure(text="Buscando...", text_color=CORES["textoSecundario"])

        def tarefa():
            return self._controlador.pesquisar_ativos_automatico(termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_selecionado.configure(text=erro, text_color=CORES["erro"])
                return
            if not resultado:
                self._exibir_resultados([])
                return
            resultados, msg = resultado
            if msg and not resultados:
                self._label_selecionado.configure(text=msg, text_color=CORES["aviso"])
                return
            self._exibir_resultados(resultados or [])

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

    def _rotulo_resultado(self, item: ResultadoBuscaCarteira | object) -> str:
        if isinstance(item, ResultadoBuscaCarteira):
            simbolo = codigo_exibicao(item.simbolo)
            tipo = ROTULOS_TIPO_CARTEIRA[item.tipo_ativo]
            nome = (item.nome or "").strip()
            if nome:
                return f"{simbolo} — {nome} ({tipo})"
            return f"{simbolo} ({tipo})"
        return codigo_exibicao(self._simbolo_do_resultado(item))

    def _tipo_do_resultado(self, item: ResultadoBuscaCarteira | object) -> TipoAtivoCarteira:
        if isinstance(item, ResultadoBuscaCarteira):
            return item.tipo_ativo
        return "acoes"

    def _exibir_resultados(self, resultados: list) -> None:
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()

        if not resultados:
            self._label_selecionado.configure(
                text="Nenhum resultado encontrado.",
                text_color=CORES["aviso"],
            )
            return

        unico_resultado = len(resultados) == 1
        item_unico = resultados[0] if unico_resultado else None
        simbolo_unico = (
            self._simbolo_do_resultado(item_unico) if item_unico is not None else None
        )

        for item in resultados[:12]:
            simbolo = self._simbolo_do_resultado(item)
            tipo = self._tipo_do_resultado(item)
            rotulo = self._rotulo_resultado(item)
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

        if unico_resultado and simbolo_unico and item_unico is not None:
            self._selecionar_ativo(simbolo_unico, self._tipo_do_resultado(item_unico))
        else:
            self._label_selecionado.configure(
                text=f"{len(resultados)} resultado(s). Clique para selecionar.",
                text_color=CORES["textoSecundario"],
            )
        self._ajustar_tamanho_conteudo()
        agendar_na_ui(self, self._rolar_para_campo_preco)

    def _selecionar_ativo(self, simbolo: str, tipo: TipoAtivoCarteira) -> None:
        self._simbolo_selecionado = simbolo
        self._definir_tipo_automatico(tipo)
        self._entrada_codigo.delete(0, "end")
        self._entrada_codigo.insert(0, codigo_exibicao(simbolo))
        rotulo_tipo = ROTULOS_TIPO_CARTEIRA[tipo]
        self._label_selecionado.configure(
            text=f"Selecionado: {codigo_exibicao(simbolo)} ({rotulo_tipo})",
            text_color=CORES["sucesso"],
        )
        self._ajustar_tamanho_conteudo()
        agendar_na_ui(self, self._rolar_para_campo_preco)

    def _usar_codigo_direto(self) -> None:
        codigo = self._entrada_codigo.get().strip() or self._entrada_busca.get().strip()
        if not codigo:
            messagebox.showwarning("Codigo", "Digite o codigo ou nome do ativo.", parent=self)
            return
        simbolo_ok, tipo_ok, erro = normalizar_simbolo_carteira(codigo)
        if erro or not simbolo_ok or not tipo_ok:
            messagebox.showwarning("Codigo", erro or "Codigo invalido.", parent=self)
            return
        self._selecionar_ativo(simbolo_ok, tipo_ok)

    def _resolver_simbolo_e_tipo(self) -> tuple[str | None, TipoAtivoCarteira | None]:
        if self._editando and self._posicao:
            return self._posicao.simbolo, self._posicao.tipo_ativo
        if self._simbolo_selecionado and self._tipo_selecionado:
            return self._simbolo_selecionado, self._tipo_selecionado
        codigo = ""
        if hasattr(self, "_entrada_codigo"):
            codigo = self._entrada_codigo.get().strip()
        if not codigo and hasattr(self, "_entrada_busca"):
            codigo = self._entrada_busca.get().strip()
        if not codigo:
            return None, None
        return normalizar_simbolo_carteira(codigo)

    def _salvar(self) -> None:
        simbolo, tipo = self._resolver_simbolo_e_tipo()
        if not simbolo:
            messagebox.showwarning("Carteira", "Selecione ou informe o ativo.", parent=self)
            return
        if not tipo:
            messagebox.showwarning(
                "Carteira",
                "Nao foi possivel identificar o tipo do ativo. Busque novamente ou informe o codigo.",
                parent=self,
            )
            return
        quantidade = self._entrada_quantidade.get()
        preco = self._entrada_preco.get()
        data = self._campo_data.obter_texto()
        modo_valor = self._modo_valor_compra["valor"]

        precisa_aviso_blacklist = not self._editando
        if self._editando and self._posicao and simbolo != self._posicao.simbolo:
            precisa_aviso_blacklist = True
        if precisa_aviso_blacklist and not confirmar_cadastro_blacklist(simbolo, parent=self):
            return

        if self._editando and self._posicao:
            _, erro = self._controlador.atualizar_posicao(
                self._posicao.id,
                simbolo,
                tipo,
                quantidade,
                preco,
                data,
                modo_valor_compra=modo_valor,
            )
        else:
            _, erro = self._controlador.adicionar_posicao(
                simbolo,
                tipo,
                quantidade,
                preco,
                data,
                modo_valor_compra=modo_valor,
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
    preencher_ativo: tuple[str, TipoAtivoCarteira] | None = None,
    preco_compra_sugerido: float | None = None,
    quantidade_sugerida: float | None = None,
) -> JanelaAdicionarCarteira | None:
    if not pai.winfo_exists():
        return None
    return JanelaAdicionarCarteira(
        pai,
        controlador,
        ao_salvar,
        posicao=posicao,
        preencher_ativo=preencher_ativo,
        preco_compra_sugerido=preco_compra_sugerido,
        quantidade_sugerida=quantidade_sugerida,
    )
