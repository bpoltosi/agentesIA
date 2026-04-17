"""
video_editor.py — Agente Editor de Vídeo.
Gera roteiros de Reel Educativo, Reel Informativo e Carrossel
com storyboard cena a cena + caption/legenda prontos para publicar.
"""

from __future__ import annotations
from agents.base_agent import BaseAgent


class VideoEditorAgent(BaseAgent):

    name = "Editor de Vídeo"
    system_prompt = """Você é um roteirista e editor de conteúdo especialista em vídeos financeiros para Instagram e TikTok.
Você cria roteiros detalhados que qualquer criador de conteúdo consegue gravar com o celular.

Seus roteiros sempre têm:
- Um hook irresistível nos primeiros 3 segundos
- Ritmo dinâmico com cortes rápidos (máx. 3-5 segundos por cena)
- Linguagem falada natural, não "de texto"
- Instruções visuais claras para cada cena (câmera, texto na tela, B-roll)
- Legenda/caption completa pronta para copiar e colar
- Sugestão de trilha sonora por mood (sem mencionar músicas com copyright)

Para Carrosséis:
- Slide de capa que para o scroll
- Progressão lógica de informação
- Copy de cada slide (curto, direto)
- Slide final com CTA

Tudo em português brasileiro (pt-BR).
"""

    def run(
        self,
        topic: str = "",
        reel_type: str = "educativo",
        extra_context: str = "",
        **kwargs,
    ) -> dict:
        """
        Gera roteiro completo para Reel ou Carrossel.

        Args:
            topic: Tema do conteúdo
            reel_type: 'educativo', 'informativo' ou 'carrossel'
            extra_context: Contexto adicional (ex: notícia recente)

        Returns:
            dict com 'output', 'filepath', 'agent'
        """
        cfg = self.config["agents"]["video_editor"]

        if reel_type == "carrossel":
            output = self._generate_carousel(topic, cfg, extra_context)
            prefix = "carrossel"
        elif reel_type == "informativo":
            output = self._generate_reel(topic, cfg, extra_context, "informativo")
            prefix = "reel_informativo"
        else:
            output = self._generate_reel(topic, cfg, extra_context, "educativo")
            prefix = "reel_educativo"

        full_output = f"# Roteiro — {reel_type.title()}\n\n**Tema:** {topic}\n\n---\n\n{output}"
        filepath = self._save_output(full_output, prefix)

        return {
            "output": output,
            "full_output": full_output,
            "filepath": filepath,
            "reel_type": reel_type,
            "topic": topic,
            "agent": self.name,
        }

    def run_full_pack(self, topic: str, extra_context: str = "") -> dict:
        """
        Gera os 3 conteúdos de uma vez: Reel Educativo + Reel Informativo + Carrossel.
        """
        results = {}
        for rtype in ["educativo", "informativo", "carrossel"]:
            self.reset_history()
            results[rtype] = self.run(topic=topic, reel_type=rtype, extra_context=extra_context)
        return results

    # ------------------------------------------------------------------
    # Geradores internos
    # ------------------------------------------------------------------

    def _generate_reel(self, topic: str, cfg: dict, extra_context: str, reel_type: str) -> str:
        duration = cfg.get("reel_duration_seconds", 30)
        structure = cfg["reel_types"][reel_type]["structure"]
        hook_style = cfg["reel_types"][reel_type]["hook_style"]

        type_instructions = {
            "educativo": (
                f"Crie um ROTEIRO DE REEL EDUCATIVO de até {duration} segundos sobre o tema abaixo.\n"
                "O objetivo é ensinar algo prático e útil sobre finanças de forma simples e rápida.\n"
                f"Hook: deve usar {hook_style}."
            ),
            "informativo": (
                f"Crie um ROTEIRO DE REEL INFORMATIVO de até {duration} segundos sobre o tema abaixo.\n"
                "O objetivo é informar sobre uma notícia ou acontecimento financeiro e seu impacto prático.\n"
                f"Hook: deve usar {hook_style}."
            ),
        }

        prompt = f"""{type_instructions[reel_type]}

TEMA: {topic}

{f'CONTEXTO ADICIONAL:{chr(10)}{extra_context}' if extra_context else ''}

ESTRUTURA OBRIGATÓRIA: {' → '.join(structure)}

Formate o roteiro assim:

## Roteiro — Reel {reel_type.title()}

### Informações gerais
- Duração estimada: X segundos
- Formato: vertical 9:16
- Mood: [mood da música sugerido, ex: energético, calmo, inspirador]
- Sugestão de trilha: [mood/estilo sem citar título, ex: "lo-fi instrumental animado" ou "trilha corporativa motivacional"]

---

### Cenas

**[CENA 1 — 0:00-0:03] Hook**
🎬 Câmera: [instrução de filmagem]
📝 Texto na tela: [texto exato que aparece sobreposto]
🗣️ Narração: "[fala exata do criador]"

**[CENA 2 — 0:03-0:08] [Nome do bloco]**
🎬 Câmera: [instrução]
📝 Texto na tela: [texto]
🗣️ Narração: "[fala]"

[Continue para todas as cenas necessárias]

---

### Caption/Legenda completa
[Legenda pronta para copiar, com emojis, parágrafos curtos e hashtags]

---

### Checklist de produção
- [ ] [Item técnico ou de conteúdo a verificar antes de postar]
[Mínimo 5 itens]
"""

        return self._chat(prompt)

    def _generate_carousel(self, topic: str, cfg: dict, extra_context: str) -> str:
        min_slides = cfg.get("carousel_slides_min", 5)
        max_slides = cfg.get("carousel_slides_max", 10)

        prompt = f"""Crie um ROTEIRO DE CARROSSEL para Instagram sobre o tema abaixo.
O carrossel deve ter entre {min_slides} e {max_slides} slides e ser otimizado para salvar e compartilhar.

TEMA: {topic}

{f'CONTEXTO ADICIONAL:{chr(10)}{extra_context}' if extra_context else ''}

Formate assim:

## Roteiro — Carrossel

### Estratégia
- Objetivo: [o que o carrossel vai ensinar/comunicar]
- Por que salvar: [motivo para o usuário guardar]
- Número de slides: X

---

### Slides

**SLIDE 1 — Capa (para o scroll)**
🎨 Visual: [descrição do visual — fundo, cor destaque]
📝 Título: [texto principal, grande e impactante]
📝 Subtítulo: [texto de apoio, opcional]
💡 Objetivo: Parar o scroll e gerar curiosidade

**SLIDE 2**
🎨 Visual: [descrição]
📝 Headline: [título do slide]
📝 Corpo: [texto do conteúdo — curto, direto, máx. 3 linhas]

[Continue para todos os slides]

**SLIDE FINAL — CTA**
🎨 Visual: [descrição]
📝 Texto: [CTA clara — ex: "Salva esse post pra não esquecer!"]
📝 Complemento: [pergunta para engajamento nos comentários]

---

### Caption/Legenda completa
[Legenda pronta para copiar, com emojis, parágrafos curtos e hashtags]

---

### Dicas de design
[3-5 orientações visuais para quem vai montar no Canva ou similar]
"""

        return self._chat(prompt)
