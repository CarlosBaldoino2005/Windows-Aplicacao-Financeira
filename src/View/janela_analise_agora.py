"""Hub de analise do ativo na tela Agora (analistas e IA)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.contexto_analise_agora import ContextoAnaliseAgora
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.janela_helper import configurar_janela_maximizada, janela_ui_ainda_ativa
from src.Tool.config_analise_ia import ler_config_analise_ia
from src.View.janela_analise_ia_agora import abrir_janela_analise_ia_agora
from src.View.janela_config_analise_ia import abrir_janela_config_analise_ia
from src.View.janela_opinioes_analistas import abrir_janela_opinioes_analistas
from src.View.tema import CORES


class JanelaAnaliseAgora(ctk.CTkToplevel):
    """Escolha entre analise de analistas (dados reais) ou analise com IA."""

    def __init__(
        self,
        pai: ctk.CTk,
        obter_contexto: Callable[[], ContextoAnaliseAgora],
    ) -> None:
        super().__init__(pai)
        self._pai = pai
        self._obter_contexto = obter_contexto
        self._janela_analistas: ctk.CTkToplevel | None = None
        self._janela_ia: ctk.CTkToplevel | None = None

        contexto = obter_contexto()
        codigo = codigo_exibicao(contexto.simbolo)
        self.title(f"Analise — {codigo}")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(560, 420)

        self._montar_interface(contexto)
        configurar_janela_maximizada(self, janela_pai=pai)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        try:
            self.deiconify()
            self.lift(pai)
            self.focus_force()
            self.update_idletasks()
        except Exception:
            pass

    def _garantir_janela_filha_visivel(self, janela: ctk.CTkToplevel) -> None:
        if not janela_ui_ainda_ativa(janela):
            return
        try:
            janela.deiconify()
            janela.lift(self)
            janela.focus_force()
            janela.update_idletasks()
        except Exception:
            pass

    def _montar_interface(self, contexto: ContextoAnaliseAgora) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        codigo = codigo_exibicao(contexto.simbolo)
        ctk.CTkLabel(
            container,
            text=f"Analise — {codigo}",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", pady=(0, 4))

        nome = contexto.nome_ativo or codigo
        ctk.CTkLabel(
            container,
            text=nome,
            font=ctk.CTkFont(size=14),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(
            container,
            text="Escolha o tipo de analise para este ativo:",
            font=ctk.CTkFont(size=13),
            text_color=CORES["texto"],
        ).pack(anchor="w", pady=(0, 12))

        grade = ctk.CTkFrame(container, fg_color="transparent")
        grade.pack(fill="x", pady=(0, 16))
        grade.grid_columnconfigure(0, weight=1, uniform="analise")
        grade.grid_columnconfigure(1, weight=1, uniform="analise")

        self._montar_card_opcao(
            grade,
            coluna=0,
            titulo="Analistas",
            descricao=(
                "Recomendacoes e precos-alvo de casas de analise "
                "(dados reais do mercado, sem IA)."
            ),
            rotulo_botao="Ver analistas",
            comando=self._abrir_analistas,
        )
        self._montar_card_opcao(
            grade,
            coluna=1,
            titulo="Inteligencia artificial",
            descricao=(
                "Analise gerada por IA (Gemini, Groq ou OpenAI) com preco, variacao "
                "e metricas atuais do Agora. Gemini e Groq tem tier gratuito."
            ),
            rotulo_botao="Analisar com IA",
            comando=self._abrir_ia,
            rotulo_secundario=self._texto_status_ia(),
            comando_secundario=self._abrir_config_ia,
        )

        ctk.CTkLabel(
            container,
            text=(
                "Nenhuma analise constitui recomendacao de investimento. "
                "Decisoes de compra e venda sao de sua responsabilidade."
            ),
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(8, 16))

        ctk.CTkButton(
            container,
            text="Fechar",
            command=self.destroy,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            width=120,
            height=36,
        ).pack(anchor="e")

    def _texto_status_ia(self) -> str:
        config = ler_config_analise_ia()
        if config.configurada:
            return f"IA: {config.rotulo_provedor}"
        return "IA: nao configurada — clique em Configurar"

    def _abrir_config_ia(self) -> None:
        abrir_janela_config_analise_ia(self, ao_salvar=self._atualizar_status_ia)

    def _atualizar_status_ia(self) -> None:
        if hasattr(self, "_label_status_ia") and self._label_status_ia.winfo_exists():
            self._label_status_ia.configure(text=self._texto_status_ia())

    def _montar_card_opcao(
        self,
        pai: ctk.CTkFrame,
        *,
        coluna: int,
        titulo: str,
        descricao: str,
        rotulo_botao: str,
        comando,
        rotulo_secundario: str | None = None,
        comando_secundario=None,
    ) -> None:
        card = ctk.CTkFrame(
            pai,
            fg_color=CORES["superficie"],
            corner_radius=12,
            border_width=1,
            border_color=CORES["borda"],
        )
        card.grid(row=0, column=coluna, sticky="nsew", padx=(0 if coluna == 0 else 8, 0))

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            card,
            text=descricao,
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 16))

        ctk.CTkButton(
            card,
            text=rotulo_botao,
            command=comando,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(fill="x", padx=16, pady=(0, 8 if rotulo_secundario else 16))

        if rotulo_secundario and comando_secundario is not None:
            self._label_status_ia = ctk.CTkLabel(
                card,
                text=rotulo_secundario,
                font=ctk.CTkFont(size=11),
                text_color=CORES["textoSecundario"],
                wraplength=360,
                justify="left",
            )
            self._label_status_ia.pack(anchor="w", padx=16, pady=(0, 8))

            ctk.CTkButton(
                card,
                text="Configurar IA",
                command=comando_secundario,
                fg_color="transparent",
                hover_color=CORES["zebraEscura"],
                text_color=CORES["primaria"],
                border_width=1,
                border_color=CORES["borda"],
                height=32,
                font=ctk.CTkFont(size=12),
            ).pack(fill="x", padx=16, pady=(0, 16))

    def _abrir_analistas(self) -> None:
        if self._janela_analistas is not None:
            try:
                if self._janela_analistas.winfo_exists():
                    self._janela_analistas.lift()
                    self._janela_analistas.focus_force()
                    return
            except Exception:
                pass

        contexto = self._obter_contexto()
        self._janela_analistas = abrir_janela_opinioes_analistas(
            self,
            contexto.simbolo,
            contexto.nome_ativo,
            contexto.moeda,
        )
        if self._janela_analistas is not None:
            self._garantir_janela_filha_visivel(self._janela_analistas)

    def _abrir_ia(self) -> None:
        if self._janela_ia is not None:
            try:
                if self._janela_ia.winfo_exists():
                    self._janela_ia.lift()
                    self._janela_ia.focus_force()
                    return
            except Exception:
                pass

        self._janela_ia = abrir_janela_analise_ia_agora(self, self._obter_contexto)
        if self._janela_ia is not None:
            self._garantir_janela_filha_visivel(self._janela_ia)


def abrir_janela_analise_agora(
    pai: ctk.CTk,
    obter_contexto: Callable[[], ContextoAnaliseAgora],
) -> JanelaAnaliseAgora | None:
    if not pai.winfo_exists():
        return None
    return JanelaAnaliseAgora(pai, obter_contexto)
