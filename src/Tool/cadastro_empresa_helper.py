"""Montagem de dados cadastrais da empresa a partir do Yahoo Finance."""
from __future__ import annotations

from src.Model.detalhes_acao import DetalhesAcao


def preencher_cadastro_empresa_de_yahoo(detalhes: DetalhesAcao, info: dict) -> None:
    """Preenche endereco, contatos e dirigentes disponiveis no perfil Yahoo."""
    detalhes.endereco_linha1 = str(info.get("address1") or "").strip()
    detalhes.endereco_linha2 = str(info.get("address2") or "").strip()
    detalhes.cidade = str(info.get("city") or "").strip()
    detalhes.estado = str(info.get("state") or "").strip()
    detalhes.cep = str(info.get("zip") or "").strip()
    detalhes.telefone = str(info.get("phone") or "").strip()
    detalhes.site_ri = str(info.get("irWebsite") or "").strip()
    detalhes.bolsa = str(
        info.get("fullExchangeName") or info.get("exchange") or ""
    ).strip()

    detalhes.dirigentes.clear()
    for dirigente in info.get("companyOfficers") or []:
        if not isinstance(dirigente, dict):
            continue
        nome = str(dirigente.get("name") or "").strip()
        cargo = str(dirigente.get("title") or "").strip()
        if nome:
            detalhes.dirigentes.append((nome, cargo or "—"))

    detalhes.filiais.clear()
    # Yahoo Finance nao lista filiais; guardamos unidades listadas em outros campos, se existirem.
    for chave in ("subsidiaries", "companyBranches", "branches"):
        valor = info.get(chave)
        if isinstance(valor, list):
            for item in valor:
                texto = str(item).strip()
                if texto:
                    detalhes.filiais.append(texto)
        elif isinstance(valor, str) and valor.strip():
            detalhes.filiais.append(valor.strip())


def montar_endereco_completo(dados: DetalhesAcao) -> str:
    """Junta linhas de endereco, cidade, estado e CEP em um texto legivel."""
    linhas_endereco: list[str] = []
    if dados.endereco_linha1:
        linhas_endereco.append(dados.endereco_linha1)
    if dados.endereco_linha2:
        linhas_endereco.append(dados.endereco_linha2)

    cidade_uf = ""
    if dados.cidade and dados.estado:
        cidade_uf = f"{dados.cidade} — {dados.estado}"
    elif dados.cidade:
        cidade_uf = dados.cidade
    elif dados.estado:
        cidade_uf = dados.estado

    if cidade_uf:
        linhas_endereco.append(cidade_uf)
    if dados.cep:
        linhas_endereco.append(f"CEP {dados.cep}")
    if dados.pais:
        linhas_endereco.append(dados.pais)

    return "\n".join(linhas_endereco) if linhas_endereco else ""
