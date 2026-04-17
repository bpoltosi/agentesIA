"""
manager.py — Gerente / Orquestrador central.
Distribui tarefas entre os agentes, ajusta parâmetros e agrega resultados.
"""

from __future__ import annotations
from typing import Optional, Callable
from pathlib import Path

from agents.news_writer import NewsWriterAgent
from agents.copywriter import CopywriterAgent
from agents.designer import DesignerAgent
from agents.marketing import MarketingAgent
from agents.video_editor import VideoEditorAgent


class AgentManager:
    """
    Orquestrador central do sistema multi-agente.
    Responsável por:
    - Inicializar e manter os agentes
    - Distribuir tarefas e passar contexto entre eles
    - Fornecer status e progresso para a UI
    - Gerenciar o fluxo de dados (ex: tópicos do Redator → Copywriter)
    """

    def __init__(self):
        self.news_writer = NewsWriterAgent()
        self.copywriter = CopywriterAgent()
        self.designer = DesignerAgent()
        self.marketing = MarketingAgent()
        self.video_editor = VideoEditorAgent()

        # Armazena o último resultado de cada agente para reutilização
        self._last_results: dict = {}

        # Tópicos gerados pelo Redator disponíveis para outros agentes
        self.available_topics: list[str] = []

    # ------------------------------------------------------------------
    # Fluxo completo (pipeline)
    # ------------------------------------------------------------------

    def run_full_pipeline(
        self,
        main_topic: str = "",
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """
        Executa o pipeline completo:
        1. Redator busca notícias e gera newsletter + tópicos
        2. Copywriter usa os tópicos do Redator
        3. Editor de Vídeo gera os 3 roteiros
        4. Designer gera brief visual baseado no copy

        Args:
            main_topic: Tema central (se vazio, usa as notícias do dia)
            progress_callback: Função opcional para atualizar barra de progresso
                               Recebe (mensagem: str, progresso: int 0-100)
        """
        results = {}

        def update(msg: str, pct: int):
            if progress_callback:
                progress_callback(msg, pct)

        # 1. Redator
        update("📰 Redator buscando notícias...", 10)
        news_result = self.news_writer.run()
        results["news_writer"] = news_result
        self._last_results["news_writer"] = news_result

        if news_result.get("topics"):
            self.available_topics = news_result["topics"]

        topic = main_topic or (self.available_topics[0] if self.available_topics else "Finanças e investimentos")

        # 2. Copywriter
        update("✍️ Copywriter gerando conteúdo...", 35)
        copy_result = self.copywriter.run(
            topic=topic,
            topics_from_news=self.available_topics,
            content_type="post_feed",
        )
        results["copywriter"] = copy_result
        self._last_results["copywriter"] = copy_result

        # 3. Editor de Vídeo (3 formatos)
        update("🎬 Editor criando roteiros (Reel Educativo)...", 50)
        edu_result = self.video_editor.run(topic=topic, reel_type="educativo")
        results["reel_educativo"] = edu_result

        update("🎬 Editor criando roteiros (Reel Informativo)...", 65)
        info_result = self.video_editor.run(
            topic=topic,
            reel_type="informativo",
            extra_context=news_result.get("output", "")[:500],
        )
        results["reel_informativo"] = info_result

        update("🎬 Editor criando roteiros (Carrossel)...", 78)
        carousel_result = self.video_editor.run(topic=topic, reel_type="carrossel")
        results["carrossel"] = carousel_result

        # 4. Designer
        update("🎨 Designer criando brief visual...", 90)
        design_result = self.designer.run(
            briefing=f"Peça para o conteúdo: {topic}",
            copy_text=copy_result.get("output", "")[:300],
        )
        results["designer"] = design_result
        self._last_results["designer"] = design_result

        update("✅ Pipeline completo!", 100)
        return results

    # ------------------------------------------------------------------
    # Execução individual de cada agente
    # ------------------------------------------------------------------

    def run_news_writer(self, extra_feeds: list[str] | None = None) -> dict:
        result = self.news_writer.run(extra_sources=extra_feeds)
        self._last_results["news_writer"] = result
        if result.get("topics"):
            self.available_topics = result["topics"]
        return result

    def run_copywriter(
        self,
        topic: str = "",
        content_type: str = "post_feed",
        inspiration_handle: str = "",
        custom_instructions: str = "",
    ) -> dict:
        result = self.copywriter.run(
            topic=topic,
            topics_from_news=self.available_topics,
            content_type=content_type,
            inspiration_style=inspiration_handle,
            custom_instructions=custom_instructions,
        )
        self._last_results["copywriter"] = result
        return result

    def run_designer(
        self,
        briefing: str = "",
        platform: str = "Instagram Feed (1080x1080)",
        style: str = "minimalista",
        palette_name: str = "Confiança Financeira",
        inspiration_handle: str = "",
        copy_text: str = "",
    ) -> dict:
        result = self.designer.run(
            briefing=briefing,
            platform=platform,
            style=style,
            palette_name=palette_name,
            inspiration_handle=inspiration_handle,
            copy_text=copy_text,
        )
        self._last_results["designer"] = result
        return result

    def run_marketing(
        self,
        meta_csv_path: Optional[str] = None,
        google_csv_path: Optional[str] = None,
        campaign_context: str = "",
    ) -> dict:
        result = self.marketing.run(
            meta_csv_path=meta_csv_path,
            google_csv_path=google_csv_path,
            campaign_context=campaign_context,
        )
        self._last_results["marketing"] = result
        return result

    def run_video_editor(
        self,
        topic: str = "",
        reel_type: str = "educativo",
        extra_context: str = "",
    ) -> dict:
        result = self.video_editor.run(
            topic=topic,
            reel_type=reel_type,
            extra_context=extra_context,
        )
        self._last_results["video_editor"] = result
        return result

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def get_last_result(self, agent_key: str) -> dict:
        return self._last_results.get(agent_key, {})

    def get_status(self) -> dict:
        return {
            "agents": [
                self.news_writer.status(),
                self.copywriter.status(),
                self.designer.status(),
                self.marketing.status(),
                self.video_editor.status(),
            ],
            "available_topics": self.available_topics,
            "outputs_dir": str(self.news_writer.outputs_dir),
        }

    def get_inspiration_profiles(self) -> list[dict]:
        return self.news_writer.config.get("inspiration_profiles", [])

    def get_design_options(self) -> dict:
        cfg = self.news_writer.config["agents"]["designer"]
        return {
            "platforms": cfg["output_platforms"],
            "palettes": [p["name"] for p in cfg["color_palettes"]],
            "styles": cfg["styles"],
        }
