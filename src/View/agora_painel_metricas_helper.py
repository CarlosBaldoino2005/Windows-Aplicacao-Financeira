"""Painel de metricas de mercado na tela Agora (abertura, volume, 52 semanas)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Service.agora_metricas_mercado_servico import MetricasMercadoAgora
from src.View.tema import CORES

_LIMITE_RESUMO = 140


class PainelMetricasAgora:
    """Grade em tres colunas com metricas do ativo e resumo recolhivel."""

    def __init__(
        self,
        pai: ctk.CTkFrame,
        *,
        ao_alternar_expansao: Callable[[], None] | None = None,
    ) -> None:
        self._pai = pai
        self._ao_alternar_expansao = ao_alternar_expansao
        self._expandido = False
        self._raiz: ctk.CTkFrame | None = None
        self._frame_grade: ctk.CTkFrame | None = None
        self._label_resumo: ctk.CTkLabel | None = None
        self._btn_expandir: ctk.CTkButton | None = None
        self._valores: dict[str, ctk.CTkLabel] = {}

    def montar(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self._pai,
            fg_color=CORES.get("infoFundo", CORES["fundo"]),
            corner_radius=10,
            border_width=1,
            border_color=CORES["borda"],
        )
        self._raiz = card

        cabecalho = ctk.CTkFrame(card, fg_color="transparent")
        cabecalho.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            cabecalho,
            text="Metricas",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left", padx=(0, 8))

        self._label_resumo = ctk.CTkLabel(
            cabecalho,
            text="Carregando metricas de mercado...",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            anchor="w",
            justify="left",
            wraplength=760,
        )
        self._label_resumo.pack(side="left", fill="x", expand=True)

        self._btn_expandir = ctk.CTkButton(
            cabecalho,
            text="▼",
            width=28,
            height=28,
            fg_color=CORES["superficie"],
            hover_color=CORES["borda"],
            text_color=CORES["texto"],
            command=self._alternar_expansao,
        )
        self._btn_expandir.pack(side="right")

        self._frame_grade = ctk.CTkFrame(card, fg_color="transparent")
        self._frame_grade.pack(fill="x", padx=12, pady=(0, 12))
        for coluna in range(3):
            self._frame_grade.grid_columnconfigure(coluna, weight=1, uniform="metricas")

        coluna_1 = self._montar_coluna(0)
        self._adicionar_linha(coluna_1, "abertura", "Abrir")
        self._adicionar_linha(coluna_1, "alta_dia", "Alta")
        self._adicionar_linha(coluna_1, "baixa_dia", "Baixa")

        coluna_2 = self._montar_coluna(1)
        self._adicionar_linha(coluna_2, "volume_medio", "Volume medio")
        self._adicionar_linha(coluna_2, "volume_dia", "Volume")
        self._adicionar_linha(coluna_2, "alta_52_semanas", "Alto — 52 sem")

        coluna_3 = self._montar_coluna(2)
        self._adicionar_linha(coluna_3, "baixa_52_semanas", "Baixo — 52 sem")
        self._adicionar_linha(coluna_3, "circulacao", "Acoes em circulacao", rotulo_dinamico=True)

        self._frame_grade.pack_forget()
        self._btn_expandir.configure(text="▶")

        return card

    def _montar_coluna(self, indice: int) -> ctk.CTkFrame:
        if self._frame_grade is None:
            raise RuntimeError("Painel de metricas nao montado.")
        coluna = ctk.CTkFrame(
            self._frame_grade,
            fg_color=CORES["superficie"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        coluna.grid(row=0, column=indice, sticky="nsew", padx=(0 if indice == 0 else 6, 0))
        return coluna

    def _adicionar_linha(
        self,
        coluna: ctk.CTkFrame,
        chave: str,
        rotulo: str,
        *,
        rotulo_dinamico: bool = False,
    ) -> None:
        bloco = ctk.CTkFrame(coluna, fg_color="transparent")
        bloco.pack(fill="x", padx=10, pady=(8, 0))

        label_rotulo = ctk.CTkLabel(
            bloco,
            text=rotulo,
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
        )
        label_rotulo.pack(fill="x")

        linha_valor = ctk.CTkFrame(bloco, fg_color="transparent")
        linha_valor.pack(fill="x", pady=(2, 0))

        label_valor = ctk.CTkLabel(
            linha_valor,
            text="—",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        )
        label_valor.pack(fill="x")

        ctk.CTkFrame(coluna, fg_color=CORES["borda"], height=1, corner_radius=0).pack(
            fill="x",
            padx=10,
            pady=(8, 0),
        )

        self._valores[chave] = label_valor
        if rotulo_dinamico:
            self._valores[f"{chave}__rotulo"] = label_rotulo

    def atualizar(self, metricas: MetricasMercadoAgora) -> None:
        mapa = {
            "abertura": metricas.abertura,
            "alta_dia": metricas.alta_dia,
            "baixa_dia": metricas.baixa_dia,
            "volume_medio": metricas.volume_medio,
            "volume_dia": metricas.volume_dia,
            "alta_52_semanas": metricas.alta_52_semanas,
            "baixa_52_semanas": metricas.baixa_52_semanas,
            "circulacao": metricas.circulacao,
        }
        for chave, texto in mapa.items():
            rotulo = self._valores.get(chave)
            if rotulo is not None:
                rotulo.configure(text=texto)

        rotulo_circ = self._valores.get("circulacao__rotulo")
        if rotulo_circ is not None:
            rotulo_circ.configure(text=metricas.rotulo_circulacao)

        if self._label_resumo is not None:
            resumo = (metricas.resumo or "").strip()
            if not resumo:
                self._label_resumo.configure(text="Metricas de mercado do ativo.")
            elif len(resumo) <= _LIMITE_RESUMO:
                self._label_resumo.configure(text=resumo)
            else:
                self._label_resumo.configure(text=resumo[:_LIMITE_RESUMO].rstrip() + "...")

    def _alternar_expansao(self) -> None:
        if self._frame_grade is None or self._btn_expandir is None:
            return
        self._expandido = not self._expandido
        if self._expandido:
            self._frame_grade.pack(fill="x", padx=12, pady=(0, 12))
            self._btn_expandir.configure(text="▼")
        else:
            self._frame_grade.pack_forget()
            self._btn_expandir.configure(text="▶")
