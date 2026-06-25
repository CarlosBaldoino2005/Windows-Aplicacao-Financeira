"""Analise de ativo com IA generativa (OpenAI, Gemini ou Groq) para a tela Agora."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from src.Model.contexto_analise_agora import ContextoAnaliseAgora
from src.Service.provedores.util_provedor import carregar_variaveis_ambiente
from src.Tool.cotacao_dual_helper import codigo_exibicao
from src.Tool.registrador_log import RegistradorLog
from src.View.formatadores import formatar_moeda

carregar_variaveis_ambiente()

_URL_OPENAI = "https://api.openai.com/v1/chat/completions"
_URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"
_URL_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_TIMEOUT_SEGUNDOS = 90

_MODELOS_GEMINI_FALLBACK = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
)

_PROVEDORES = ("gemini", "groq", "openai")

_MENSAGEM_SISTEMA = """Voce e um assistente de analise de mercado financeiro para investidores no Brasil.
Responda sempre em portugues do Brasil, de forma clara e objetiva.

Regras:
- Use apenas os dados fornecidos pelo usuario; nao invente numeros de cotacao.
- Se faltar dado, diga explicitamente o que nao foi possivel avaliar.
- Nao garanta resultados nem prometa lucro.
- Ao final, inclua uma linha de aviso: "Conteudo informativo. Nao constitui recomendacao de investimento."

Estruture a resposta com estas secoes (titulos em negrito com **):
1. **Tendencia provavel** — alta, baixa ou lateral no curto prazo, com justificativa breve.
2. **Cenarios de preco** — otimista, base e pessimista, com valores na moeda informada.
3. **Pontos de atencao** — riscos, volatilidade ou fatores relevantes.
4. **Resumo** — uma frase conclusiva objetiva.
"""


class AnaliseIaMercadoServico:
    """Monta o prompt e consulta a API de IA configurada no .env."""

    def __init__(self) -> None:
        self._log = RegistradorLog()

    @staticmethod
    def chave_configurada() -> bool:
        return AnaliseIaMercadoServico._resolver_provedor()[0] is not None

    @staticmethod
    def provedor_configurado() -> str:
        provedor, _, rotulo = AnaliseIaMercadoServico._resolver_provedor()
        return rotulo if provedor else "Nenhum"

    @staticmethod
    def modelo_configurado() -> str:
        _, modelo, _ = AnaliseIaMercadoServico._resolver_provedor()
        return modelo or "—"

    @staticmethod
    def _resolver_provedor() -> tuple[str | None, str, str]:
        """
        Retorna (provedor, modelo, rotulo_exibicao).
        IA_PROVEDOR=auto tenta gemini, groq e openai nesta ordem.
        """
        preferido = (os.getenv("IA_PROVEDOR", "auto") or "auto").strip().lower()
        ordem = _PROVEDORES if preferido == "auto" else [preferido]

        for nome in ordem:
            if nome not in _PROVEDORES:
                continue
            if nome == "gemini" and os.getenv("GEMINI_API_KEY", "").strip():
                modelo = (
                    os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
                )
                return nome, modelo, f"Google Gemini ({modelo})"
            if nome == "groq" and os.getenv("GROQ_API_KEY", "").strip():
                modelo = (
                    os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
                    or "llama-3.3-70b-versatile"
                )
                return nome, modelo, f"Groq ({modelo})"
            if nome == "openai" and os.getenv("OPENAI_API_KEY", "").strip():
                modelo = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
                return nome, modelo, f"OpenAI ({modelo})"

        return None, "", "Nenhum"

    def analisar(self, contexto: ContextoAnaliseAgora) -> tuple[str | None, str | None]:
        provedor, modelo, rotulo = self._resolver_provedor()
        if provedor is None:
            return None, self._mensagem_sem_provedor()

        prompt_usuario = self._montar_prompt_usuario(contexto)
        if provedor == "gemini":
            return self._analisar_gemini(prompt_usuario, modelo, rotulo)
        if provedor == "groq":
            return self._analisar_openai_compat(
                prompt_usuario,
                modelo,
                rotulo,
                url=_URL_GROQ,
                chave=os.getenv("GROQ_API_KEY", "").strip(),
                header_auth=f"Bearer {os.getenv('GROQ_API_KEY', '').strip()}",
            )
        return self._analisar_openai_compat(
            prompt_usuario,
            modelo,
            rotulo,
            url=_URL_OPENAI,
            chave=os.getenv("OPENAI_API_KEY", "").strip(),
            header_auth=f"Bearer {os.getenv('OPENAI_API_KEY', '').strip()}",
        )

    def _analisar_openai_compat(
        self,
        prompt_usuario: str,
        modelo: str,
        rotulo: str,
        *,
        url: str,
        chave: str,
        header_auth: str,
    ) -> tuple[str | None, str | None]:
        corpo = {
            "model": modelo,
            "messages": [
                {"role": "system", "content": _MENSAGEM_SISTEMA},
                {"role": "user", "content": prompt_usuario},
            ],
            "temperature": 0.35,
        }
        requisicao = urllib.request.Request(
            url,
            data=json.dumps(corpo).encode("utf-8"),
            headers={
                "Authorization": header_auth,
                "Content-Type": "application/json",
                "User-Agent": "Financeiro-Desktop/1.0",
            },
            method="POST",
        )
        return self._executar_requisicao(requisicao, rotulo, self._extrair_texto_openai)

    def _analisar_gemini(
        self,
        prompt_usuario: str,
        modelo: str,
        rotulo: str,
    ) -> tuple[str | None, str | None]:
        modelos = [modelo]
        for candidato in _MODELOS_GEMINI_FALLBACK:
            if candidato not in modelos:
                modelos.append(candidato)

        ultimo_erro: str | None = None
        for indice, modelo_tentativa in enumerate(modelos):
            rotulo_tentativa = (
                rotulo
                if modelo_tentativa == modelo
                else f"Google Gemini ({modelo_tentativa})"
            )
            texto, erro = self._executar_gemini_modelo(
                prompt_usuario,
                modelo_tentativa,
                rotulo_tentativa,
            )
            if texto or erro is None:
                return texto, erro
            ultimo_erro = erro
            if not self._gemini_erro_permite_fallback(erro) or indice >= len(modelos) - 1:
                return None, erro

        return None, ultimo_erro or "Nao foi possivel consultar o Gemini."

    def _executar_gemini_modelo(
        self,
        prompt_usuario: str,
        modelo: str,
        rotulo: str,
    ) -> tuple[str | None, str | None]:
        chave = os.getenv("GEMINI_API_KEY", "").strip()
        url = (
            f"{_URL_GEMINI_BASE}/{urllib.parse.quote(modelo)}:generateContent"
            f"?key={urllib.parse.quote(chave)}"
        )
        corpo = {
            "systemInstruction": {"parts": [{"text": _MENSAGEM_SISTEMA}]},
            "contents": [{"role": "user", "parts": [{"text": prompt_usuario}]}],
            "generationConfig": {"temperature": 0.35},
        }
        requisicao = urllib.request.Request(
            url,
            data=json.dumps(corpo).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Financeiro-Desktop/1.0",
            },
            method="POST",
        )
        return self._executar_requisicao(requisicao, rotulo, self._extrair_texto_gemini)

    @staticmethod
    def _gemini_erro_permite_fallback(erro: str | None) -> bool:
        if not erro:
            return False
        texto = erro.lower()
        return any(
            trecho in texto
            for trecho in (
                "cota",
                "quota",
                "limite",
                "limit: 0",
                "limit:0",
                "429",
                "nao esta disponivel",
                "not found",
                "404",
            )
        )

    def _executar_requisicao(
        self,
        requisicao: urllib.request.Request,
        rotulo: str,
        extrator,
    ) -> tuple[str | None, str | None]:
        try:
            with urllib.request.urlopen(requisicao, timeout=_TIMEOUT_SEGUNDOS) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            mensagem = self._extrair_erro_http(exc, rotulo)
            self._log.aviso(f"Falha IA ({rotulo}) HTTP {exc.code}: {mensagem[:120]}")
            return None, mensagem
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self._log.aviso(f"Falha IA ({rotulo}): {exc}")
            return None, "Nao foi possivel conectar a API de IA. Verifique a internet e tente novamente."

        texto = extrator(dados)
        if not texto:
            return None, "A API de IA retornou resposta vazia. Tente novamente."
        return texto.strip(), None

    def _montar_prompt_usuario(self, contexto: ContextoAnaliseAgora) -> str:
        codigo = codigo_exibicao(contexto.simbolo)
        moeda = contexto.moeda or "BRL"
        linhas = [
            f"Ativo: {codigo} ({contexto.nome_ativo})",
            f"Simbolo Yahoo: {contexto.simbolo}",
        ]
        if contexto.tipo_ativo:
            linhas.append(f"Tipo: {contexto.tipo_ativo}")

        if contexto.preco_atual is not None and contexto.preco_atual > 0:
            linhas.append(f"Preco atual: {formatar_moeda(contexto.preco_atual, moeda)}")
        else:
            linhas.append("Preco atual: nao disponivel no momento")

        if contexto.variacao_valor is not None and contexto.variacao_pct is not None:
            sinal = "+" if contexto.variacao_valor >= 0 else ""
            linhas.append(
                f"Variacao do dia: {sinal}{contexto.variacao_valor:.2f} ({contexto.variacao_pct:+.2f}%)"
            )

        if contexto.metricas_resumo:
            linhas.append(f"Metricas de mercado: {contexto.metricas_resumo}")

        if contexto.quantidade_carteira is not None and contexto.quantidade_carteira > 0:
            linhas.append(
                f"Posicao na carteira do usuario: {contexto.quantidade_carteira:g} unidades"
            )
            if contexto.preco_compra_carteira is not None:
                linhas.append(
                    f"Preco medio de compra: {formatar_moeda(contexto.preco_compra_carteira, moeda)}"
                )
            if contexto.valor_investido_carteira is not None:
                linhas.append(
                    f"Valor investido: {formatar_moeda(contexto.valor_investido_carteira, moeda)}"
                )

        if contexto.alerta_preco_venda is not None:
            linhas.append(
                f"Alerta de venda configurado: {formatar_moeda(contexto.alerta_preco_venda, moeda)}"
            )
        if contexto.alerta_preco_compra is not None:
            linhas.append(
                f"Alerta de compra configurado: {formatar_moeda(contexto.alerta_preco_compra, moeda)}"
            )

        linhas.append(
            "\nCom base nesses dados, analise se o ativo tende a subir ou cair no curto prazo "
            "e estime cenarios de preco. Seja conservador quando os dados forem insuficientes."
        )
        return "\n".join(linhas)

    @staticmethod
    def _extrair_texto_openai(dados: dict) -> str:
        choices = dados.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        primeiro = choices[0]
        if not isinstance(primeiro, dict):
            return ""
        message = primeiro.get("message")
        if not isinstance(message, dict):
            return ""
        conteudo = message.get("content")
        return str(conteudo).strip() if conteudo else ""

    @staticmethod
    def _extrair_texto_gemini(dados: dict) -> str:
        candidates = dados.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            return ""
        primeiro = candidates[0]
        if not isinstance(primeiro, dict):
            return ""
        content = primeiro.get("content")
        if not isinstance(content, dict):
            return ""
        parts = content.get("parts")
        if not isinstance(parts, list) or not parts:
            return ""
        texto_partes: list[str] = []
        for parte in parts:
            if isinstance(parte, dict) and parte.get("text"):
                texto_partes.append(str(parte["text"]))
        return "\n".join(texto_partes).strip()

    @staticmethod
    def _extrair_erro_http(exc: urllib.error.HTTPError, rotulo: str) -> str:
        mensagem_api = ""
        status_erro = ""
        try:
            corpo = json.loads(exc.read().decode("utf-8"))
            erro = corpo.get("error")
            if isinstance(erro, dict):
                mensagem_api = str(erro.get("message") or "").strip()
                status_erro = str(
                    erro.get("status") or erro.get("code") or erro.get("type") or ""
                ).strip()
                codigo_erro = str(
                    erro.get("code") or erro.get("type") or erro.get("status") or ""
                ).lower()
                if "gemini" in rotulo.lower():
                    interpretado = AnaliseIaMercadoServico._interpretar_erro_gemini(
                        mensagem_api,
                        status_erro,
                        exc.code,
                        rotulo,
                    )
                    if interpretado:
                        return interpretado
                if "quota" in codigo_erro or "insufficient_quota" in codigo_erro:
                    return AnaliseIaMercadoServico._mensagem_cota_esgotada(rotulo, mensagem_api)
                if mensagem_api and "quota" in mensagem_api.lower():
                    return AnaliseIaMercadoServico._mensagem_cota_esgotada(rotulo, mensagem_api)
                if mensagem_api:
                    return mensagem_api
            mensagem_gemini = str(
                corpo.get("error", {}).get("message") or corpo.get("message") or ""
            ).strip()
            if mensagem_gemini:
                if "gemini" in rotulo.lower():
                    interpretado = AnaliseIaMercadoServico._interpretar_erro_gemini(
                        mensagem_gemini,
                        status_erro,
                        exc.code,
                        rotulo,
                    )
                    if interpretado:
                        return interpretado
                return mensagem_gemini
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            pass
        if exc.code == 401:
            return f"Chave de API invalida ou expirada ({rotulo})."
        if exc.code == 404:
            return (
                f"Modelo nao encontrado em {rotulo}.\n\n"
                "Abra Configurar IA e salve novamente para usar gemini-2.5-flash."
            )
        if exc.code == 429:
            if "gemini" in rotulo.lower():
                interpretado = AnaliseIaMercadoServico._interpretar_erro_gemini(
                    mensagem_api,
                    status_erro,
                    exc.code,
                    rotulo,
                )
                if interpretado:
                    return interpretado
            if mensagem_api and "quota" in mensagem_api.lower():
                return AnaliseIaMercadoServico._mensagem_cota_esgotada(rotulo, mensagem_api)
            return (
                f"Muitas requisicoes em sequencia em {rotulo}.\n\n"
                "Aguarde 1–2 minutos e tente de novo, ou troque o provedor em Configurar IA."
            )
        return f"Erro na API de IA ({rotulo}, HTTP {exc.code})."

    @staticmethod
    def _interpretar_erro_gemini(
        mensagem_api: str,
        status_erro: str,
        codigo_http: int,
        rotulo: str,
    ) -> str | None:
        texto = f"{mensagem_api} {status_erro}".lower()
        if not texto.strip():
            return None

        if "limit: 0" in texto or "limit:0" in texto:
            return (
                f"O Google Gemini retornou cota zero para {rotulo}.\n\n"
                "Isso pode acontecer na primeira tentativa, sem voce ter usado antes. "
                "Motivos comuns:\n"
                "• Modelo antigo (gemini-2.0-flash) sem cota no plano gratuito\n"
                "• Chave/projeto sem tier grativo ativo\n\n"
                "O que fazer:\n"
                "1. Abra Configurar IA e salve de novo (usa gemini-2.5-flash)\n"
                "2. Crie uma chave nova em https://aistudio.google.com/apikey\n"
                "3. Ou use Groq (gratuito) em Configurar IA\n\n"
                f"Detalhe: {mensagem_api or status_erro}"
            )

        if "billing" in texto or "payment" in texto:
            return (
                "A conta Google pode exigir metodo de pagamento vinculado para liberar "
                "a API Gemini, mesmo no tier gratuito.\n\n"
                "Em https://aistudio.google.com → Configuracoes → Plan information.\n\n"
                "Alternativa gratuita: use Groq em Configurar IA (https://console.groq.com)."
            )

        if codigo_http == 429 and "quota" in texto and "free_tier" in texto:
            return (
                f"Limite do plano gratuito do Gemini atingido em {rotulo}.\n\n"
                "Se voce mal usou, pode ser limite por minuto (aguarde 1–2 min) "
                "ou cota diaria da chave/projeto.\n\n"
                "Confira em AI Studio → API Keys → uso da chave.\n"
                "Alternativa: Groq em Configurar IA.\n\n"
                f"Detalhe: {mensagem_api or status_erro}"
            )

        return None

    @staticmethod
    def _mensagem_cota_esgotada(rotulo: str, detalhe_api: str = "") -> str:
        if "openai" in rotulo.lower():
            return (
                "Cota da OpenAI esgotada ou plano sem creditos.\n\n"
                "Alternativa gratuita: abra Configurar IA e use Google Gemini "
                "(chave em https://aistudio.google.com/apikey) ou Groq "
                "(https://console.groq.com)."
            )
        if "gemini" in rotulo.lower():
            interpretado = AnaliseIaMercadoServico._interpretar_erro_gemini(
                detalhe_api,
                "",
                429,
                rotulo,
            )
            if interpretado:
                return interpretado
            return (
                f"Limite do Gemini atingido em {rotulo}.\n\n"
                "Pode ser limite por minuto (aguarde e tente de novo) ou cota diaria "
                "da chave. Se foi a primeira vez, salve de novo em Configurar IA "
                "para usar gemini-2.5-flash ou teste Groq.\n\n"
                f"{('Detalhe: ' + detalhe_api) if detalhe_api else ''}"
            ).strip()
        return (
            f"Cota ou limite esgotado em {rotulo}.\n\n"
            "Aguarde a renovacao do limite ou troque o provedor em Configurar IA."
        )

    @staticmethod
    def _mensagem_sem_provedor() -> str:
        return (
            "Nenhuma IA configurada.\n\n"
            "Clique em Configurar IA, escolha um provedor (Gemini e Groq tem tier "
            "gratuito) e informe a chave de API. A configuracao e salva no .env "
            "automaticamente."
        )
