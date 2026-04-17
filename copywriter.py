"""
copywriter.py — Agente Copywriter.
Gera posts, legendas, anúncios e CTAs com estilo financeiro,
usando tópicos do Redator e inspirações de perfis configurados.
"""

from __future__ import annotations
from agents.base_agent import BaseAgent


class CopywriterAgent(BaseAgent):

    name = "Copywriter"
    system_prompt = """Você é um copywriter especialista em marketing financeiro digital para o mercado brasileiro.
Você cria conteúdo persuasivo, autêntico e que gera engajamento real nas redes sociais.

Seus textos sempre:
- Têm um hook forte na primeira linha (para parar o scroll)
- Usam linguagem próxima, sem ser informal demais
- Incluem dados e provas concretas quando disponíveis
- Terminam com uma CTA clara e natural
- São adaptados para o nicho de finanças pessoais e investimentos
- Estão em português brasileiro (pt-BR)
"""

    def run(
        self,
        topic: str = "",
        topics_from_news: list[str] | None = None,
        content_type: str = "post_feed",
        inspiration_style: str = "",
        custom_instructions: str = "",
        **kwargs,
    ) -> dict:
        """
        Gera conteúdo de copy para um tópico.

        Args:
            topic: Tópico principal a ser trabalhado
            topics_from_news: Lista de tópicos vindos do Redator
            content_type: Tipo de conteúdo (post_feed, legenda_reel, copy_anuncio, cta)
            inspiration_style: Estilo de perfil de inspiração selecionado
            custom_instructions: Instruções extras do usuário

        Returns:
            dict com 'output', 'filepath', 'agent'
        """
        cfg = self.config["agents"]["copywriter"]
        profiles = self.config.get("inspiration_profiles", [])

        # Resolver tópico
        if not topic and topics_from_news:
            topic = topics_from_news[0]
        if not topic:
            topic = "Investimentos e finanças pessoais"

        # Montar contexto de inspiração
        inspiration_ctx = ""
        if inspiration_style and profiles:
            for p in profiles:
                if inspiration_style.lower() in p["handle"].lower() or inspiration_style.lower() in p["style"].lower():
                    inspiration_ctx = (
                        f"Perfil de inspiração: {p['handle']} ({p['platform']})\n"
                        f"Estilo: {p['style']}\n"
                        f"Tom: {p['tone']}\n"
                        f"Formatos comuns: {', '.join(p['formats'])}"
                    )
                    break

        type_instructions = {
            "post_feed": (
                "Crie um POST para feed do Instagram sobre o tópico abaixo.\n"
                "Estrutura: Hook impactante (1-2 linhas) → Desenvolvimento (3-5 parágrafos curtos) → CTA final.\n"
                f"Use até {cfg['max_hashtags']} hashtags relevantes no final."
            ),
            "legenda_reel": (
                "Crie uma LEGENDA para Reel do Instagram.\n"
                "Estrutura: Primeira linha = hook que aparece antes do 'ver mais' → 2-3 linhas de contexto → CTA com chamada para salvar/comentar.\n"
                f"Use até {cfg['max_hashtags']} hashtags no final."
            ),
            "copy_anuncio": (
                "Crie o TEXTO DE ANÚNCIO (Meta Ads) para o tópico abaixo.\n"
                "Inclua: Headline principal (até 40 chars), Texto primário (até 125 chars), Descrição (até 30 chars), e sugestão de CTA do botão.\n"
                "Crie 2 variações para teste A/B."
            ),
            "cta": (
                "Crie 5 CTAs diferentes para o tópico abaixo.\n"
                f"Estilos de CTA a cobrir: {', '.join(cfg['cta_styles'])}.\n"
                "Cada CTA deve ter no máximo 2 linhas."
            ),
        }

        instructions = type_instructions.get(content_type, type_instructions["post_feed"])

        prompt = f"""{instructions}

TÓPICO: {topic}

{f'CONTEXTO DE INSPIRAÇÃO:{chr(10)}{inspiration_ctx}' if inspiration_ctx else ''}

{f'INSTRUÇÕES ADICIONAIS:{chr(10)}{custom_instructions}' if custom_instructions else ''}

Escreva agora em formato Markdown, pronto para copiar e usar:"""

        output = self._chat(prompt)

        # Adicionar metadados ao output salvo
        full_output = f"# Copy — {content_type.replace('_', ' ').title()}\n\n**Tópico:** {topic}\n\n---\n\n{output}"
        filepath = self._save_output(full_output, f"copy_{content_type}")

        return {
            "output": output,
            "full_output": full_output,
            "filepath": filepath,
            "topic": topic,
            "content_type": content_type,
            "agent": self.name,
        }

    def run_batch(self, topics: list[str], content_types: list[str] | None = None) -> list[dict]:
        """
        Gera copy para múltiplos tópicos de uma vez (ex: saída do Redator).
        """
        if content_types is None:
            content_types = ["post_feed"]

        results = []
        for topic in topics:
            for ct in content_types:
                self.reset_history()
                result = self.run(topic=topic, content_type=ct)
                results.append(result)
        return results
