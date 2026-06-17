"""Modal para cadastrar alerta de preco em um ativo."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk
from src.View import mensagem_helper as messagebox

from src.Controller.controlador_monitoramento import ControladorMonitoramento
from src.Model.monitoramento import (
    ROTULOS_TIPO_ATIVO,
    TIPOS_ATIVO_MONITORAMENTO,
    TipoAtivoMonitoramento,
)
from src.Model.resultado_busca import ResultadoBusca
from src.Tool.blacklist_ativos_helper import confirmar_cadastro_blacklist
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_filha_modal, executar_em_thread, liberar_modal_janela_filha, centralizar_janela_sobre_referencia
from src.Tool.mascara_moeda_helper import aplicar_mascara_moeda_ptbr
from src.Tool.validadores import validar_limites_monitoramento, validar_valor_monetario_opcional
from src.View.janela_calcular_limites_monitoramento import abrir_calcular_limites_monitoramento
from src.View.limites_monitoramento_ui_helper import preencher_entrada_moeda
from src.View.tema import CORES

_LARGURA_COMPLETA = 520
_ALTURA_COMPLETA = 520
_LARGURA_RAPIDA = 440
_ALTURA_RAPIDA = 420


class JanelaAdicionarMonitoramento(ctk.CTkToplevel):
    """Formulario para incluir ativo com valor baixo e/ou valor alto."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorMonitoramento,
        ao_salvar: Callable[[], None],
        *,
        simbolo_preenchido: str | None = None,
        tipo_ativo_preenchido: TipoAtivoMonitoramento | None = None,
        apenas_limites: bool = False,
        nome_ativo: str | None = None,
        preco_atual_texto: str | None = None,
        preco_atual: float | None = None,
        moeda_ativo: str = "BRL",
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._ao_salvar = ao_salvar
        self._simbolo_preenchido = (simbolo_preenchido or "").strip() or None
        self._tipo_ativo_preenchido = tipo_ativo_preenchido
        self._modo_apenas_limites = bool(
            apenas_limites and self._simbolo_preenchido and self._tipo_ativo_preenchido
        )
        self._nome_ativo = (nome_ativo or "").strip() or None
        self._preco_atual_texto = (preco_atual_texto or "").strip() or None
        self._preco_atual = preco_atual if preco_atual is not None and preco_atual > 0 else None
        self._moeda_ativo = (moeda_ativo or "BRL").strip().upper() or "BRL"
        self._janela_calcular = None
        self._simbolo_selecionado: str | None = self._simbolo_preenchido

        self._largura = _LARGURA_RAPIDA if self._modo_apenas_limites else _LARGURA_COMPLETA
        self._altura = _ALTURA_RAPIDA if self._modo_apenas_limites else _ALTURA_COMPLETA

        codigo_titulo = codigo_exibicao(self._simbolo_preenchido) if self._simbolo_preenchido else ""
        if self._modo_apenas_limites and codigo_titulo:
            self.title(f"Monitoramento — {codigo_titulo}")
        else:
            self.title("Adicionar monitoramento")

        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(self._largura, self._altura)

        self._montar_interface()
        if not self._modo_apenas_limites:
            self._aplicar_preenchimento_inicial()
        self._ajustar_tamanho_conteudo(pai)
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        if self._modo_apenas_limites:
            self._entrada_valor_baixo.focus_set()

    def _centralizar_sobre_pai(self, pai: ctk.CTk) -> None:
        try:
            self.update_idletasks()
            centralizar_janela_sobre_referencia(self, pai, self._largura, self._altura)
        except Exception:
            pass

    def _ajustar_tamanho_conteudo(self, pai: ctk.CTk) -> None:
        """Garante altura suficiente para exibir botoes apos card e campos de limite."""
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

        titulo = "Definir limites" if self._modo_apenas_limites else "Adicionar monitoramento"
        ctk.CTkLabel(
            painel,
            text=titulo,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            painel,
            text="Defina limites de preco. A linha ficara vermelha abaixo do valor baixo e verde acima do valor alto.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=self._largura - 80,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        if self._modo_apenas_limites:
            self._montar_resumo_ativo(painel)
        else:
            self._montar_selecao_ativo(painel)

        self._montar_limites(painel)
        self._montar_botoes(painel)

    def _montar_resumo_ativo(self, painel: ctk.CTkFrame) -> None:
        codigo = codigo_exibicao(self._simbolo_preenchido or "")
        tipo_rotulo = (
            ROTULOS_TIPO_ATIVO[self._tipo_ativo_preenchido]
            if self._tipo_ativo_preenchido
            else ""
        )

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

        if self._nome_ativo and self._nome_ativo.upper() != codigo.upper():
            ctk.CTkLabel(
                card,
                text=self._nome_ativo,
                font=ctk.CTkFont(size=12),
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=12, pady=(0, 2))

        if self._preco_atual_texto:
            ctk.CTkLabel(
                card,
                text=f"Preco atual: {self._preco_atual_texto}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=CORES["primaria"],
            ).pack(anchor="w", padx=12, pady=(4, 10))
        else:
            ctk.CTkLabel(
                card,
                text="",
            ).pack(pady=(0, 6))

    def _montar_selecao_ativo(self, painel: ctk.CTkFrame) -> None:
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
            values=[ROTULOS_TIPO_ATIVO[t] for t in TIPOS_ATIVO_MONITORAMENTO],
            width=220,
            command=lambda _v: self._limpar_selecao(),
        )
        self._combo_tipo.set(ROTULOS_TIPO_ATIVO["acoes"])
        self._combo_tipo.pack(anchor="w", pady=(6, 0))

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
        self._entrada_codigo = ctk.CTkEntry(linha_busca, width=100, placeholder_text="Codigo")
        self._entrada_codigo.pack(side="left", padx=(0, 8))
        self._entrada_codigo.bind("<Return>", lambda _e: self._usar_codigo_direto())
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
            height=110,
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
        aplicar_mascara_moeda_ptbr(self._entrada_valor_baixo)
        aplicar_mascara_moeda_ptbr(self._entrada_valor_alto)

    def _abrir_calcular_limites(self) -> None:
        preco, moeda, titulo, erro = self._resolver_dados_calculo_limites()
        if erro:
            messagebox.showwarning("Calcular limites", erro, parent=self)
            return
        assert preco is not None and moeda is not None

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
            preco,
            moeda,
            ao_aplicar,
            titulo_ativo=titulo,
        )

    def _resolver_dados_calculo_limites(
        self,
    ) -> tuple[float | None, str | None, str | None, str | None]:
        if self._preco_atual is not None and self._preco_atual > 0:
            titulo = codigo_exibicao(self._simbolo_preenchido) if self._simbolo_preenchido else None
            return self._preco_atual, self._moeda_ativo, titulo, None

        simbolo = self._simbolo_selecionado or (
            self._entrada_codigo.get().strip() if hasattr(self, "_entrada_codigo") else None
        )
        if not simbolo:
            return None, None, None, "Selecione um ativo antes de calcular os limites."

        tipo = self._tipo_selecionado()
        cotacao, erro = self._controlador.obter_cotacao_ativo(simbolo, tipo)
        if erro or cotacao is None or cotacao.preco <= 0:
            return None, None, None, erro or "Cotacao indisponivel para calcular os limites."

        return cotacao.preco, cotacao.moeda, codigo_exibicao(simbolo), None

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
        """Preenche tipo e ativo quando aberto com dados parciais (modo completo)."""
        if self._tipo_ativo_preenchido is not None:
            self._combo_tipo.set(ROTULOS_TIPO_ATIVO[self._tipo_ativo_preenchido])

        if not self._simbolo_preenchido:
            return

        codigo = codigo_exibicao(self._simbolo_preenchido)
        self._entrada_codigo.insert(0, codigo)
        self._label_selecionado.configure(
            text=f"Ativo informado: {codigo}",
            text_color=CORES["sucesso"],
        )

    def _tipo_selecionado(self) -> TipoAtivoMonitoramento:
        if self._modo_apenas_limites and self._tipo_ativo_preenchido:
            return self._tipo_ativo_preenchido

        rotulo = self._combo_tipo.get().strip()
        for chave, texto in ROTULOS_TIPO_ATIVO.items():
            if texto == rotulo:
                return chave
        return "acoes"

    def _limpar_selecao(self) -> None:
        self._simbolo_selecionado = None
        self._label_selecionado.configure(
            text="Nenhum ativo selecionado.",
            text_color=CORES["textoSecundario"],
        )
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()

    def _pesquisar(self) -> None:
        termo = self._entrada_busca.get().strip()
        if not termo:
            messagebox.showwarning("Buscar", "Digite o codigo ou nome do ativo.", parent=self)
            return

        tipo = self._tipo_selecionado()
        self._label_selecionado.configure(text="Buscando...", text_color=CORES["textoSecundario"])

        def tarefa():
            return self._controlador.pesquisar_ativos(tipo, termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_selecionado.configure(text=erro, text_color=CORES["erro"])
                return
            resultados, msg = resultado
            if msg:
                self._label_selecionado.configure(text=msg, text_color=CORES["erro"])
                return
            self._exibir_resultados(resultados or [])

        executar_em_thread(self, tarefa, ao_concluir)

    def _exibir_resultados(self, resultados: list[ResultadoBusca]) -> None:
        for widget in self._frame_resultados.winfo_children():
            widget.destroy()

        if not resultados:
            self._label_selecionado.configure(
                text="Nenhum resultado encontrado.",
                text_color=CORES["textoSecundario"],
            )
            return

        for item in resultados:
            codigo = codigo_exibicao(item.simbolo)
            ctk.CTkButton(
                self._frame_resultados,
                text=f"{codigo} — {item.nome}",
                anchor="w",
                fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
                command=lambda s=item.simbolo, n=item.nome: self._selecionar_ativo(s, n),
            ).pack(fill="x", pady=2)

        self._label_selecionado.configure(
            text=f"{len(resultados)} resultado(s). Clique para selecionar.",
            text_color=CORES["textoSecundario"],
        )

    def _selecionar_ativo(self, simbolo: str, nome: str) -> None:
        self._simbolo_selecionado = simbolo
        self._label_selecionado.configure(
            text=f"Selecionado: {codigo_exibicao(simbolo)} — {nome}",
            text_color=CORES["sucesso"],
        )

    def _usar_codigo_direto(self) -> None:
        codigo = self._entrada_codigo.get().strip()
        if not codigo:
            messagebox.showwarning("Codigo", "Informe o codigo do ativo.", parent=self)
            return
        self._simbolo_selecionado = codigo
        self._label_selecionado.configure(
            text=f"Selecionado por codigo: {codigo}",
            text_color=CORES["sucesso"],
        )

    def _ler_valor_campo(self, entry: ctk.CTkEntry) -> tuple[float | None, str | None]:
        return validar_valor_monetario_opcional(entry.get())

    def _obter_simbolo_salvar(self) -> str | None:
        if self._modo_apenas_limites:
            return self._simbolo_preenchido
        simbolo = self._simbolo_selecionado or self._entrada_codigo.get().strip()
        return simbolo or None

    def _salvar(self) -> None:
        simbolo = self._obter_simbolo_salvar()
        if not simbolo:
            messagebox.showwarning(
                "Ativo",
                "Selecione um ativo na busca ou informe o codigo.",
                parent=self,
            )
            return

        valor_baixo, erro_baixo = self._ler_valor_campo(self._entrada_valor_baixo)
        if erro_baixo:
            messagebox.showwarning("Valor baixo", erro_baixo, parent=self)
            return
        valor_alto, erro_alto = self._ler_valor_campo(self._entrada_valor_alto)
        if erro_alto:
            messagebox.showwarning("Valor alto", erro_alto, parent=self)
            return

        erro_limites = validar_limites_monitoramento(
            valor_baixo,
            valor_alto,
            self._preco_atual,
            self._moeda_ativo,
        ) if self._preco_atual is not None else validar_limites_monitoramento(
            valor_baixo,
            valor_alto,
        )
        if erro_limites:
            messagebox.showwarning("Limites", erro_limites, parent=self)
            return

        if not confirmar_cadastro_blacklist(simbolo, parent=self):
            return

        tipo = self._tipo_selecionado()
        kwargs_adicionar: dict = {}
        if self._preco_atual is not None:
            kwargs_adicionar["preco_atual"] = self._preco_atual
            kwargs_adicionar["moeda"] = self._moeda_ativo
        _, erro = self._controlador.adicionar_item(
            simbolo,
            tipo,
            valor_baixo,
            valor_alto,
            **kwargs_adicionar,
        )
        if erro:
            messagebox.showwarning("Monitoramento", erro, parent=self)
            return

        ao_salvar = self._ao_salvar
        self._ao_fechar()
        ao_salvar()


def abrir_adicionar_monitoramento(
    pai: ctk.CTk,
    controlador: ControladorMonitoramento,
    ao_salvar: Callable[[], None],
    *,
    simbolo: str | None = None,
    tipo_ativo: TipoAtivoMonitoramento | None = None,
    apenas_limites: bool = False,
    nome_ativo: str | None = None,
    preco_atual_texto: str | None = None,
    preco_atual: float | None = None,
    moeda_ativo: str = "BRL",
) -> JanelaAdicionarMonitoramento | None:
    if not pai.winfo_exists():
        return None
    return JanelaAdicionarMonitoramento(
        pai,
        controlador,
        ao_salvar,
        simbolo_preenchido=simbolo,
        tipo_ativo_preenchido=tipo_ativo,
        apenas_limites=apenas_limites,
        nome_ativo=nome_ativo,
        preco_atual_texto=preco_atual_texto,
        preco_atual=preco_atual,
        moeda_ativo=moeda_ativo,
    )
