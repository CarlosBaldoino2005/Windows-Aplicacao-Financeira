"""Janela dedicada para comparar desempenho de ate 6 acoes."""
from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from src.Controller.controlador_mercado import ControladorMercado
from src.Tool.janela_helper import executar_em_thread, configurar_janela_maximizada
from src.Tool.dividendos_helper import eh_pagadora_dividendos
from src.Tool.fiis_helper import eh_fii
from src.Tool.validadores import normalizar_simbolo, normalizar_simbolo_cripto
from src.View.placeholders_ui import (
    PLACEHOLDER_CODIGO_ACAO,
    PLACEHOLDER_CODIGO_CRIPTO,
    PLACEHOLDER_COMPARAR_BUSCA_ACAO,
    PLACEHOLDER_COMPARAR_BUSCA_CRIPTO,
)
from src.View.janela_grafico_comparacao import JanelaGraficoComparacao
from src.View.tema import CORES

PERIODOS = [
    ("dia", "Dia"),
    ("semana", "Semana"),
    ("mes", "Mes"),
    ("trimestre", "Trimestre"),
    ("semestre", "Semestre"),
    ("ano", "Ano"),
    ("personalizado", "Personalizado"),
]


class JanelaCompararAcoes(ctk.CTkToplevel):
    """Seleciona acoes e abre o grafico comparativo em tela cheia."""

    def __init__(
        self,
        pai: ctk.CTk,
        controlador: ControladorMercado,
        modo_cripto: bool = False,
        modo_somente_dividendos: bool = False,
        modo_somente_fiis: bool = False,
    ) -> None:
        super().__init__(pai)
        self._controlador = controlador
        self._modo_cripto = modo_cripto
        self._modo_somente_dividendos = modo_somente_dividendos
        self._modo_somente_fiis = modo_somente_fiis
        self._simbolos: list[str] = []
        self._janela_grafico: JanelaGraficoComparacao | None = None

        self.title("Comparar criptomoedas" if modo_cripto else "Comparar acoes")
        self.configure(fg_color=CORES["fundo"])
        self.minsize(900, 620)

        self._montar_interface()
        configurar_janela_maximizada(self)
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        self.focus_force()

    def _ao_fechar(self) -> None:
        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass
        self.destroy()

    def _montar_interface(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=0)
        cabecalho.pack(fill="x")

        ctk.CTkLabel(
            cabecalho,
            text="Comparar criptomoedas" if self._modo_cripto else "Comparar acoes",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            cabecalho,
            text=(
                "Adicione de 2 a 6 criptomoedas, escolha o periodo e abra o grafico comparativo."
                if self._modo_cripto
                else (
                    "Adicione de 2 a 6 acoes, escolha o periodo e abra o grafico com indice base 100 "
                    "e linha de referencia do CDI."
                )
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=860,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        form = ctk.CTkFrame(self, fg_color=CORES["superficie"], corner_radius=12)
        form.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        linha_busca = ctk.CTkFrame(form, fg_color="transparent")
        linha_busca.pack(fill="x", padx=12, pady=(12, 4))

        rotulo_busca = "Pesquisar cripto" if self._modo_cripto else "Pesquisar acao"
        ctk.CTkLabel(linha_busca, text=rotulo_busca).pack(side="left", padx=(0, 8))
        self._entrada_busca = ctk.CTkEntry(
            linha_busca,
            width=280,
            placeholder_text=(
                PLACEHOLDER_COMPARAR_BUSCA_CRIPTO
                if self._modo_cripto
                else PLACEHOLDER_COMPARAR_BUSCA_ACAO
            ),
        )
        self._entrada_busca.pack(side="left", padx=(0, 8))
        self._entrada_busca.bind("<Return>", lambda _e: self._pesquisar_acoes())

        ctk.CTkButton(
            linha_busca,
            text="Buscar",
            command=self._pesquisar_acoes,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left")

        self._frame_resultados_busca = ctk.CTkScrollableFrame(
            form, height=140, fg_color=CORES["fundo"], label_text="Resultados da busca"
        )
        self._frame_resultados_busca.pack(fill="x", padx=12, pady=(4, 8))

        linha_codigo = ctk.CTkFrame(form, fg_color="transparent")
        linha_codigo.pack(fill="x", padx=12, pady=(4, 8))

        ctk.CTkLabel(linha_codigo, text="Ou digite o codigo").pack(side="left", padx=(0, 8))
        self._entrada_codigo = ctk.CTkEntry(
            linha_codigo,
            width=120,
            placeholder_text=(
                PLACEHOLDER_CODIGO_CRIPTO if self._modo_cripto else PLACEHOLDER_CODIGO_ACAO
            ),
        )
        self._entrada_codigo.pack(side="left", padx=(0, 8))
        self._entrada_codigo.bind("<Return>", lambda _e: self._adicionar_por_codigo())

        ctk.CTkButton(
            linha_codigo,
            text="Adicionar",
            command=self._adicionar_por_codigo,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(side="left")

        self._label_chips = ctk.CTkLabel(
            form,
            text=(
                "Criptos selecionadas: (nenhuma)"
                if self._modo_cripto
                else "Acoes selecionadas: (nenhuma)"
            ),
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=860,
            justify="left",
        )
        self._label_chips.pack(anchor="w", padx=12, pady=(4, 4))

        ctk.CTkButton(
            form,
            text="Limpar lista",
            width=100,
            command=self._limpar_lista,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
        ).pack(anchor="w", padx=12, pady=(0, 12))

        linha_periodo = ctk.CTkFrame(form, fg_color="transparent")
        linha_periodo.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(linha_periodo, text="Periodo").pack(side="left", padx=(0, 8))
        self._combo_periodo = ctk.CTkComboBox(
            linha_periodo,
            values=[p[1] for p in PERIODOS],
            width=140,
            command=self._alternar_datas,
        )
        self._combo_periodo.set("Mes")
        self._combo_periodo.pack(side="left", padx=(0, 16))

        ctk.CTkButton(
            linha_periodo,
            text="Abrir grafico comparativo",
            command=self._executar_comparacao,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            height=36,
        ).pack(side="left")

        self._frame_datas = ctk.CTkFrame(form, fg_color="transparent")
        ctk.CTkLabel(self._frame_datas, text="Inicio (dd/mm/aaaa)").pack(side="left", padx=(12, 4))
        self._entrada_inicio = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_inicio.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(self._frame_datas, text="Fim").pack(side="left")
        self._entrada_fim = ctk.CTkEntry(self._frame_datas, width=110)
        self._entrada_fim.pack(side="left", padx=(0, 12))

        self._label_status = ctk.CTkLabel(
            form,
            text="Selecione as acoes e clique em Abrir grafico comparativo.",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
            wraplength=860,
            justify="left",
        )
        self._label_status.pack(anchor="w", padx=12, pady=(8, 12))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            rodape,
            text="Fechar",
            command=self._ao_fechar,
            fg_color=CORES["primaria"],
            hover_color=CORES["primariaHover"],
            width=120,
        ).pack(side="right")

    def _periodo_chave(self) -> str:
        rotulo = self._combo_periodo.get()
        for chave, nome in PERIODOS:
            if nome == rotulo:
                return chave
        return "mes"

    def _alternar_datas(self, _valor=None) -> None:
        if self._periodo_chave() == "personalizado":
            self._frame_datas.pack(fill="x", padx=12, pady=(0, 8))
        else:
            self._frame_datas.pack_forget()

    def _executar_em_thread(self, funcao, ao_concluir) -> None:
        executar_em_thread(self, funcao, ao_concluir)

    def _codigo_exibicao(self, simbolo: str) -> str:
        if self._modo_cripto:
            return simbolo.replace("-USD", "")
        return simbolo.replace(".SA", "")

    def _validar_empresa_dividendos(self, simbolo: str) -> bool:
        if not self._modo_somente_dividendos:
            return True
        if eh_pagadora_dividendos(simbolo):
            return True
        codigo = self._codigo_exibicao(simbolo)
        messagebox.showwarning(
            "Comparar",
            f"{codigo} nao consta como pagadora de dividendos nas fontes consultadas.",
            parent=self,
        )
        return False

    def _validar_fii(self, simbolo: str) -> bool:
        if not self._modo_somente_fiis:
            return True
        if eh_fii(simbolo):
            return True
        codigo = self._codigo_exibicao(simbolo)
        messagebox.showwarning(
            "Comparar",
            f"{codigo} nao consta como fundo imobiliario (FII) nas fontes consultadas.",
            parent=self,
        )
        return False

    def _incluir_simbolo(self, simbolo: str) -> bool:
        if not simbolo:
            return False
        if not self._validar_empresa_dividendos(simbolo):
            return False
        if not self._validar_fii(simbolo):
            return False
        if simbolo in self._simbolos:
            messagebox.showinfo(
                "Comparar",
                f"{self._codigo_exibicao(simbolo)} ja esta na lista.",
                parent=self,
            )
            return False
        if len(self._simbolos) >= 6:
            limite_msg = (
                "Maximo de 6 criptomoedas por comparacao."
                if self._modo_cripto
                else "Maximo de 6 acoes por comparacao."
            )
            messagebox.showwarning("Comparar", limite_msg, parent=self)
            return False
        self._simbolos.append(simbolo)
        self._atualizar_chips()
        return True

    def _atualizar_chips(self) -> None:
        rotulo_vazio = (
            "Criptos selecionadas: (nenhuma)"
            if self._modo_cripto
            else "Acoes selecionadas: (nenhuma)"
        )
        rotulo_lista = (
            "Criptos selecionadas" if self._modo_cripto else "Acoes selecionadas"
        )
        if not self._simbolos:
            self._label_chips.configure(text=rotulo_vazio)
        else:
            texto = ", ".join(self._codigo_exibicao(s) for s in self._simbolos)
            self._label_chips.configure(text=f"{rotulo_lista}: {texto}")

    def _limpar_lista(self) -> None:
        self._simbolos.clear()
        self._atualizar_chips()

    def _limpar_resultados_busca(self) -> None:
        for widget in self._frame_resultados_busca.winfo_children():
            widget.destroy()

    def _exibir_resultados_busca(self, itens) -> None:
        self._limpar_resultados_busca()
        if not itens:
            ctk.CTkLabel(
                self._frame_resultados_busca,
                text="Nenhum resultado.",
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=4, pady=4)
            return

        for item in itens:
            linha = ctk.CTkFrame(self._frame_resultados_busca, fg_color=CORES["superficie"], corner_radius=8)
            linha.pack(fill="x", padx=4, pady=3)

            codigo = self._codigo_exibicao(item.simbolo)
            texto = f"{codigo}  —  {item.nome}  ({item.bolsa})"
            ctk.CTkLabel(
                linha,
                text=texto,
                anchor="w",
                font=ctk.CTkFont(size=12),
                text_color=CORES["texto"],
            ).pack(side="left", fill="x", expand=True, padx=8, pady=6)

            ctk.CTkButton(
                linha,
                text="Adicionar",
                width=90,
                command=lambda s=item.simbolo: self._adicionar_da_busca(s),
                fg_color=CORES["primaria"],
                hover_color=CORES["primariaHover"],
            ).pack(side="right", padx=8, pady=4)

    def _adicionar_da_busca(self, simbolo: str) -> None:
        if self._incluir_simbolo(simbolo):
            self._label_status.configure(
                text=f"{self._codigo_exibicao(simbolo)} adicionada a lista.",
                text_color=CORES["sucesso"],
            )

    def _pesquisar_acoes(self) -> None:
        termo = self._entrada_busca.get().strip()
        if not termo:
            aviso = (
                "Digite o nome ou codigo da criptomoeda (ex.: Bitcoin ou ETH)."
                if self._modo_cripto
                else "Digite o nome ou codigo da acao."
            )
            messagebox.showwarning("Buscar", aviso, parent=self)
            return

        status = (
            "Buscando criptomoedas..."
            if self._modo_cripto
            else "Buscando acoes..."
        )
        self._label_status.configure(text=status, text_color=CORES["textoSecundario"])

        def buscar():
            return self._controlador.pesquisar_acoes(termo)

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                self._limpar_resultados_busca()
                return
            itens, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                self._limpar_resultados_busca()
                return
            self._exibir_resultados_busca(itens)
            self._label_status.configure(
                text=f"{len(itens)} resultado(s). Clique em Adicionar na linha desejada.",
                text_color=CORES["sucesso"],
            )

        self._executar_em_thread(buscar, ao_concluir)

    def _normalizar_entrada(self, termo: str):
        if self._modo_cripto:
            return normalizar_simbolo_cripto(termo)
        return normalizar_simbolo(termo)

    def _adicionar_por_codigo(self) -> None:
        texto = self._entrada_codigo.get().strip()
        simbolo, erro = self._normalizar_entrada(texto)
        if erro:
            messagebox.showwarning("Comparar", erro, parent=self)
            return
        if self._incluir_simbolo(simbolo):
            self._entrada_codigo.delete(0, "end")

    def _executar_comparacao(self) -> None:
        if len(self._simbolos) < 2:
            aviso = (
                "Adicione pelo menos duas criptomoedas."
                if self._modo_cripto
                else "Adicione pelo menos duas acoes."
            )
            messagebox.showwarning("Comparar", aviso, parent=self)
            return

        periodo = self._periodo_chave()
        self._label_status.configure(text="Gerando comparacao...", text_color=CORES["textoSecundario"])

        def buscar():
            return self._controlador.comparar(
                self._simbolos,
                periodo,
                self._entrada_inicio.get(),
                self._entrada_fim.get(),
            )

        def ao_concluir(resultado, erro):
            if erro:
                self._label_status.configure(text=erro, text_color=CORES["erro"])
                messagebox.showwarning("Comparar", erro, parent=self)
                return
            dados, msg_erro = resultado
            if msg_erro:
                self._label_status.configure(text=msg_erro, text_color=CORES["erro"])
                messagebox.showwarning("Comparar", msg_erro, parent=self)
                return

            self._abrir_grafico(dados, periodo)
            status = "Grafico aberto. Voce pode gerar novamente com outro periodo."
            avisos = dados.get("avisos") or []
            if avisos:
                status += " Avisos: " + " | ".join(avisos)
            self._label_status.configure(text=status, text_color=CORES["sucesso"])

        self._executar_em_thread(buscar, ao_concluir)

    def _abrir_grafico(self, dados: dict, periodo_chave: str) -> None:
        rotulos = {chave: nome for chave, nome in PERIODOS}
        rotulo = rotulos.get(periodo_chave, periodo_chave)

        if self._janela_grafico is not None:
            try:
                if self._janela_grafico.winfo_exists():
                    self._janela_grafico._ao_fechar()
            except Exception:
                pass

        self._janela_grafico = JanelaGraficoComparacao(
            self,
            dados,
            rotulo,
            controlador=self._controlador,
        )
