# 💹 Finance Agents — Sistema Multi-Agente Financeiro

Sistema de agentes de IA 100% local para produção de conteúdo financeiro.

## 🏗️ Arquitetura

```
finance-agents/
├── app.py                  # Interface Streamlit
├── manager.py              # Orquestrador central
├── config.yaml             # Configurações, feeds e perfis
├── requirements.txt
├── agents/
│   ├── base_agent.py       # Classe base
│   ├── news_writer.py      # Redator de Notícias
│   ├── copywriter.py       # Copywriter
│   ├── designer.py         # Designer (prompts visuais)
│   ├── marketing.py        # Marketing & Tráfego Pago
│   └── video_editor.py     # Editor de Vídeo
├── tools/
│   ├── rss_fetcher.py      # feedparser
│   ├── web_scraper.py      # BeautifulSoup
│   └── pdf_exporter.py     # FPDF2
└── outputs/                # Arquivos gerados
```

---

## ⚙️ Pré-requisitos

### 1. Python 3.10+
```bash
python --version
```

### 2. Ollama (LLM local)

**Download:** https://ollama.com/download

Após instalar, baixe o modelo recomendado (4GB, funciona com 8GB RAM):
```bash
ollama pull llama3.2:3b
```

Verifique se o Ollama está rodando:
```bash
ollama list
```

### 3. Instalar dependências Python
```bash
pip install -r requirements.txt
```

---

## 🚀 Como rodar

```bash
streamlit run app.py
```

Acesse: **http://localhost:8501**

---

## 📋 Funcionalidades

### 📰 Redator de Notícias
- Busca artigos via RSS (InfoMoney, Valor, Exame, etc.)
- Scraping complementar de sites financeiros
- Gera newsletter estruturada em Markdown/PDF
- Exporta tópicos prontos para o Copywriter

### ✍️ Copywriter
- 4 tipos: Post feed, Legenda Reel, Copy Anúncio, CTAs
- Inspiração em perfis financeiros configurados
- Instruções customizáveis por geração

### 🎨 Designer
- Brief visual completo com composição, tipografia e paleta
- Prompt em inglês pronto para Adobe Firefly / Bing Creator
- 3 paletas pré-configuradas para o nicho financeiro

### 📊 Marketing & Tráfego Pago
- Upload de CSV exportado do **Meta Ads** e/ou **Google Ads**
- Análise automática de métricas vs benchmarks do setor financeiro
- Relatório de auditoria em PDF com gargalos e plano de ação

### 🎬 Editor de Vídeo
- **Reel Educativo:** estrutura didática cena a cena
- **Reel Informativo:** baseado em notícias do dia
- **Carrossel:** slide a slide com copy + dicas de design
- Caption/legenda pronta para publicar

---

## ⚙️ Personalização

Edite `config.yaml` para:
- Adicionar/remover feeds RSS
- Configurar perfis de inspiração
- Ajustar benchmarks de marketing
- Trocar o modelo Ollama (ex: `mistral:7b` se tiver mais RAM)
- Mudar paletas de cores e estilos do Designer

---

## 🛠️ Solução de problemas

**Ollama não conecta:**
```bash
# Verifique se está rodando
ollama serve
# Em outro terminal:
ollama list
```

**Modelo não encontrado:**
```bash
ollama pull llama3.2:3b
```

**Scraping bloqueado:**
Alguns sites bloqueiam scraping. Use apenas os RSS feeds nesses casos.
Configure `scraping_sites: []` no `config.yaml` para desativar o scraping.

**PDF não gerado:**
```bash
pip install fpdf2 --upgrade
```

---

## 📁 Saídas

Todos os arquivos são salvos em `./outputs/` com timestamp:
- `newsletter_YYYY-MM-DD_HH-MM.md` + `.pdf`
- `copy_post_feed_YYYY-MM-DD_HH-MM.md`
- `designer_brief_YYYY-MM-DD_HH-MM.md`
- `auditoria_campanhas_YYYY-MM-DD_HH-MM.md` + `.pdf`
- `reel_educativo_YYYY-MM-DD_HH-MM.md`
- `reel_informativo_YYYY-MM-DD_HH-MM.md`
- `carrossel_YYYY-MM-DD_HH-MM.md`

---

## 💡 Stack utilizada

| Componente | Tecnologia | Custo |
|---|---|---|
| LLM | Ollama + llama3.2:3b | Gratuito |
| Interface | Streamlit | Gratuito |
| RSS | feedparser | Gratuito |
| Scraping | BeautifulSoup4 | Gratuito |
| Dados CSV | pandas | Gratuito |
| PDF | FPDF2 | Gratuito |
| Imagens | Prompt p/ Firefly/Bing | Gratuito |
