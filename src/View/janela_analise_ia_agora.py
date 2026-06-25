"""Janela de analise do ativo com IA generativa (tela Agora)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.contexto_analise_agora import ContextoAnaliseAgora
from src.Service.analise_ia_mercado_servico import AnaliseIaMercadoServico
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_maximizada, executar_em_thread, janela_ui_ainda_ativa
from src.View.janela_config_analise_ia import abrir_janela_config_analise_ia
from src.View.painel_carregamento_helper import montar_painel_carregamento, parar_painel_carregamento
from src.View.tema import CORES


class JanelaAnaliseIaAgora(ctk.CTkToplevel):
    """Exibe analise gerada por IA com base nos dados atuais do Agora."""

    def __init__(
        self,
        pai: ctk.CTk,
        obter_contexto: Callable[[], ContextoAnaliseAgora],
    ) -> None:
        super().__init__(pai)
        self._obter_contexto = obter_contexto
        self._servico = AnaliseIaMercadoServico()
        self._carregando = False
        self._barra_carregamento = None
        self._frame_carregamento: ctk.CTkFrame | None = None

        contexto = obter_contexto()
        codigo = codigo_exibicao(contexto.simbolo)
        self.title(f"Analise com IA — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(720, 520)

        self._montar_interface(contexto)
        self._exibir_carregando_inicial()

        configurar_janela_maximizada(
            self,
            janela_pai=pai,
            ao_apos_layout=self._iniciar_fluxo,
        )
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        try:
            self.deiconify()
            self.lift(pai)
            self.focus_force()
            self.update_idletasks()
        except Exception:
            pass

    def _exibir_carregando_inicial(self) -> None:
        self._area_texto.grid_remove()
        if self._frame_carregamento is not None:
            self._frame_carregamento.destroy()
        self._frame_carregamento = ctk.CTkFrame(self, fg_color=CORES["fundo"])
        self._frame_carregamento.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        _, self._barra_carregamento, _ = montar_painel_carregamento(
            self._frame_carregamento,
            titulo="Preparando analise com IA...",
            detalhe="Aguarde nesta tela enquanto consultamos a inteligencia artificial.",
        )

    def _ocultar_carregando(self) -> None:
        parar_painel_carregamento(self._barra_carregamento)
        self._barra_carregamento = None
        if self._frame_carregamento is not None:
            self._frame_carregamento.destroy()
            self._frame_carregamento = None
        self._area_texto.grid()

    def _montar_interface(self, contexto: ContextoAnaliseAgora) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.grid(row=0, column=0, sticky="ew")

        barra = ctk.CTkFrame(cabecalho, fg_color="transparent")
        barra.pack(fill="x", padx=16, pady=12)

        codigo = codigo_exibicao(contexto.simbolo)
        ctk.CTkLabel(
            barra,
            text=f"Analise com IA — {codigo}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")

        self._btn_gerar = ctk.CTkButton(
            barra,
            text="Gerar novamente",
            command=self._gerar_analise,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=140,
            height=32,
        )
        self._btn_gerar.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            barra,
            text="Configurar IA",
            command=self._abrir_config,
            fg_color="transparent",
            hover_color=CORES["zebraEscura"],
            text_color=CORES["primaria"],
            border_width=1,
            border_color=CORES["borda"],
            width=120,
            height=32,
        ).pack(side="right")

        ctk.CTkLabel(
            cabecalho,
            text=(
                "A IA usa preco, variacao e metricas do momento em que voce abriu ou atualizou. "
                "Conteudo informativo — nao e recomendacao de investimento."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self._area_texto = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(size=14),
            fg_color=CORES["superficie"],
            text_color=CORES["texto"],
            wrap="word",
            activate_scrollbars=True,
        )
        self._area_texto.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        self._area_texto.configure(state="disabled")

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        modelo = self._servico.modelo_configurado()
        provedor = self._servico.provedor_configurado()
        self._label_rodape = ctk.CTkLabel(
            rodape,
            text=f"Provedor: {provedor} · Modelo: {modelo}",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        )
        self._label_rodape.pack(side="left")

        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self.destroy,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=100,
        ).pack(side="right")

    def _iniciar_fluxo(self) -> None:
        if self._servico.chave_configurada():
            self._gerar_analise()
            return
        self._ocultar_carregando()
        self._exibir_texto(
            "Nenhuma IA configurada.\n\n"
            "Clique em Configurar IA para escolher o provedor (Gemini ou Groq "
            "tem tier gratuito) e informar a chave. A configuracao e salva no .env."
        )
        self.after(200, self._abrir_config)

    def _abrir_config(self) -> None:
        abrir_janela_config_analise_ia(self, ao_salvar=self._apos_configurar)

    def _apos_configurar(self) -> None:
        self._atualizar_rodape()
        if self._servico.chave_configurada():
            self._gerar_analise()

    def _atualizar_rodape(self) -> None:
        if not hasattr(self, "_label_rodape"):
            return
        modelo = self._servico.modelo_configurado()
        provedor = self._servico.provedor_configurado()
        self._label_rodape.configure(text=f"Provedor: {provedor} · Modelo: {modelo}")

    def _gerar_analise(self) -> None:
        if self._carregando or not janela_ui_ainda_ativa(self):
            return

        if not self._servico.chave_configurada():
            self._ocultar_carregando()
            self._exibir_texto(
                "Configure a IA antes de gerar a analise.\n\n"
                "Use o botao Configurar IA no topo da tela."
            )
            return

        self._carregando = True
        self._btn_gerar.configure(state="disabled")
        if self._frame_carregamento is None:
            self._exibir_carregando_inicial()
        contexto = self._obter_contexto()

        def buscar():
            return self._servico.analisar(contexto)

        executar_em_thread(self, buscar, self._ao_concluir)

    def _ao_concluir(self, resultado, erro_thread) -> None:
        self._carregando = False
        if not janela_ui_ainda_ativa(self):
            return
        self._btn_gerar.configure(state="normal")
        self._ocultar_carregando()

        if erro_thread:
            self._exibir_texto(f"Erro ao gerar analise:\n\n{erro_thread}")
            return

        texto, erro = resultado if resultado else (None, "Resposta vazia.")
        if erro or not texto:
            self._exibir_texto(f"Nao foi possivel gerar a analise:\n\n{erro or 'Resposta vazia.'}")
            return
        self._exibir_texto(texto)

    def _exibir_texto(self, texto: str) -> None:
        self._area_texto.configure(state="normal")
        self._area_texto.delete("1.0", "end")
        self._area_texto.insert("1.0", texto)
        self._area_texto.configure(state="disabled")


def abrir_janela_analise_ia_agora(
    pai: ctk.CTk,
    obter_contexto: Callable[[], ContextoAnaliseAgora],
) -> JanelaAnaliseIaAgora | None:
    if not pai.winfo_exists():
        return None
    return JanelaAnaliseIaAgora(pai, obter_contexto)
