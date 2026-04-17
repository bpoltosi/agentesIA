"""
designer.py — Agente Designer.
Analisa briefing e perfis de inspiração para gerar prompts visuais
detalhados prontos para usar no Adobe Firefly, Bing Creator ou similares.
"""

from __future__ import annotations
from agents.base_agent import BaseAgent


class DesignerAgent(BaseAgent):

    name = "Designer"
    system_prompt = """Você é um diretor de arte especialista em conteúdo financeiro para redes sociais.
Você não gera imagens diretamente — você cria briefs e prompts visuais extremamente detalhados
que um designer ou uma IA de imagens (Firefly, Midjourney, DALL-E) pode executar com perfeição.

Seus prompts sempre incluem:
- Composição e enquadramento
- Paleta de cores exata (com valores hexadecimais)
- Tipografia e hierarquia visual
- Elementos gráficos e ícones
- Mood/atmosfera desejada
- Especificações técnicas (tamanho, formato)
- Versão em inglês do prompt para IA geradora de imagens

Você conhece profundamente o mercado financeiro brasileiro e cria visuais que transmitem:
confiança, crescimento, clareza e modernidade.
"""

    def run(
        self,
        briefing: str = "",
        platform: str = "Instagram Feed (1080x1080)",
        style: str = "minimalista",
        palette_name: str = "Confiança Financeira",
        inspiration_handle: str = "",
        copy_text: str = "",
        **kwargs,
    ) -> dict:
        """
        Gera prompt visual detalhado para uma peça gráfica.

        Args:
            briefing: Descrição do que a peça deve comunicar
            platform: Plataforma/formato de destino
            style: Estilo visual desejado
            palette_name: Nome da paleta de cores do config
            inspiration_handle: Handle do perfil de inspiração
            copy_text: Texto/copy que aparecerá na peça

        Returns:
            dict com 'output', 'filepath', 'agent'
        """
        cfg_design = self.config["agents"]["designer"]
        profiles = self.config.get("inspiration_profiles", [])

        # Resolver paleta
        palette = next(
            (p for p in cfg_design["color_palettes"] if p["name"] == palette_name),
            cfg_design["color_palettes"][0],
        )

        # Resolver inspiração
        inspiration_ctx = ""
        if inspiration_handle:
            profile = next(
                (p for p in profiles if inspiration_handle.lower() in p["handle"].lower()),
                None,
            )
            if profile:
                inspiration_ctx = (
                    f"Inspiração visual no perfil {profile['handle']}:\n"
                    f"- Estilo: {profile['style']}\n"
                    f"- Tom visual: {profile['tone']}\n"
                    f"- Formatos comuns: {', '.join(profile['formats'])}"
                )

        prompt = f"""Crie um brief visual completo e um prompt de IA para a seguinte peça gráfica financeira.

ESPECIFICAÇÕES:
- Plataforma: {platform}
- Estilo visual: {style}
- Paleta de cores: {palette['name']} — {', '.join(palette['colors'])}

BRIEFING DO CONTEÚDO:
{briefing if briefing else "Conteúdo financeiro geral — inspire-se nos melhores perfis do nicho"}

{f'TEXTO QUE APARECERÁ NA PEÇA:{chr(10)}{copy_text}' if copy_text else ''}

{f'REFERÊNCIA VISUAL:{chr(10)}{inspiration_ctx}' if inspiration_ctx else ''}

Estruture sua resposta assim:

## Brief Visual

### Conceito
[Descrição do conceito e ideia central da peça]

### Composição
[Enquadramento, grid, hierarquia dos elementos]

### Tipografia
[Fontes sugeridas, tamanhos, pesos, cores de cada texto]

### Elementos gráficos
[Ícones, formas, gráficos, elementos decorativos]

### Paleta aplicada
[Como cada cor da paleta será usada]

### Mood/Atmosfera
[Sensação que a peça deve transmitir]

---

## Prompt para IA geradora de imagens (em inglês)

```
[Prompt completo e detalhado em inglês para usar no Adobe Firefly, Bing Image Creator ou DALL-E]
```

## Orientações de uso
[Onde usar, variações recomendadas, cuidados]
"""

        output = self._chat(prompt)
        full_output = f"# Brief Visual — {platform}\n\n**Briefing:** {briefing}\n\n---\n\n{output}"
        filepath = self._save_output(full_output, "designer_brief")

        return {
            "output": output,
            "full_output": full_output,
            "filepath": filepath,
            "platform": platform,
            "palette": palette,
            "agent": self.name,
        }
