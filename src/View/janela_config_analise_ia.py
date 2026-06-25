"""Modal para configurar provedor e chave de IA (gravacao no .env)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Tool.config_analise_ia import (
    ler_config_analise_ia,
    listar_provedores_ia,
    salvar_config_analise_ia,
    url_chave_provedor,
)
from src.Tool.janela_helper import (
    centralizar_janela_sobre_referencia,
    configurar_janela_filha_modal,
    liberar_modal_janela_filha,
)
from src.View import mensagem_helper as messagebox
from src.View.tema import CORES

_LARGURA = 520
_ALTURA = 420

_MAPA_PROVEDOR_ROTULO = {item[0]: item[1] for item in listar_provedores_ia()}
_ROTULOS_MENU = [item[1] for item in listar_provedores_ia()]
_MAPA_ROTULO_PROVEDOR = {item[1]: item[0] for item in listar_provedores_ia()}


class JanelaConfigAnaliseIa(ctk.CTkToplevel):
    """Formulario simples: provedor + chave API, salvo no .env."""

    def __init__(
        self,
        pai: ctk.CTk | ctk.CTkToplevel,
        ao_salvar: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(pai)
        self._ao_salvar = ao_salvar
        self._config_inicial = ler_config_analise_ia()
        self._chave_salva = self._config_inicial.chave_api

        self.title("Configurar IA")
        self.configure(fg_color=CORES["fundo"])
        self.resizable(False, False)
        self.minsize(_LARGURA, _ALTURA)

        self._montar_interface()
        self._centralizar_sobre_pai(pai)
        configurar_janela_filha_modal(self, pai)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()
        self.after(120, lambda: self._ajustar_tamanho(pai))

    def _centralizar_sobre_pai(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        try:
            self.update_idletasks()
            altura = max(_ALTURA, int(self.winfo_reqheight()))
            centralizar_janela_sobre_referencia(self, pai, _LARGURA, altura)
        except Exception:
            pass

    def _ajustar_tamanho(self, pai: ctk.CTk | ctk.CTkToplevel) -> None:
        self._centralizar_sobre_pai(pai)

    def _ao_fechar(self) -> None:
        liberar_modal_janela_filha(self)
        self.destroy()

    def _montar_interface(self) -> None:
        painel = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        painel.pack(fill="both", expand=True, padx=16, pady=16)

        # Botoes fixos na parte inferior para nunca ficarem fora da janela.
        self._montar_botoes(painel)

        conteudo = ctk.CTkFrame(painel, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        ctk.CTkLabel(
            conteudo,
            text="Configurar analise com IA",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            conteudo,
            text=(
                "Escolha o provedor e informe a chave de API. "
                "A configuracao e salva no arquivo .env na raiz do projeto."
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=460,
            justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 12))

        rotulo_inicial = _MAPA_PROVEDOR_ROTULO.get(
            self._config_inicial.provedor,
            _ROTULOS_MENU[0],
        )

        ctk.CTkLabel(
            conteudo,
            text="Provedor",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=8, pady=(0, 4))

        self._menu_provedor = ctk.CTkOptionMenu(
            conteudo,
            values=_ROTULOS_MENU,
            command=self._ao_trocar_provedor,
            fg_color=CORES["superficie"],
            button_color=CORES["primaria"],
            button_hover_color=CORES["primariaHover"],
            text_color=CORES["texto"],
            dropdown_fg_color=CORES["superficie"],
            dropdown_text_color=CORES["texto"],
            width=460,
        )
        self._menu_provedor.set(rotulo_inicial)
        self._menu_provedor.pack(fill="x", padx=8, pady=(0, 12))

        ctk.CTkLabel(
            conteudo,
            text="Chave de API",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=8, pady=(0, 4))

        linha_chave = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_chave.pack(fill="x", padx=8, pady=(0, 8))

        self._entrada_chave = ctk.CTkEntry(
            linha_chave,
            show="*",
            placeholder_text="Cole a chave aqui",
        )
        self._entrada_chave.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._btn_mostrar = ctk.CTkButton(
            linha_chave,
            text="Mostrar",
            width=90,
            command=self._alternar_visibilidade_chave,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            text_color=CORES.get("textoInverso", "#FFFFFF"),
        )
        self._btn_mostrar.pack(side="right")

        if self._chave_salva:
            self._entrada_chave.insert(0, self._chave_salva)

        self._label_ajuda = ctk.CTkLabel(
            conteudo,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            wraplength=460,
            justify="left",
        )
        self._label_ajuda.pack(anchor="w", padx=8, pady=(0, 8))

        status = (
            f"Status: {self._config_inicial.rotulo_provedor} configurado."
            if self._config_inicial.configurada
            else "Status: nenhuma IA configurada."
        )
        self._label_status = ctk.CTkLabel(
            conteudo,
            text=status,
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
        )
        self._label_status.pack(anchor="w", padx=8, pady=(0, 8))

        self._ao_trocar_provedor(rotulo_inicial)

    def _montar_botoes(self, painel: ctk.CTkFrame) -> None:
        barra = ctk.CTkFrame(painel, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=16, pady=(0, 16))

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

    def _provedor_selecionado(self) -> str:
        rotulo = self._menu_provedor.get()
        return _MAPA_ROTULO_PROVEDOR.get(rotulo, "gemini")

    def _ao_trocar_provedor(self, rotulo: str) -> None:
        provedor = _MAPA_ROTULO_PROVEDOR.get(rotulo, "gemini")
        url = url_chave_provedor(provedor)
        if provedor == "openai":
            detalhe = (
                f"Crie a chave em {url}. A OpenAI exige creditos na conta."
            )
        else:
            detalhe = f"Chave gratuita em {url} (sem cartao na maioria dos casos)."
        self._label_ajuda.configure(text=detalhe)

    def _alternar_visibilidade_chave(self) -> None:
        if self._entrada_chave.cget("show") == "*":
            self._entrada_chave.configure(show="")
            self._btn_mostrar.configure(text="Ocultar")
        else:
            self._entrada_chave.configure(show="*")
            self._btn_mostrar.configure(text="Mostrar")

    def _salvar(self) -> None:
        provedor = self._provedor_selecionado()
        chave = self._entrada_chave.get().strip()

        ok, erro = salvar_config_analise_ia(provedor, chave)
        if not ok:
            messagebox.showwarning("Configurar IA", erro, parent=self)
            return

        config = ler_config_analise_ia()
        self._label_status.configure(
            text=f"Status: {config.rotulo_provedor} configurado."
        )
        messagebox.showinfo(
            "Configurar IA",
            "Configuracao salva no .env.\n\nVoce ja pode gerar analises com IA.",
            parent=self,
        )

        if self._ao_salvar is not None:
            self._ao_salvar()
        self._ao_fechar()


def abrir_janela_config_analise_ia(
    pai: ctk.CTk | ctk.CTkToplevel,
    ao_salvar: Callable[[], None] | None = None,
) -> JanelaConfigAnaliseIa | None:
    if not pai.winfo_exists():
        return None
    return JanelaConfigAnaliseIa(pai, ao_salvar=ao_salvar)
