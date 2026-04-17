"""
marketing.py — Agente de Marketing e Tráfego Pago.
Analisa CSVs exportados do Meta Ads e Google Ads,
identifica gargalos e gera relatório de auditoria com sugestões de melhoria.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

import pandas as pd

from agents.base_agent import BaseAgent
from tools.pdf_exporter import export_as_pdf


class MarketingAgent(BaseAgent):

    name = "Marketing & Tráfego Pago"
    system_prompt = """Você é um especialista em tráfego pago e performance digital com foco em finanças.
Você analisa dados reais de campanhas Meta Ads e Google Ads e produz relatórios acionáveis.

Suas análises sempre:
- Identificam métricas fora dos benchmarks do setor financeiro
- Apontam gargalos específicos com dados (ex: "CTR de 0.3% está 70% abaixo do benchmark de 1%")
- Priorizam as melhorias por impacto potencial
- Sugerem testes A/B concretos e hipóteses de melhoria
- Consideram o funil completo: impressões → cliques → conversões
- Estão em português brasileiro (pt-BR)

Você nunca inventa dados — só analisa o que foi fornecido.
"""

    def run(
        self,
        meta_csv_path: Optional[str] = None,
        google_csv_path: Optional[str] = None,
        campaign_context: str = "",
        **kwargs,
    ) -> dict:
        """
        Analisa CSVs de campanhas e gera relatório de auditoria.

        Args:
            meta_csv_path: Caminho para CSV exportado do Meta Ads
            google_csv_path: Caminho para CSV exportado do Google Ads
            campaign_context: Contexto adicional sobre as campanhas (objetivo, período, produto)

        Returns:
            dict com 'output', 'filepath', 'pdf_filepath', 'agent'
        """
        if not meta_csv_path and not google_csv_path:
            return {
                "output": "Nenhum arquivo CSV fornecido. Faça upload de um CSV do Meta Ads e/ou Google Ads.",
                "filepath": None,
                "pdf_filepath": None,
                "agent": self.name,
            }

        benchmarks = self.config["agents"]["marketing"]["benchmarks"]
        sections = []

        # Analisar Meta Ads
        if meta_csv_path and Path(meta_csv_path).exists():
            meta_summary = self._analyze_meta(meta_csv_path, benchmarks["meta"])
            sections.append(("Meta Ads", meta_summary))

        # Analisar Google Ads
        if google_csv_path and Path(google_csv_path).exists():
            google_summary = self._analyze_google(google_csv_path, benchmarks["google"])
            sections.append(("Google Ads", google_summary))

        if not sections:
            return {
                "output": "Arquivos CSV não encontrados ou inválidos.",
                "filepath": None,
                "pdf_filepath": None,
                "agent": self.name,
            }

        # Montar prompt de auditoria
        data_text = ""
        for platform, summary in sections:
            data_text += f"\n\n### {platform}\n{summary}"

        audit_prompt = f"""Com base nos dados reais de campanhas abaixo, gere um relatório completo de auditoria em Markdown.

CONTEXTO DAS CAMPANHAS:
{campaign_context if campaign_context else "Sem contexto adicional fornecido."}

DADOS DAS CAMPANHAS:
{data_text}

BENCHMARKS DO SETOR FINANCEIRO:
Meta Ads:
- CTR mínimo: {benchmarks['meta']['ctr_min']}%
- CPC máximo: R$ {benchmarks['meta']['cpc_max_brl']}
- CPM referência: R$ {benchmarks['meta']['cpm_ref_brl']}
- Frequência máxima: {benchmarks['meta']['frequency_max']}x

Google Ads:
- CTR mínimo: {benchmarks['google']['ctr_min']}%
- CPC máximo: R$ {benchmarks['google']['cpc_max_brl']}
- Taxa de conversão mínima: {benchmarks['google']['conv_rate_min']}%

Estruture o relatório assim:

# Relatório de Auditoria de Campanhas

## Resumo Executivo
[3-5 frases com os principais achados]

## Análise por Plataforma

### [Nome da plataforma]
#### Métricas em destaque
[Tabela ou lista com as métricas principais e status: ✅ OK / ⚠️ Atenção / 🔴 Crítico]

#### Gargalos identificados
[Lista priorizada de problemas, com dados concretos]

#### Campanhas com melhor e pior performance
[Top 2 e bottom 2 se houver dados suficientes]

## Plano de Ação

### Melhorias imediatas (esta semana)
[2-3 ações de alto impacto e baixo esforço]

### Testes A/B recomendados
[2-3 hipóteses de teste com metodologia]

### Ajustes de médio prazo (próximas 4 semanas)
[Estratégias estruturais de melhoria]

## Conclusão
[Prioridade #1 absoluta e próximo passo]
"""

        report_md = self._chat(audit_prompt)

        md_path = self._save_output(report_md, "auditoria_campanhas")
        pdf_path = export_as_pdf(
            content=report_md,
            filepath=md_path,
            title="Relatório de Auditoria de Campanhas",
            agent=self.name,
        )

        return {
            "output": report_md,
            "filepath": md_path,
            "pdf_filepath": pdf_path,
            "platforms_analyzed": [s[0] for s in sections],
            "agent": self.name,
        }

    # ------------------------------------------------------------------
    # Parsers de CSV
    # ------------------------------------------------------------------

    def _analyze_meta(self, csv_path: str, benchmarks: dict) -> str:
        """Lê CSV do Meta Ads e retorna sumário textual."""
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
            df.columns = df.columns.str.strip()

            lines = [f"Arquivo: {Path(csv_path).name}", f"Total de linhas: {len(df)}"]
            lines.append(f"Colunas disponíveis: {', '.join(df.columns.tolist())}")

            # Métricas numéricas
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            for col in numeric_cols:
                total = df[col].sum()
                mean = df[col].mean()
                lines.append(f"{col}: Total={total:,.2f} | Média={mean:,.2f}")

            # Alertas de benchmark
            col_map = {c.lower(): c for c in df.columns}
            alerts = []

            ctr_col = col_map.get("ctr (link click-through rate)", col_map.get("ctr", None))
            if ctr_col:
                avg_ctr = df[ctr_col].mean()
                if avg_ctr < benchmarks["ctr_min"]:
                    alerts.append(f"⚠️ CTR médio ({avg_ctr:.2f}%) abaixo do benchmark ({benchmarks['ctr_min']}%)")

            freq_col = col_map.get("frequency", None)
            if freq_col:
                avg_freq = df[freq_col].mean()
                if avg_freq > benchmarks["frequency_max"]:
                    alerts.append(f"🔴 Frequência média ({avg_freq:.1f}x) acima do máximo recomendado ({benchmarks['frequency_max']}x)")

            if alerts:
                lines.append("\nALERTAS:")
                lines.extend(alerts)

            # Top/bottom campanhas por resultado
            name_col = col_map.get("campaign name", col_map.get("nome da campanha", None))
            result_col = col_map.get("results", col_map.get("resultados", None))
            if name_col and result_col:
                df_sorted = df[[name_col, result_col]].dropna().sort_values(result_col, ascending=False)
                if len(df_sorted) >= 2:
                    lines.append(f"\nMelhor campanha: {df_sorted.iloc[0][name_col]} ({df_sorted.iloc[0][result_col]} resultados)")
                    lines.append(f"Pior campanha: {df_sorted.iloc[-1][name_col]} ({df_sorted.iloc[-1][result_col]} resultados)")

            return "\n".join(lines)

        except Exception as e:
            return f"[Erro ao ler CSV do Meta Ads: {e}]"

    def _analyze_google(self, csv_path: str, benchmarks: dict) -> str:
        """Lê CSV do Google Ads e retorna sumário textual."""
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
            df.columns = df.columns.str.strip()

            lines = [f"Arquivo: {Path(csv_path).name}", f"Total de linhas: {len(df)}"]
            lines.append(f"Colunas disponíveis: {', '.join(df.columns.tolist())}")

            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            for col in numeric_cols:
                total = df[col].sum()
                mean = df[col].mean()
                lines.append(f"{col}: Total={total:,.2f} | Média={mean:,.2f}")

            col_map = {c.lower(): c for c in df.columns}
            alerts = []

            ctr_col = col_map.get("ctr", None)
            if ctr_col:
                avg_ctr = pd.to_numeric(df[ctr_col].astype(str).str.replace("%", ""), errors="coerce").mean()
                if pd.notna(avg_ctr) and avg_ctr < benchmarks["ctr_min"]:
                    alerts.append(f"⚠️ CTR médio ({avg_ctr:.2f}%) abaixo do benchmark ({benchmarks['ctr_min']}%)")

            conv_col = col_map.get("conv. rate", col_map.get("conversion rate", None))
            if conv_col:
                avg_conv = pd.to_numeric(df[conv_col].astype(str).str.replace("%", ""), errors="coerce").mean()
                if pd.notna(avg_conv) and avg_conv < benchmarks["conv_rate_min"]:
                    alerts.append(f"⚠️ Taxa de conversão média ({avg_conv:.2f}%) abaixo do benchmark ({benchmarks['conv_rate_min']}%)")

            if alerts:
                lines.append("\nALERTAS:")
                lines.extend(alerts)

            return "\n".join(lines)

        except Exception as e:
            return f"[Erro ao ler CSV do Google Ads: {e}]"
