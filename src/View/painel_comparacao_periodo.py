"""Painel visual para resultado da comparacao entre dois pontos no grafico."""
import customtkinter as ctk

from src.View.formatadores import formatar_moeda
from src.View.tema import CORES


def calcular_comparacao_multiplas(
    series: dict[str, list[dict]],
    simbolos: list[str],
    indice_inicio: int,
    indice_fim: int,
) -> dict:
    """Monta dados estruturados para exibir no painel."""
    primeira = series[simbolos[0]]
    acoes: list[dict] = []

    for simbolo in simbolos:
        pontos = series[simbolo]
        if indice_fim >= len(pontos) or indice_inicio >= len(pontos):
            continue

        indice_ini_val = float(pontos[indice_inicio]["indice_relativo"])
        indice_fim_val = float(pontos[indice_fim]["indice_relativo"])
        base = indice_ini_val if indice_ini_val else 100.0
        variacao_pct = ((indice_fim_val - indice_ini_val) / base) * 100
        moeda = "BRL" if simbolo.endswith(".SA") else "USD"
        preco_ini = pontos[indice_inicio].get("preco")
        preco_fim = pontos[indice_fim].get("preco")
        variacao_preco_pct = None
        if preco_ini and preco_fim and preco_ini != 0:
            variacao_preco_pct = ((float(preco_fim) - float(preco_ini)) / float(preco_ini)) * 100

        acoes.append(
            {
                "codigo": simbolo.replace(".SA", ""),
                "indice_inicio": indice_ini_val,
                "indice_fim": indice_fim_val,
                "variacao_indice_pct": round(variacao_pct, 2),
                "preco_inicio": preco_ini,
                "preco_fim": preco_fim,
                "variacao_preco_pct": round(variacao_preco_pct, 2) if variacao_preco_pct is not None else None,
                "moeda": moeda,
            }
        )

    acoes.sort(key=lambda item: item["variacao_indice_pct"], reverse=True)
    melhor = acoes[0]["codigo"] if acoes else ""
    pior = acoes[-1]["codigo"] if acoes else ""

    return {
        "tipo": "completo",
        "data_inicio": primeira[indice_inicio]["data"],
        "data_fim": primeira[indice_fim]["data"],
        "pregoes": abs(indice_fim - indice_inicio) + 1,
        "acoes": acoes,
        "melhor_desempenho": melhor,
        "pior_desempenho": pior,
    }


def payload_instrucao(texto: str) -> dict:
    return {"tipo": "instrucao", "texto": texto}


def payload_inicio_selecionado(
    data: str,
    preco: float | None = None,
    moeda: str = "BRL",
    quantidade_cotas: int | None = None,
) -> dict:
    dados = {"tipo": "parcial", "data_inicio": data}
    if preco is not None:
        dados["preco_inicio"] = preco
        dados["moeda"] = moeda
    if quantidade_cotas is not None and quantidade_cotas > 0:
        dados["quantidade_cotas"] = quantidade_cotas
        if preco is not None:
            dados["valor_inicio_total"] = round(float(preco) * quantidade_cotas, 2)
    return dados


def calcular_comparacao_acao_unica(
    pontos: list[dict],
    simbolo: str,
    moeda: str,
    indice_inicio: int,
    indice_fim: int,
    quantidade_cotas: int = 1,
) -> dict:
    """Comparacao de periodo para uma unica acao com simulacao por quantidade."""
    p_ini = pontos[indice_inicio]
    p_fim = pontos[indice_fim]
    preco_ini = float(p_ini["fechamento"])
    preco_fim = float(p_fim["fechamento"])
    base = preco_ini if preco_ini else 1.0
    variacao_pct = ((preco_fim - preco_ini) / base) * 100
    codigo = simbolo.replace(".SA", "")

    qtd = max(1, int(quantidade_cotas))
    valor_inicio_total = round(preco_ini * qtd, 2)
    valor_fim_total = round(preco_fim * qtd, 2)
    resultado_total = round(valor_fim_total - valor_inicio_total, 2)

    acao = {
        "codigo": codigo,
        "somente_preco": True,
        "preco_inicio": preco_ini,
        "preco_fim": preco_fim,
        "variacao_preco_pct": round(variacao_pct, 2),
        "variacao_indice_pct": round(variacao_pct, 2),
        "moeda": moeda,
        "volume_inicio": p_ini.get("volume"),
        "volume_fim": p_fim.get("volume"),
        "quantidade_cotas": qtd,
        "valor_inicio_total": valor_inicio_total,
        "valor_fim_total": valor_fim_total,
        "resultado_total": resultado_total,
        "lucro": resultado_total >= 0,
    }

    return {
        "tipo": "completo",
        "data_inicio": p_ini["data"],
        "data_fim": p_fim["data"],
        "pregoes": abs(indice_fim - indice_inicio) + 1,
        "acoes": [acao],
        "melhor_desempenho": codigo,
        "pior_desempenho": codigo,
        "uma_acao": True,
    }


class PainelComparacaoPeriodo:
    """Renderiza cards e tabela resumo no topo da janela de comparacao."""

    @staticmethod
    def exibir(container: ctk.CTkFrame, dados: dict) -> None:
        for widget in container.winfo_children():
            widget.destroy()

        tipo = dados.get("tipo", "instrucao")

        if tipo == "instrucao":
            PainelComparacaoPeriodo._exibir_instrucao(container, dados.get("texto", ""))
        elif tipo == "parcial":
            PainelComparacaoPeriodo._exibir_parcial(container, dados)
        elif tipo == "completo":
            PainelComparacaoPeriodo._exibir_completo(container, dados)

    @staticmethod
    def _exibir_instrucao(container: ctk.CTkFrame, texto: str) -> None:
        ctk.CTkLabel(
            container,
            text=texto,
            font=ctk.CTkFont(size=12),
            text_color=CORES["texto"],
            fg_color="#FEE2E2",
            corner_radius=8,
            wraplength=1050,
            justify="left",
        ).pack(fill="x", padx=4, pady=6)

    @staticmethod
    def _exibir_parcial(container: ctk.CTkFrame, dados: dict) -> None:
        texto = f"Inicio selecionado: {dados.get('data_inicio', '')}"
        if dados.get("preco_inicio") is not None:
            moeda = dados.get("moeda", "BRL")
            texto += f" — {formatar_moeda(float(dados['preco_inicio']), moeda)} por acao"
        if dados.get("valor_inicio_total") is not None:
            moeda = dados.get("moeda", "BRL")
            qtd = dados.get("quantidade_cotas", "")
            texto += f" | {int(qtd)} acoes = {formatar_moeda(float(dados['valor_inicio_total']), moeda)}"
        ctk.CTkLabel(
            container,
            text=texto,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=CORES["primaria"],
            fg_color="#EFF6FF",
            corner_radius=8,
        ).pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(
            container,
            text="Clique no segundo ponto no grafico (data final).",
            font=ctk.CTkFont(size=12),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=8, pady=(0, 6))

    @staticmethod
    def _exibir_completo(container: ctk.CTkFrame, dados: dict) -> None:
        faixa_periodo = ctk.CTkFrame(container, fg_color="#FEE2E2", corner_radius=10)
        faixa_periodo.pack(fill="x", padx=4, pady=(4, 8))

        grid_periodo = ctk.CTkFrame(faixa_periodo, fg_color="transparent")
        grid_periodo.pack(fill="x", padx=12, pady=10)
        for col in range(3):
            grid_periodo.grid_columnconfigure(col, weight=1)

        PainelComparacaoPeriodo._celula_resumo(
            grid_periodo, 0, "Data inicial", dados["data_inicio"], CORES["texto"]
        )
        PainelComparacaoPeriodo._celula_resumo(
            grid_periodo, 1, "Data final", dados["data_fim"], CORES["texto"]
        )
        PainelComparacaoPeriodo._celula_resumo(
            grid_periodo,
            2,
            "Pregoes no intervalo",
            str(dados["pregoes"]),
            CORES["primaria"],
        )

        if not dados.get("uma_acao"):
            ctk.CTkLabel(
                container,
                text=(
                    f"Melhor no intervalo: {dados['melhor_desempenho']}  |  "
                    f"Pior no intervalo: {dados['pior_desempenho']}  "
                    f"(ordenado da maior para a menor variacao %)"
                ),
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=8, pady=(0, 6))

        grade = ctk.CTkFrame(container, fg_color="transparent")
        grade.pack(fill="x", padx=4, pady=4)
        colunas = min(3, max(1, len(dados["acoes"])))
        for col in range(colunas):
            grade.grid_columnconfigure(col, weight=1)

        for i, acao in enumerate(dados["acoes"]):
            linha = i // colunas
            coluna = i % colunas
            PainelComparacaoPeriodo._card_acao(grade, acao, linha, coluna)

    @staticmethod
    def _celula_resumo(pai: ctk.CTkFrame, coluna: int, titulo: str, valor: str, cor_valor: str) -> None:
        celula = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=8)
        celula.grid(row=0, column=coluna, padx=6, pady=4, sticky="nsew")
        ctk.CTkLabel(
            celula, text=titulo, font=ctk.CTkFont(size=11), text_color=CORES["textoSecundario"]
        ).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(
            celula,
            text=valor,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=cor_valor,
            wraplength=280,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(2, 10))

    @staticmethod
    def _card_acao(pai: ctk.CTkFrame, acao: dict, linha: int, coluna: int) -> None:
        pct = acao["variacao_indice_pct"]
        cor_pct = CORES["sucesso"] if pct >= 0 else CORES["erro"]
        fundo_pct = "#F0FDF4" if pct >= 0 else "#FEF2F2"
        sinal = "+" if pct >= 0 else ""

        card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=10, border_width=1)
        card.grid(row=linha, column=coluna, padx=6, pady=6, sticky="nsew")

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(
            topo,
            text=acao["codigo"],
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")
        ctk.CTkLabel(
            topo,
            text=f"{sinal}{pct:.2f}%",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=cor_pct,
            fg_color=fundo_pct,
            corner_radius=6,
            width=80,
        ).pack(side="right")

        somente_preco = acao.get("somente_preco", False)
        moeda = acao["moeda"]

        if not somente_preco:
            PainelComparacaoPeriodo._linha_metrica(
                card,
                "Indice relativo",
                f"{acao['indice_inicio']:.1f}  →  {acao['indice_fim']:.1f}",
            )

        if acao.get("quantidade_cotas"):
            qtd = int(acao["quantidade_cotas"])
            PainelComparacaoPeriodo._linha_metrica(card, "Quantidade de acoes", f"{qtd:,}".replace(",", "."))

            if acao.get("valor_inicio_total") is not None:
                PainelComparacaoPeriodo._linha_metrica(
                    card,
                    "Valor pago no inicio",
                    formatar_moeda(float(acao["valor_inicio_total"]), moeda),
                )
            if acao.get("valor_fim_total") is not None:
                PainelComparacaoPeriodo._linha_metrica(
                    card,
                    "Valor no final",
                    formatar_moeda(float(acao["valor_fim_total"]), moeda),
                )
            if acao.get("resultado_total") is not None:
                res = float(acao["resultado_total"])
                lucro = acao.get("lucro", res >= 0)
                rotulo_res = "Lucro" if lucro else "Prejuizo"
                PainelComparacaoPeriodo._linha_metrica(
                    card,
                    rotulo_res,
                    formatar_moeda(abs(res), moeda),
                    CORES["sucesso"] if lucro else CORES["erro"],
                )

        if acao.get("preco_inicio") is not None and acao.get("preco_fim") is not None:
            rotulo_preco = "Preco por acao" if acao.get("quantidade_cotas") else "Preco fechamento"
            if not somente_preco:
                rotulo_preco = "Preco"
            texto_preco = (
                f"{formatar_moeda(float(acao['preco_inicio']), moeda)}  →  "
                f"{formatar_moeda(float(acao['preco_fim']), moeda)}"
            )
            PainelComparacaoPeriodo._linha_metrica(card, rotulo_preco, texto_preco)
            if acao.get("variacao_preco_pct") is not None:
                pct_preco = acao["variacao_preco_pct"]
                sinal_preco = "+" if pct_preco >= 0 else ""
                rotulo_pct = "% lucro" if pct_preco >= 0 else "% prejuizo"
                PainelComparacaoPeriodo._linha_metrica(
                    card,
                    rotulo_pct,
                    f"{sinal_preco}{pct_preco:.2f}%",
                    CORES["sucesso"] if pct_preco >= 0 else CORES["erro"],
                )

        if somente_preco and acao.get("volume_inicio") is not None:
            vol_ini = f"{int(acao['volume_inicio']):,}".replace(",", ".")
            vol_fim = acao.get("volume_fim")
            vol_fim_txt = f"{int(vol_fim):,}".replace(",", ".") if vol_fim is not None else "—"
            PainelComparacaoPeriodo._linha_metrica(card, "Volume", f"{vol_ini}  →  {vol_fim_txt}")

    @staticmethod
    def _linha_metrica(
        pai: ctk.CTkFrame,
        rotulo: str,
        valor: str,
        cor_valor: str | None = None,
    ) -> None:
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(
            linha,
            text=rotulo,
            font=ctk.CTkFont(size=11),
            text_color=CORES["textoSecundario"],
            width=110,
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            linha,
            text=valor,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=cor_valor or CORES["texto"],
            anchor="w",
            justify="left",
        ).pack(side="left", fill="x", expand=True)
