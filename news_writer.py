"""
news_writer.py — Agente Redator de Notícias.
Busca artigos via RSS + scraping e gera newsletter + tópicos para o Copywriter.
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime

from agents.base_agent import BaseAgent
from tools.rss_fetcher import fetch_all_rss
from tools.web_scraper import scrape_all_sites
from tools.pdf_exporter import export_as_pdf


class NewsWriterAgent(BaseAgent):

    name = "Redator de Notícias"
    system_prompt = """Você é um redator financeiro especialista do mercado brasileiro.
Seu trabalho é transformar manchetes e resumos de notícias em newsletters claras,
objetivas e úteis para investidores e pessoas interessadas em finanças.

Diretrizes:
- Linguagem clara, sem jargões desnecessários
- Dados e números sempre em destaque
- Tom informativo e imparcial
- Sempre em português brasileiro (pt-BR)
- Destaque o impacto prático de cada notícia para o leitor
- Ao final, gere tópicos diretos para o copywriter usar como base de conteúdo
"""

    def run(self, extra_sources: list[str] | None = None, **kwargs) -> dict:
        """
        Busca notícias e gera a newsletter + lista de tópicos.

        Args:
            extra_sources: URLs extras de RSS adicionadas pelo usuário na UI

        Returns:
            dict com 'output', 'filepath', 'pdf_filepath', 'topics', 'agent'
        """
        news_cfg = self.config["news"]
        agent_cfg = self.config["agents"]["news_writer"]

        # 1. Coletar artigos
        feeds = news_cfg.get("rss_feeds", [])
        if extra_sources:
            feeds += [{"name": "Customizado", "url": u} for u in extra_sources]

        rss_articles = fetch_all_rss(
            feeds=feeds,
            max_articles=news_cfg.get("max_articles", 10),
            max_age_hours=news_cfg.get("max_age_hours", 24),
        )
        scraped_articles = scrape_all_sites(news_cfg.get("scraping_sites", []))

        all_articles = rss_articles + scraped_articles

        if not all_articles:
            return {
                "output": "Nenhum artigo encontrado. Verifique sua conexão e os feeds configurados.",
                "filepath": None,
                "pdf_filepath": None,
                "topics": [],
                "agent": self.name,
            }

        # 2. Formatar artigos para o LLM
        articles_text = self._format_articles(all_articles)
        sections = agent_cfg.get("newsletter_sections", [])
        max_topics = agent_cfg.get("max_topics_for_copywriter", 5)

        # 3. Gerar newsletter
        newsletter_prompt = f"""Com base nas seguintes manchetes e resumos financeiros de hoje, escreva uma newsletter completa em Markdown.

SEÇÕES OBRIGATÓRIAS:
{chr(10).join(f"- {s}" for s in sections)}

FORMATO:
# Newsletter Financeira — {datetime.now().strftime('%d/%m/%Y')}

## [Nome da seção]
[Conteúdo da seção com 2-3 notícias relevantes, bem redigidas, com impacto prático]

---

## Para ficar de olho
[3 pontos rápidos sobre tendências ou eventos próximos]

---

## Tópicos para o copywriter
[Liste {max_topics} tópicos numerados, diretos, prontos para virar posts/reels/copy. Ex: "1. Como a alta da Selic afeta seu CDB"]

ARTIGOS DE HOJE:
{articles_text}

Escreva a newsletter completa agora:"""

        newsletter_md = self._chat(newsletter_prompt)

        # 4. Extrair tópicos do output
        topics = self._extract_topics(newsletter_md, max_topics)

        # 5. Salvar arquivos
        md_path = self._save_output(newsletter_md, "newsletter")
        pdf_path = export_as_pdf(
            content=newsletter_md,
            filepath=md_path,
            title=f"Newsletter Financeira — {datetime.now().strftime('%d/%m/%Y')}",
            agent=self.name,
        )

        return {
            "output": newsletter_md,
            "filepath": md_path,
            "pdf_filepath": pdf_path,
            "topics": topics,
            "articles_found": len(all_articles),
            "agent": self.name,
        }

    def _format_articles(self, articles: list[dict]) -> str:
        lines = []
        for i, a in enumerate(articles, 1):
            lines.append(
                f"{i}. [{a['source']}] {a['title']}\n"
                f"   Data: {a.get('published', 'N/D')}\n"
                f"   Resumo: {a.get('summary', 'Sem resumo')}\n"
                f"   URL: {a.get('url', '')}"
            )
        return "\n\n".join(lines)

    def _extract_topics(self, newsletter_text: str, max_topics: int) -> list[str]:
        """Extrai os tópicos listados na seção 'Tópicos para o copywriter'."""
        import re
        topics = []
        in_section = False
        for line in newsletter_text.split("\n"):
            if "tópicos para o copywriter" in line.lower():
                in_section = True
                continue
            if in_section:
                match = re.match(r"^\d+\.\s+(.+)", line.strip())
                if match:
                    topics.append(match.group(1).strip())
                elif line.startswith("##") and topics:
                    break
        return topics[:max_topics]
