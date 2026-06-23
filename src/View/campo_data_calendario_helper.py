"""Campo de data pt-BR com calendario popup (padrao UI do projeto)."""
from __future__ import annotations

import calendar
from collections.abc import Callable
from datetime import date

import customtkinter as ctk

from src.Tool.calendario_semana_helper import (
    ROTULOS_DIAS_SEMANA_DOMINGO,
    obter_semanas_mes_calendario,
)

from src.Tool.dia_util_helper import formatar_data_ptbr
from src.Tool.icone_calendario_helper import criar_botao_calendario
from src.Tool.mascara_data_helper import aplicar_mascara_data_ptbr
from src.Tool.janela_helper import janela_ui_ainda_ativa
from src.Tool.validadores import validar_data_ptbr
from src.View.tema import CORES


class CampoDataCalendario:
    """Entrada dd/mm/aaaa com seletor visual de calendario."""

    def __init__(
        self,
        pai: ctk.CTkFrame,
        *,
        valor_inicial: date | None = None,
        largura_entrada: int = 118,
        ao_mudar: Callable[[], None] | None = None,
    ) -> None:
        self._pai = pai
        self._ao_mudar = ao_mudar
        self._popup: ctk.CTkToplevel | None = None
        self._mes_visivel: date = valor_inicial or date.today()
        self._data_destaque: date | None = valor_inicial

        self.frame = ctk.CTkFrame(pai, fg_color="transparent")
        self.frame.pack(side="left")

        self._entrada = ctk.CTkEntry(self.frame, width=largura_entrada, placeholder_text="dd/mm/aaaa")
        self._entrada.pack(side="left", padx=(0, 6))
        if valor_inicial is not None:
            self._entrada.insert(0, formatar_data_ptbr(valor_inicial))
        aplicar_mascara_data_ptbr(self._entrada)

        criar_botao_calendario(
            self.frame,
            command=self._abrir_calendario,
            fg_color=CORES["borda"],
            hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        ).pack(side="left")

    def obter_texto(self) -> str:
        return self._entrada.get().strip()

    def obter_data(self) -> tuple[date | None, str | None]:
        texto = self.obter_texto()
        dt, erro = validar_data_ptbr(texto)
        if erro or dt is None:
            return None, erro or "Informe a data no formato dd/mm/aaaa."
        return dt.date(), None

    def definir_data(self, valor: date) -> None:
        self._entrada.delete(0, "end")
        self._entrada.insert(0, formatar_data_ptbr(valor))
        self._mes_visivel = valor
        self._data_destaque = valor

    def _sincronizar_data_do_input(self) -> None:
        """Atualiza mes visivel e destaque com a data valida do campo."""
        data_atual, _ = self.obter_data()
        if data_atual is not None:
            self._mes_visivel = data_atual
            self._data_destaque = data_atual

    def _abrir_calendario(self) -> None:
        self._sincronizar_data_do_input()

        if self._popup is not None:
            try:
                if self._popup.winfo_exists():
                    self._montar_calendario(self._popup)
                    self._popup.focus_force()
                    return
            except Exception:
                pass

        raiz = self._pai.winfo_toplevel()
        self._popup = ctk.CTkToplevel(raiz)
        self._popup.title("Selecionar data")
        self._popup.configure(fg_color=CORES["superficie"])
        self._popup.resizable(False, False)
        self._popup.transient(raiz)
        try:
            self._popup.grab_set()
        except Exception:
            pass

        self._montar_calendario(self._popup)
        self._popup.update_idletasks()
        x = self._entrada.winfo_rootx()
        y = self._entrada.winfo_rooty() + self._entrada.winfo_height() + 4
        self._popup.geometry(f"+{x}+{y}")
        self._popup.focus_force()

    def _montar_calendario(self, janela: ctk.CTkToplevel) -> None:
        for widget in janela.winfo_children():
            widget.destroy()

        barra = ctk.CTkFrame(janela, fg_color="transparent")
        barra.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkButton(
            barra,
            text="<",
            width=36,
            command=lambda: self._mudar_mes(-1),
            fg_color=CORES["borda"],
            hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        ).pack(side="left")

        meses = (
            "Janeiro",
            "Fevereiro",
            "Marco",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        )
        rotulo = f"{meses[self._mes_visivel.month - 1]} {self._mes_visivel.year}"
        ctk.CTkLabel(
            barra,
            text=rotulo,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left", expand=True)

        ctk.CTkButton(
            barra,
            text=">",
            width=36,
            command=lambda: self._mudar_mes(1),
            fg_color=CORES["borda"],
            hover_color=CORES["zebraEscura"],
            text_color=CORES["texto"],
        ).pack(side="right")

        grade = ctk.CTkFrame(janela, fg_color="transparent")
        grade.pack(padx=10, pady=(0, 10))

        for indice, nome in enumerate(ROTULOS_DIAS_SEMANA_DOMINGO):
            ctk.CTkLabel(
                grade,
                text=nome,
                width=34,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=CORES["textoSecundario"],
            ).grid(row=0, column=indice, padx=2, pady=2)

        semanas = obter_semanas_mes_calendario(self._mes_visivel.year, self._mes_visivel.month)
        hoje = date.today()
        for linha, semana in enumerate(semanas, start=1):
            for coluna, dia in enumerate(semana):
                if dia == 0:
                    ctk.CTkLabel(grade, text="", width=34).grid(row=linha, column=coluna, padx=2, pady=2)
                    continue
                data_botao = date(self._mes_visivel.year, self._mes_visivel.month, dia)
                eh_selecionada = self._data_destaque is not None and data_botao == self._data_destaque
                eh_hoje = data_botao == hoje
                if eh_selecionada:
                    fg_cor = CORES["primaria"]
                    hover_cor = CORES["primariaHover"]
                    texto_cor = CORES.get("textoInverso", "#FFFFFF")
                elif eh_hoje:
                    fg_cor = CORES.get("infoFundo", CORES["borda"])
                    hover_cor = CORES["primariaHover"]
                    texto_cor = CORES["primaria"]
                else:
                    fg_cor = CORES["borda"]
                    hover_cor = CORES["zebraEscura"]
                    texto_cor = CORES["texto"]
                ctk.CTkButton(
                    grade,
                    text=str(dia),
                    width=34,
                    height=30,
                    fg_color=fg_cor,
                    hover_color=hover_cor,
                    text_color=texto_cor,
                    command=lambda d=data_botao: self._selecionar_data(d),
                ).grid(row=linha, column=coluna, padx=2, pady=2)

    def _mudar_mes(self, delta: int) -> None:
        mes = self._mes_visivel.month + delta
        ano = self._mes_visivel.year
        if mes < 1:
            mes = 12
            ano -= 1
        elif mes > 12:
            mes = 1
            ano += 1
        dia = min(self._mes_visivel.day, calendar.monthrange(ano, mes)[1])
        self._mes_visivel = date(ano, mes, dia)
        if self._popup is not None and janela_ui_ainda_ativa(self._popup):
            self._montar_calendario(self._popup)

    def _selecionar_data(self, valor: date) -> None:
        self.definir_data(valor)
        if self._popup is not None:
            try:
                self._popup.grab_release()
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None
        if self._ao_mudar is not None:
            self._ao_mudar()


def montar_campo_data_calendario(
    pai: ctk.CTkFrame,
    *,
    valor_inicial: date | None = None,
    largura_entrada: int = 118,
    ao_mudar: Callable[[], None] | None = None,
) -> CampoDataCalendario:
    return CampoDataCalendario(
        pai,
        valor_inicial=valor_inicial,
        largura_entrada=largura_entrada,
        ao_mudar=ao_mudar,
    )
