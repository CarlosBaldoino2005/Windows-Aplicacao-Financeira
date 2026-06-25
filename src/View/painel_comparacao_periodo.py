"""Painel visual para resultado da comparacao entre dois pontos no grafico."""
import customtkinter as ctk

from src.Tool.dividendos_helper import analisar_dividendos_periodo
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
        "comparar_cdi": True,
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
    *,
    intraday: bool = False,
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

    if intraday:
        acao["total_dividendos_carteira"] = 0.0
        acao["resultado_com_dividendos"] = resultado_total
        acao["lucro_com_dividendos"] = resultado_total >= 0
    elif not simbolo.endswith("-USD"):
        resumo_div = analisar_dividendos_periodo(
            simbolo,
            str(p_ini["data"]),
            str(p_fim["data"]),
            moeda,
        )
        acao.update(resumo_div)
        total_div_por_acao = float(acao.get("total_dividendos_periodo") or 0)
        total_div_carteira = round(total_div_por_acao * qtd, 2)
        acao["total_dividendos_carteira"] = total_div_carteira
        acao["resultado_com_dividendos"] = round(resultado_total + total_div_carteira, 2)
        acao["lucro_com_dividendos"] = acao["resultado_com_dividendos"] >= 0
    else:
        acao["total_dividendos_carteira"] = 0.0
        acao["resultado_com_dividendos"] = resultado_total
        acao["lucro_com_dividendos"] = resultado_total >= 0

    payload = {
        "tipo": "completo",
        "data_inicio": p_ini["data"],
        "data_fim": p_fim["data"],
        "pregoes": abs(indice_fim - indice_inicio) + 1,
        "indice_inicio": indice_inicio,
        "indice_fim": indice_fim,
        "acoes": [acao],
        "melhor_desempenho": codigo,
        "pior_desempenho": codigo,
        "uma_acao": True,
    }
    if intraday:
        payload["rotulo_inicio"] = "Horario inicial"
        payload["rotulo_fim"] = "Horario final"
        payload["rotulo_contagem"] = "Pontos no intervalo"
    elif moeda == "BRL" and qtd > 0:
        payload["comparar_cdi"] = True
    return payload


def enriquecer_comparacao_com_cdi(payload: dict) -> dict:
    """Adiciona rendimento em 100% CDI (grafico unico em R$ ou comparacao em indice 100)."""
    if not payload.get("comparar_cdi") or payload.get("tipo") != "completo":
        return payload

    from src.Service.cdi_servico import CdiServico

    data_ini = str(payload.get("data_inicio", ""))
    data_fim = str(payload.get("data_fim", ""))
    servico = CdiServico()

    if payload.get("uma_acao"):
        acoes = payload.get("acoes") or []
        if not acoes:
            return payload
        acao = acoes[0]
        valor_ini = acao.get("valor_inicio_total")
        if valor_ini is None or acao.get("moeda") != "BRL":
            return payload

        resultado = servico.calcular_rendimento(float(valor_ini), data_ini, data_fim)
        if resultado is None:
            acao["cdi_erro"] = "Nao foi possivel calcular o CDI para este periodo."
            return payload

        acao["cdi_valor_fim"] = resultado["valor_fim"]
        acao["cdi_resultado"] = resultado["rendimento"]
        acao["cdi_pct"] = resultado["rendimento_pct"]
        acao["cdi_dias_uteis"] = resultado["dias_uteis"]
        acao["cdi_lucro"] = resultado["rendimento"] >= 0
        resultado_acao = float(acao.get("resultado_total") or 0)
        acao["cdi_diferenca_acao"] = round(resultado_acao - resultado["rendimento"], 2)
        return payload

    resultado = servico.calcular_rendimento(100.0, data_ini, data_fim)
    if resultado is None:
        payload["cdi_erro"] = "Nao foi possivel calcular o CDI para este periodo."
        return payload

    pct_cdi = float(resultado["rendimento_pct"])
    payload["cdi_indice_inicio"] = 100.0
    payload["cdi_indice_fim"] = resultado["valor_fim"]
    payload["cdi_pct"] = pct_cdi
    payload["cdi_lucro"] = pct_cdi >= 0
    payload["cdi_dias_uteis"] = resultado["dias_uteis"]

    for acao in payload.get("acoes") or []:
        acao["cdi_pct_periodo"] = pct_cdi
        acao["cdi_diferenca_pct"] = round(float(acao["variacao_indice_pct"]) - pct_cdi, 2)

    return payload


class PainelComparacaoPeriodo:
    """Renderiza cards e tabela resumo no topo da janela de comparacao."""

    _modo_amplo: bool = False

    @staticmethod
    def _tamanho_fonte(base: int) -> int:
        return base + (3 if PainelComparacaoPeriodo._modo_amplo else 0)

    @staticmethod
    def _largura_texto(base: int) -> int:
        return base + (220 if PainelComparacaoPeriodo._modo_amplo else 0)

    @staticmethod
    def exibir(container: ctk.CTkFrame, dados: dict, modo_amplo: bool = False) -> None:
        PainelComparacaoPeriodo._modo_amplo = modo_amplo
        try:
            for widget in container.winfo_children():
                widget.destroy()

            tipo = dados.get("tipo", "instrucao")

            if tipo == "instrucao":
                PainelComparacaoPeriodo._exibir_instrucao(container, dados.get("texto", ""))
            elif tipo == "parcial":
                PainelComparacaoPeriodo._exibir_parcial(container, dados)
            elif tipo == "completo":
                PainelComparacaoPeriodo._exibir_completo(container, dados)
        finally:
            PainelComparacaoPeriodo._modo_amplo = False

    @staticmethod
    def _exibir_instrucao(container: ctk.CTkFrame, texto: str) -> None:
        ctk.CTkLabel(
            container,
            text=texto,
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(12)),
            text_color=CORES["texto"],
            fg_color=CORES.get("destaqueInstrucao", CORES["erroFundo"]),
            corner_radius=8,
            wraplength=PainelComparacaoPeriodo._largura_texto(1050),
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
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(13), weight="bold"),
            text_color=CORES["primaria"],
            fg_color=CORES.get("destaqueParcial", CORES["infoFundo"]),
            corner_radius=8,
        ).pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(
            container,
            text=dados.get(
                "texto_segundo_clique",
                "Clique no segundo ponto no grafico (data final).",
            ),
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(12)),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=8, pady=(0, 6))

    @staticmethod
    def _exibir_completo(container: ctk.CTkFrame, dados: dict) -> None:
        faixa_periodo = ctk.CTkFrame(
            container, fg_color=CORES.get("destaquePeriodo", CORES["erroFundo"]), corner_radius=10
        )
        faixa_periodo.pack(fill="x", padx=4, pady=(4, 8))

        grid_periodo = ctk.CTkFrame(faixa_periodo, fg_color="transparent")
        grid_periodo.pack(fill="x", padx=12, pady=10)
        for col in range(3):
            grid_periodo.grid_columnconfigure(col, weight=1)

        PainelComparacaoPeriodo._celula_resumo(
            grid_periodo, 0, dados.get("rotulo_inicio", "Data inicial"), dados["data_inicio"], CORES["texto"]
        )
        PainelComparacaoPeriodo._celula_resumo(
            grid_periodo, 1, dados.get("rotulo_fim", "Data final"), dados["data_fim"], CORES["texto"]
        )
        PainelComparacaoPeriodo._celula_resumo(
            grid_periodo,
            2,
            dados.get("rotulo_contagem", "Pregoes no intervalo"),
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
                font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(11), weight="bold"),
                text_color=CORES["textoSecundario"],
            ).pack(anchor="w", padx=8, pady=(0, 6))
            PainelComparacaoPeriodo._exibir_faixa_cdi_periodo(container, dados)

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
            celula,
            text=titulo,
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(11)),
            text_color=CORES["textoSecundario"],
        ).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(
            celula,
            text=valor,
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(13), weight="bold"),
            text_color=cor_valor,
            wraplength=PainelComparacaoPeriodo._largura_texto(280),
            justify="left",
        ).pack(anchor="w", padx=10, pady=(2, 10))

    @staticmethod
    def _card_acao(pai: ctk.CTkFrame, acao: dict, linha: int, coluna: int) -> None:
        pct = acao["variacao_indice_pct"]
        cor_pct = CORES["sucesso"] if pct >= 0 else CORES["erro"]
        fundo_pct = CORES["sucessoFundo"] if pct >= 0 else CORES["erroFundo"]
        sinal = "+" if pct >= 0 else ""

        card = ctk.CTkFrame(pai, fg_color=CORES["superficie"], corner_radius=10, border_width=1)
        card.grid(row=linha, column=coluna, padx=6, pady=6, sticky="nsew")

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(
            topo,
            text=acao["codigo"],
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(16), weight="bold"),
            text_color=CORES["texto"],
        ).pack(side="left")
        ctk.CTkLabel(
            topo,
            text=f"{sinal}{pct:.2f}%",
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(14), weight="bold"),
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
            PainelComparacaoPeriodo._linha_vs_cdi_indice(card, acao)

        if acao.get("quantidade_cotas"):
            qtd = int(acao["quantidade_cotas"])
            PainelComparacaoPeriodo._linha_metrica(card, "Quantidade de acoes", f"{qtd:,}".replace(",", "."))

            if acao.get("modo_simulacao") == "valor" and acao.get("valor_investimento_informado") is not None:
                PainelComparacaoPeriodo._linha_metrica(
                    card,
                    "Valor informado",
                    formatar_moeda(float(acao["valor_investimento_informado"]), moeda),
                )
                if acao.get("valor_sobra_compra") is not None and float(acao["valor_sobra_compra"]) > 0:
                    PainelComparacaoPeriodo._linha_metrica(
                        card,
                        "Sobra (nao compra acao fracionada)",
                        formatar_moeda(float(acao["valor_sobra_compra"]), moeda),
                        CORES["textoSecundario"],
                    )

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
            if acao.get("resultado_total") is not None and acao.get("resultado_com_dividendos") is None:
                res = float(acao["resultado_total"])
                lucro = acao.get("lucro", res >= 0)
                rotulo_res = "Lucro" if lucro else "Prejuizo"
                PainelComparacaoPeriodo._linha_metrica(
                    card,
                    rotulo_res,
                    formatar_moeda(abs(res), moeda),
                    CORES["sucesso"] if lucro else CORES["erro"],
                )

            PainelComparacaoPeriodo._exibir_bloco_cdi(card, acao, moeda)

        PainelComparacaoPeriodo._exibir_bloco_dividendos(card, acao, moeda)

        if acao.get("quantidade_cotas") and acao.get("resultado_total") is not None:
            PainelComparacaoPeriodo._exibir_resumo_total_periodo(card, acao, moeda)

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
                if acao.get("preco_inicio") is not None and acao.get("preco_fim") is not None:
                    lucro_acao = float(acao["preco_fim"]) - float(acao["preco_inicio"])
                    lucro_preco = lucro_acao >= 0
                    rotulo_valor = (
                        "Lucro em valor (por acao)"
                        if lucro_preco
                        else "Prejuizo em valor (por acao)"
                    )
                    sinal_valor = "+" if lucro_preco else "-"
                    PainelComparacaoPeriodo._linha_metrica(
                        card,
                        rotulo_valor,
                        f"{sinal_valor} {formatar_moeda(abs(lucro_acao), moeda)}",
                        CORES["sucesso"] if lucro_preco else CORES["erro"],
                    )

        if somente_preco and acao.get("volume_inicio") is not None:
            vol_ini = f"{int(acao['volume_inicio']):,}".replace(",", ".")
            vol_fim = acao.get("volume_fim")
            vol_fim_txt = f"{int(vol_fim):,}".replace(",", ".") if vol_fim is not None else "—"
            PainelComparacaoPeriodo._linha_metrica(card, "Volume", f"{vol_ini}  →  {vol_fim_txt}")

    @staticmethod
    def _exibir_bloco_dividendos(card: ctk.CTkFrame, acao: dict, moeda: str) -> None:
        if acao.get("codigo", "").endswith("-USD"):
            return
        if not acao.get("texto_resumo") and acao.get("ultimo_dividendo_global_valor") is None:
            return

        bloco = ctk.CTkFrame(
            card,
            fg_color=CORES.get("destaqueDividendo", CORES.get("infoFundo", CORES["fundo"])),
            corner_radius=8,
        )
        bloco.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            bloco,
            text="Dividendos no periodo",
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(12), weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=10, pady=(8, 4))

        if acao.get("houve_dividendo_no_periodo"):
            qtd = max(1, int(acao.get("quantidade_cotas") or 1))
            qtd_texto = f"{qtd:,} acoes".replace(",", ".")
            for item in acao.get("dividendos_no_periodo") or []:
                valor_acao = float(item.valor_por_cota)
                valor_pago = round(valor_acao * qtd, 2)
                PainelComparacaoPeriodo._linha_metrica(
                    bloco,
                    item.data_pagamento,
                    "",
                    CORES["texto"],
                )
                PainelComparacaoPeriodo._linha_metrica(
                    bloco,
                    "Valor por acao",
                    formatar_moeda(valor_acao, moeda),
                    CORES["sucesso"],
                    indentar=True,
                )
                PainelComparacaoPeriodo._linha_metrica(
                    bloco,
                    qtd_texto,
                    formatar_moeda(valor_pago, moeda),
                    CORES["sucesso"],
                    indentar=True,
                )
            total = float(acao.get("total_dividendos_periodo") or 0)
            if total > 0:
                total_carteira = float(acao.get("total_dividendos_carteira") or round(total * qtd, 2))
                PainelComparacaoPeriodo._linha_metrica(
                    bloco,
                    "Total por acao no periodo",
                    formatar_moeda(total, moeda),
                    CORES["sucesso"],
                )
                PainelComparacaoPeriodo._linha_metrica(
                    bloco,
                    f"Total pago ({qtd_texto})",
                    formatar_moeda(total_carteira, moeda),
                    CORES["sucesso"],
                )
        else:
            data_ult = acao.get("ultimo_dividendo_data") or acao.get("ultimo_dividendo_global_data")
            valor_ult = acao.get("ultimo_dividendo_valor")
            if valor_ult is None:
                valor_ult = acao.get("ultimo_dividendo_global_valor")
            if data_ult and valor_ult is not None:
                PainelComparacaoPeriodo._linha_metrica(
                    bloco,
                    "Sem pagamento no periodo",
                    "Nenhum dividendo neste intervalo",
                    CORES["aviso"],
                )
                PainelComparacaoPeriodo._linha_metrica(
                    bloco,
                    "Ultimo dividendo pago",
                    f"{data_ult} — {formatar_moeda(float(valor_ult), moeda)} por acao",
                    CORES["texto"],
                )
            else:
                texto = acao.get("texto_resumo") or "Dividendos indisponiveis."
                ctk.CTkLabel(
                    bloco,
                    text=texto,
                    font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(11)),
                    text_color=CORES["textoSecundario"],
                    wraplength=PainelComparacaoPeriodo._largura_texto(420),
                    justify="left",
                ).pack(anchor="w", padx=10, pady=(0, 8))

    @staticmethod
    def _exibir_resumo_total_periodo(card: ctk.CTkFrame, acao: dict, moeda: str) -> None:
        resultado_preco = float(acao.get("resultado_total") or 0)
        total_div = float(acao.get("total_dividendos_carteira") or 0)
        resultado_total = float(acao.get("resultado_com_dividendos", resultado_preco + total_div))
        lucro_total = acao.get("lucro_com_dividendos", resultado_total >= 0)

        bloco = ctk.CTkFrame(
            card,
            fg_color=CORES.get("destaqueResumo", CORES["superficie"]),
            corner_radius=8,
            border_width=1,
            border_color=CORES["primaria"],
        )
        bloco.pack(fill="x", padx=10, pady=(8, 10))

        ctk.CTkLabel(
            bloco,
            text="Resumo total no periodo",
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(12), weight="bold"),
            text_color=CORES["texto"],
        ).pack(anchor="w", padx=10, pady=(8, 4))

        rotulo_preco = "Valorizacao" if resultado_preco >= 0 else "Desvalorizacao"
        cor_preco = CORES["sucesso"] if resultado_preco >= 0 else CORES["erro"]
        PainelComparacaoPeriodo._linha_metrica(
            bloco,
            rotulo_preco,
            formatar_moeda(abs(resultado_preco), moeda),
            cor_preco,
        )
        PainelComparacaoPeriodo._linha_metrica(
            bloco,
            "Dividendos recebidos",
            formatar_moeda(total_div, moeda),
            CORES["sucesso"] if total_div > 0 else CORES["textoSecundario"],
        )

        sinal = "+" if resultado_total >= 0 else "-"
        rotulo_final = "Lucro total" if lucro_total else "Prejuizo total"
        cor_final = CORES["sucesso"] if lucro_total else CORES["erro"]
        PainelComparacaoPeriodo._linha_metrica(
            bloco,
            rotulo_final,
            f"{sinal} {formatar_moeda(abs(resultado_total), moeda)}",
            cor_final,
        )

        ctk.CTkLabel(
            bloco,
            text=(
                "Valorizacao/desvalorizacao da acao + dividendos pagos no periodo "
                "(com base na quantidade informada)."
            ),
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(10)),
            text_color=CORES["textoSecundario"],
            wraplength=PainelComparacaoPeriodo._largura_texto(420),
            justify="left",
        ).pack(anchor="w", padx=10, pady=(2, 8))

    @staticmethod
    def _exibir_faixa_cdi_periodo(container: ctk.CTkFrame, dados: dict) -> None:
        faixa = ctk.CTkFrame(container, fg_color=CORES.get("destaqueCdi", CORES["avisoFundo"]), corner_radius=8)
        faixa.pack(fill="x", padx=4, pady=(0, 8))

        if dados.get("cdi_carregando"):
            texto = "100% CDI no periodo: calculando..."
            cor = CORES["textoSecundario"]
        elif dados.get("cdi_erro"):
            texto = dados["cdi_erro"]
            cor = CORES["textoSecundario"]
        elif dados.get("cdi_pct") is not None:
            pct = float(dados["cdi_pct"])
            indice_fim = float(dados.get("cdi_indice_fim") or 100)
            sinal = "+" if pct >= 0 else ""
            texto = (
                f"100% CDI no periodo: indice {dados.get('cdi_indice_inicio', 100):.1f}  →  "
                f"{indice_fim:.2f} ({sinal}{pct:.2f}%)"
            )
            cor = CORES["sucesso"] if pct >= 0 else CORES["erro"]
        else:
            return

        ctk.CTkLabel(
            faixa,
            text=texto,
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(12), weight="bold"),
            text_color=cor,
            wraplength=PainelComparacaoPeriodo._largura_texto(1000),
            justify="left",
        ).pack(anchor="w", padx=12, pady=10)

    @staticmethod
    def _linha_vs_cdi_indice(card: ctk.CTkFrame, acao: dict) -> None:
        if acao.get("cdi_diferenca_pct") is None:
            return
        diff = float(acao["cdi_diferenca_pct"])
        pct_cdi = float(acao.get("cdi_pct_periodo") or 0)
        if diff > 0:
            texto = f"{diff:+.2f} p.p. acima do CDI ({pct_cdi:+.2f}% no periodo)"
            cor = CORES["sucesso"]
        elif diff < 0:
            texto = f"{diff:.2f} p.p. abaixo do CDI ({pct_cdi:+.2f}% no periodo)"
            cor = CORES["erro"]
        else:
            texto = f"Empate com CDI ({pct_cdi:+.2f}% no periodo)"
            cor = CORES["textoSecundario"]
        PainelComparacaoPeriodo._linha_metrica(card, "Acao x CDI", texto, cor)

    @staticmethod
    def _exibir_bloco_cdi(card: ctk.CTkFrame, acao: dict, moeda: str) -> None:
        if acao.get("cdi_carregando"):
            PainelComparacaoPeriodo._linha_metrica(card, "100% CDI (mesmo valor)", "Calculando...")
            return
        if acao.get("cdi_erro"):
            PainelComparacaoPeriodo._linha_metrica(
                card,
                "100% CDI",
                acao["cdi_erro"],
                CORES["textoSecundario"],
            )
            return
        if acao.get("cdi_valor_fim") is None:
            return

        moeda_cdi = "BRL"
        PainelComparacaoPeriodo._linha_metrica(
            card,
            "Valor final em 100% CDI",
            formatar_moeda(float(acao["cdi_valor_fim"]), moeda_cdi),
        )
        res_cdi = float(acao.get("cdi_resultado") or 0)
        lucro_cdi = acao.get("cdi_lucro", res_cdi >= 0)
        PainelComparacaoPeriodo._linha_metrica(
            card,
            "Rendimento CDI",
            formatar_moeda(abs(res_cdi), moeda_cdi),
            CORES["sucesso"] if lucro_cdi else CORES["erro"],
        )
        if acao.get("cdi_pct") is not None:
            pct_cdi = float(acao["cdi_pct"])
            sinal_cdi = "+" if pct_cdi >= 0 else ""
            PainelComparacaoPeriodo._linha_metrica(
                card,
                "% CDI no periodo",
                f"{sinal_cdi}{pct_cdi:.2f}%",
                CORES["sucesso"] if pct_cdi >= 0 else CORES["erro"],
            )
        if acao.get("cdi_diferenca_acao") is not None:
            diff = float(acao["cdi_diferenca_acao"])
            if diff > 0:
                texto_diff = (
                    f"Acao rendeu {formatar_moeda(diff, moeda)} a mais que 100% CDI"
                )
                cor_diff = CORES["sucesso"]
            elif diff < 0:
                texto_diff = (
                    f"CDI rendeu {formatar_moeda(abs(diff), moeda_cdi)} a mais que a acao"
                )
                cor_diff = CORES["erro"]
            else:
                texto_diff = "Empate com 100% CDI no periodo"
                cor_diff = CORES["textoSecundario"]
            PainelComparacaoPeriodo._linha_metrica(card, "Acao x CDI", texto_diff, cor_diff)

    @staticmethod
    def _linha_metrica(
        pai: ctk.CTkFrame,
        rotulo: str,
        valor: str,
        cor_valor: str | None = None,
        *,
        indentar: bool = False,
    ) -> None:
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=10, pady=3)
        largura_rotulo = 140 if PainelComparacaoPeriodo._modo_amplo else 110
        padx_rotulo = 18 if indentar else 0
        ctk.CTkLabel(
            linha,
            text=rotulo,
            font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(11)),
            text_color=CORES["textoSecundario"],
            width=largura_rotulo,
            anchor="w",
        ).pack(side="left", padx=(padx_rotulo, 0))
        if valor:
            ctk.CTkLabel(
                linha,
                text=valor,
                font=ctk.CTkFont(size=PainelComparacaoPeriodo._tamanho_fonte(12), weight="bold"),
                text_color=cor_valor or CORES["texto"],
                anchor="w",
                justify="left",
            ).pack(side="left", fill="x", expand=True)
