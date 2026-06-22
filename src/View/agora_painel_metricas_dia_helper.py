"""Painel de metricas do pregão em um dia historico (tela Agora — Ver dia)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.Model.agora_dia_historico import ResumoDiaAgora
from src.View.formatadores import formatar_moeda, formatar_variacao
from src.View.tema import CORES

_LIMITE_RESUMO = 140


class PainelMetricasDiaAgora:
    """Grade recolhivel com abertura, alta, baixa, fechamento e volume do dia."""

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
            text="Metricas do dia",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left", padx=(0, 8))

        self._label_resumo = ctk.CTkLabel(
            cabecalho,
            text="Carregando metricas do dia...",
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
            self._frame_grade.grid_columnconfigure(coluna, weight=1, uniform="metricas_dia")

        coluna_1 = self._montar_coluna(0)
        self._adicionar_linha(coluna_1, "abertura", "Abertura")
        self._adicionar_linha(coluna_1, "maxima", "Alta")
        self._adicionar_linha(coluna_1, "minima", "Baixa")

        coluna_2 = self._montar_coluna(1)
        self._adicionar_linha(coluna_2, "fechamento", "Fechamento")
        self._adicionar_linha(coluna_2, "fechamento_anterior", "Fech. anterior")
        self._adicionar_linha(coluna_2, "variacao", "Variacao do dia")

        coluna_3 = self._montar_coluna(2)
        self._adicionar_linha(coluna_3, "volume", "Volume")

        self._frame_grade.pack_forget()
        self._btn_expandir.configure(text="▶")

        return card

    def _montar_coluna(self, indice: int) -> ctk.CTkFrame:
        if self._frame_grade is None:
            raise RuntimeError("Painel de metricas do dia nao montado.")
        coluna = ctk.CTkFrame(
            self._frame_grade,
            fg_color=CORES["superficie"],
            corner_radius=8,
            border_width=1,
            border_color=CORES["borda"],
        )
        coluna.grid(row=0, column=indice, sticky="nsew", padx=(0 if indice == 0 else 6, 0))
        return coluna

    def _adicionar_linha(self, coluna: ctk.CTkFrame, chave: str, rotulo: str) -> None:
        bloco = ctk.CTkFrame(coluna, fg_color="transparent")
        bloco.pack(fill="x", padx=10, pady=(8, 0))

        ctk.CTkLabel(
            bloco,
            text=rotulo,
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            anchor="w",
        ).pack(fill="x")

        label_valor = ctk.CTkLabel(
            bloco,
            text="—",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=CORES["texto"],
            anchor="w",
        )
        label_valor.pack(fill="x", pady=(2, 0))

        ctk.CTkFrame(coluna, fg_color=CORES["borda"], height=1, corner_radius=0).pack(
            fill="x",
            padx=10,
            pady=(8, 0),
        )
        self._valores[chave] = label_valor

    def _montar_texto_resumo(self, resumo: ResumoDiaAgora) -> str:
        moeda = resumo.moeda
        partes = [
            f"Abertura {formatar_moeda(resumo.abertura, moeda)}",
            f"Alta {formatar_moeda(resumo.maxima, moeda)}",
            f"Baixa {formatar_moeda(resumo.minima, moeda)}",
            f"Fechamento {formatar_moeda(resumo.fechamento, moeda)}",
            formatar_variacao(resumo.variacao_valor, resumo.variacao_pct, moeda),
        ]
        if resumo.volume_total is not None:
            partes.append(f"Volume {resumo.volume_total:,}".replace(",", "."))
        texto = "  ·  ".join(partes)
        if len(texto) <= _LIMITE_RESUMO:
            return texto
        return texto[:_LIMITE_RESUMO].rstrip() + "..."

    def atualizar(self, resumo: ResumoDiaAgora) -> None:
        moeda = resumo.moeda
        mapa: dict[str, str] = {
            "abertura": formatar_moeda(resumo.abertura, moeda),
            "maxima": formatar_moeda(resumo.maxima, moeda),
            "minima": formatar_moeda(resumo.minima, moeda),
            "fechamento": formatar_moeda(resumo.fechamento, moeda),
            "fechamento_anterior": (
                formatar_moeda(resumo.fechamento_anterior, moeda)
                if resumo.fechamento_anterior is not None
                else "—"
            ),
            "variacao": formatar_variacao(
                resumo.variacao_valor,
                resumo.variacao_pct,
                moeda,
            ),
            "volume": (
                f"{resumo.volume_total:,}".replace(",", ".")
                if resumo.volume_total is not None
                else "—"
            ),
        }
        cor_variacao = CORES["sucesso"] if resumo.variacao_valor >= 0 else CORES["erro"]

        for chave, texto in mapa.items():
            rotulo = self._valores.get(chave)
            if rotulo is None:
                continue
            rotulo.configure(text=texto)
            if chave == "variacao":
                rotulo.configure(text_color=cor_variacao)
            else:
                rotulo.configure(text_color=CORES["texto"])

        if self._label_resumo is not None:
            self._label_resumo.configure(text=self._montar_texto_resumo(resumo))

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
        if self._ao_alternar_expansao is not None:
            self._ao_alternar_expansao()
