"""
app.py — Interface Streamlit do sistema multi-agente financeiro.
Execute com: streamlit run app.py
"""

import streamlit as st
import tempfile
from pathlib import Path
from datetime import date, datetime

st.set_page_config(
    page_title="Finance Agents",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .agent-card {
        background: var(--secondary-background-color);
        border-left: 4px solid #1A3C5E;
        padding: 10px 14px;
        border-radius: 4px;
        margin-bottom: 6px;
        font-size: 13px;
    }
    .stTabs [data-baseweb="tab"] { font-size: 14px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------
# Singletons via cache
# ---------------------------------------------------------------
@st.cache_resource
def get_manager():
    from manager import AgentManager
    return AgentManager()

@st.cache_resource
def get_templates():
    from tools.template_manager import TemplateManager
    return TemplateManager()

@st.cache_resource
def get_calendar():
    from tools.content_calendar import ContentCalendar
    return ContentCalendar()

@st.cache_resource
def get_metrics():
    from tools.metrics import MetricsTracker
    return MetricsTracker()

@st.cache_resource
def get_refiner():
    from tools.refiner import RefinerAgent
    return RefinerAgent()

manager   = get_manager()
templates = get_templates()
calendar  = get_calendar()
metrics   = get_metrics()
refiner   = get_refiner()


# ---------------------------------------------------------------
# Utilitário de download — MD + PDF + DOCX
# ---------------------------------------------------------------
def show_downloads(result: dict, content: str = "", title: str = "", agent_name: str = ""):
    filepath = result.get("filepath")
    pdf_filepath = result.get("pdf_filepath")
    text = content or result.get("full_output") or result.get("output", "")

    col1, col2, col3 = st.columns(3)
    with col1:
        if filepath and Path(filepath).exists():
            st.download_button("⬇️ .md",
                data=Path(filepath).read_text(encoding="utf-8"),
                file_name=Path(filepath).name, mime="text/markdown",
                use_container_width=True, key=f"md_{filepath}")
    with col2:
        if pdf_filepath and Path(str(pdf_filepath)).exists():
            with open(str(pdf_filepath), "rb") as f:
                st.download_button("⬇️ .pdf", data=f.read(),
                    file_name=Path(str(pdf_filepath)).name, mime="application/pdf",
                    use_container_width=True, key=f"pdf_{pdf_filepath}")
    with col3:
        if text and filepath:
            try:
                from tools.docx_exporter import export_as_docx
                docx_path = export_as_docx(text, Path(filepath),
                    title=title or Path(filepath).stem,
                    agent=agent_name or result.get("agent", ""))
                if docx_path.exists():
                    with open(docx_path, "rb") as f:
                        st.download_button("⬇️ .docx", data=f.read(),
                            file_name=docx_path.name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True, key=f"docx_{docx_path}")
            except Exception:
                pass


# ---------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------
with st.sidebar:
    st.title("💹 Finance Agents")
    st.caption("Sistema multi-agente · 100% local")
    st.divider()

    status = manager.get_status()

    # Status do Ollama e modelos disponiveis
    try:
        from agents.base_agent import list_available_models
        _models = list_available_models("http://localhost:11434")
        if _models:
            st.success("Ollama: " + " | ".join(_models))
        else:
            st.error("Nenhum modelo instalado. Execute:\n`ollama pull mistral:7b`")
    except Exception as _e:
        st.warning(f"Ollama offline. Inicie com: `ollama serve`")

    st.subheader("🤖 Agentes")
    for agent in status["agents"]:
        st.markdown(
            f"<div class='agent-card'><b>{agent['agent']}</b><br>"
            f"<small>Modelo: {agent['model']} · {agent['history_turns']} turnos</small></div>",
            unsafe_allow_html=True)

    st.divider()
    if status["available_topics"]:
        st.subheader("📌 Tópicos disponíveis")
        for t in status["available_topics"]:
            st.markdown(f"• {t}")

    st.divider()
    import scheduler as sched_mod
    if sched_mod.is_running():
        st.success("🕐 Scheduler: **ativo**")
        for job in sched_mod.get_next_runs():
            st.caption(f"Próximo {job['label']}: {job['next_run']}")
    else:
        st.info("🕐 Scheduler: inativo")

    st.divider()
    outputs_path = Path(status["outputs_dir"])
    n_files = len(list(outputs_path.glob("*"))) if outputs_path.exists() else 0
    st.caption(f"📁 {n_files} arquivo(s) em /outputs")
    st.caption(f"📊 {metrics.total_generations()} conteúdos gerados")


# ---------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------
(tab_pipeline, tab_news, tab_copy, tab_design, tab_mkt, tab_video,
 tab_refine, tab_history, tab_calendar, tab_templates,
 tab_dashboard, tab_scheduler) = st.tabs([
    "🚀 Pipeline", "📰 Redator", "✍️ Copywriter", "🎨 Designer",
    "📊 Marketing", "🎬 Vídeo", "🔁 Refinar", "📁 Histórico",
    "📅 Calendário", "🔖 Templates", "📈 Métricas", "⚙️ Agendamento",
])


# ===============================================================
# PIPELINE
# ===============================================================
with tab_pipeline:
    st.header("🚀 Pipeline Completo")
    st.markdown("Executa todos os agentes em sequência: **Redator → Copywriter → Vídeo → Designer**")
    main_topic = st.text_input("Tema central (opcional)", placeholder="Ex: Alta da Selic e impacto nos investimentos")

    if st.button("▶️ Executar pipeline", type="primary", use_container_width=True):
        bar = st.progress(0)
        def upd(msg, pct): bar.progress(pct / 100, text=msg)
        with st.spinner("Agentes trabalhando..."):
            try:
                results = manager.run_full_pipeline(main_topic=main_topic, progress_callback=upd)
                bar.empty()
                st.success("✅ Pipeline concluído!")
                metrics.record("Pipeline", "pipeline_completo", topic=main_topic, success=True)
                for key, result in results.items():
                    if not result.get("output"):
                        continue
                    with st.expander(f"📄 {result.get('agent', key)}"):
                        st.markdown(result["output"])
                        show_downloads(result)
            except Exception as e:
                st.error(f"Erro: {e}"); bar.empty()


# ===============================================================
# REDATOR
# ===============================================================
with tab_news:
    st.header("📰 Redator de Notícias")
    with st.expander("⚙️ Feeds RSS adicionais"):
        extra_input = st.text_area("URLs extras (uma por linha)", placeholder="https://site.com/feed/")

    if st.button("📡 Buscar e gerar newsletter", type="primary", use_container_width=True):
        extra = [u.strip() for u in extra_input.strip().splitlines() if u.strip()]
        with st.spinner("Buscando notícias..."):
            result = manager.run_news_writer(extra_feeds=extra or None)
        if result.get("output"):
            st.success(f"✅ {result.get('articles_found', 0)} artigos processados.")
            if result.get("topics"):
                st.subheader("📌 Tópicos para o Copywriter")
                for i, t in enumerate(result["topics"], 1):
                    st.markdown(f"**{i}.** {t}")
            st.markdown(result["output"])
            show_downloads(result, title="Newsletter Financeira", agent_name="Redator")
            metrics.record("Redator", "newsletter", output_chars=len(result["output"]))


# ===============================================================
# COPYWRITER
# ===============================================================
with tab_copy:
    st.header("✍️ Copywriter")
    col1, col2 = st.columns([2, 1])
    with col1:
        topic_input = st.text_input("Tópico", placeholder="Ex: Como a Selic alta afeta seus CDBs")
    with col2:
        content_type = st.selectbox("Tipo", ["post_feed", "legenda_reel", "copy_anuncio", "cta"],
            format_func=lambda x: {"post_feed": "📸 Post Feed", "legenda_reel": "🎬 Legenda Reel",
                                    "copy_anuncio": "📢 Anúncio", "cta": "👆 CTAs"}[x])

    profiles = manager.get_inspiration_profiles()
    insp_sel = st.selectbox("Inspiração", ["Nenhum"] + [f"{p['handle']} — {p['tone']}" for p in profiles])
    insp_handle = "" if insp_sel == "Nenhum" else insp_sel.split("—")[0].strip()
    custom_inst = st.text_area("Instruções adicionais", height=70)

    col_gen, col_ab = st.columns(2)
    with col_gen:
        if st.button("✍️ Gerar copy", type="primary", use_container_width=True):
            with st.spinner("Escrevendo..."):
                result = manager.run_copywriter(topic=topic_input, content_type=content_type,
                    inspiration_handle=insp_handle, custom_instructions=custom_inst)
            if result.get("output"):
                st.success("✅ Copy gerado!")
                st.markdown(result["output"])
                show_downloads(result, title=f"Copy — {content_type}", agent_name="Copywriter")
                metrics.record("Copywriter", content_type, topic=topic_input, output_chars=len(result["output"]))

    with col_ab:
        if st.button("🆎 Comparar A/B", use_container_width=True):
            with st.spinner("Gerando versões A e B..."):
                r_a = manager.run_copywriter(topic=topic_input, content_type=content_type,
                    inspiration_handle=insp_handle, custom_instructions=custom_inst)
                manager.copywriter.reset_history()
                r_b = manager.run_copywriter(topic=topic_input, content_type=content_type,
                    inspiration_handle=insp_handle, custom_instructions=custom_inst + "\n[Variação B]")
            if r_a.get("output") and r_b.get("output"):
                ca, cb = st.columns(2)
                with ca:
                    st.markdown("**Versão A**"); st.markdown(r_a["output"])
                with cb:
                    st.markdown("**Versão B**"); st.markdown(r_b["output"])
                with st.spinner("Analisando diferenças..."):
                    analysis = refiner.compare_versions(r_a["output"], r_b["output"], content_type)
                st.markdown(analysis.get("analysis", ""))
                metrics.record("Copywriter", f"{content_type}_ab", topic=topic_input)


# ===============================================================
# DESIGNER
# ===============================================================
with tab_design:
    st.header("🎨 Designer")
    design_opts = manager.get_design_options()
    c1, c2, c3 = st.columns(3)
    with c1: platform = st.selectbox("Plataforma", design_opts["platforms"])
    with c2: palette = st.selectbox("Paleta", design_opts["palettes"])
    with c3: style = st.selectbox("Estilo", design_opts["styles"])
    briefing  = st.text_area("Briefing", placeholder="Ex: Peça sobre Tesouro Direto para iniciantes", height=70)
    copy_text = st.text_area("Copy na peça (opcional)", height=70)
    insp_d    = st.selectbox("Inspiração visual", ["Nenhum"] + [p["handle"] for p in manager.get_inspiration_profiles()], key="d_insp")

    if st.button("🎨 Gerar brief visual", type="primary", use_container_width=True):
        with st.spinner("Criando brief..."):
            result = manager.run_designer(briefing=briefing, platform=platform, style=style,
                palette_name=palette, inspiration_handle="" if insp_d == "Nenhum" else insp_d, copy_text=copy_text)
        if result.get("output"):
            st.success("✅ Brief gerado!")
            st.markdown(result["output"])
            show_downloads(result, title="Brief Visual", agent_name="Designer")
            metrics.record("Designer", "brief_visual", topic=briefing, output_chars=len(result["output"]))


# ===============================================================
# MARKETING
# ===============================================================
with tab_mkt:
    st.header("📊 Marketing & Tráfego Pago")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Meta Ads")
        meta_file = st.file_uploader("CSV do Meta Ads", type=["csv"], key="meta")
    with c2:
        st.subheader("Google Ads")
        google_file = st.file_uploader("CSV do Google Ads", type=["csv"], key="google")
    campaign_ctx = st.text_area("Contexto das campanhas", height=70,
        placeholder="Ex: Campanha de leads para previdência privada, março/2025, orçamento R$150/dia")

    if st.button("🔍 Analisar campanhas", type="primary", use_container_width=True):
        if not meta_file and not google_file:
            st.warning("Faça upload de ao menos um CSV.")
        else:
            meta_path = google_path = None
            if meta_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(meta_file.read()); meta_path = tmp.name
            if google_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    tmp.write(google_file.read()); google_path = tmp.name
            with st.spinner("Analisando..."):
                result = manager.run_marketing(meta_csv_path=meta_path,
                    google_csv_path=google_path, campaign_context=campaign_ctx)
            if result.get("output"):
                st.success(f"✅ Auditoria concluída! ({', '.join(result.get('platforms_analyzed', []))})")
                st.markdown(result["output"])
                show_downloads(result, title="Auditoria de Campanhas", agent_name="Marketing")
                metrics.record("Marketing", "auditoria_ads", output_chars=len(result["output"]))


# ===============================================================
# EDITOR DE VÍDEO
# ===============================================================
with tab_video:
    st.header("🎬 Editor de Vídeo")
    c1, c2 = st.columns([3, 1])
    with c1: video_topic = st.text_input("Tema", placeholder="Ex: Como investir R$500/mês em renda fixa")
    with c2:
        reel_type = st.selectbox("Tipo", ["educativo", "informativo", "carrossel"],
            format_func=lambda x: {"educativo": "🎓 Reel Educativo",
                                    "informativo": "📡 Reel Informativo", "carrossel": "📑 Carrossel"}[x])
    extra_ctx = st.text_area("Contexto adicional", height=70)

    cs, cp = st.columns(2)
    with cs:
        if st.button("🎬 Gerar roteiro", type="primary", use_container_width=True):
            t = video_topic or (manager.available_topics[0] if manager.available_topics else "")
            if not t: st.warning("Digite um tema ou execute o Redator primeiro.")
            else:
                with st.spinner("Criando roteiro..."):
                    result = manager.run_video_editor(topic=t, reel_type=reel_type, extra_context=extra_ctx)
                st.success("✅ Roteiro gerado!")
                st.markdown(result["output"])
                show_downloads(result, title=f"Roteiro {reel_type}", agent_name="Editor Vídeo")
                metrics.record("Editor Vídeo", reel_type, topic=t, output_chars=len(result["output"]))
    with cp:
        if st.button("📦 Pack completo (3 formatos)", use_container_width=True):
            t = video_topic or (manager.available_topics[0] if manager.available_topics else "")
            if not t: st.warning("Digite um tema ou execute o Redator primeiro.")
            else:
                with st.spinner("Gerando pack..."):
                    pack = manager.video_editor.run_full_pack(topic=t, extra_context=extra_ctx)
                st.success("✅ Pack completo!")
                for rtype, result in pack.items():
                    with st.expander(f"🎬 {rtype.replace('_',' ').title()}"):
                        st.markdown(result.get("output", ""))
                        show_downloads(result)
                        metrics.record("Editor Vídeo", rtype, topic=t)


# ===============================================================
# REFINADOR
# ===============================================================
with tab_refine:
    st.header("🔁 Modo Refinamento")
    st.markdown("Ajuste qualquer conteúdo gerado sem reescrever do zero.")

    from tools.refiner import REFINEMENT_PRESETS

    original_text = st.text_area("Cole o conteúdo a refinar", height=200,
        placeholder="Cole qualquer output gerado pelos agentes...")
    c1, c2 = st.columns([2, 1])
    with c1: preset = st.selectbox("Tipo de refinamento", list(REFINEMENT_PRESETS.keys()))
    with c2:
        ct_ref = st.selectbox("Tipo do conteúdo", ["", "post_feed", "newsletter", "reel", "carrossel", "copy_anuncio"],
            format_func=lambda x: x or "Detectar automaticamente")

    custom_ref = ""
    if preset == "Instrução personalizada":
        custom_ref = st.text_area("Sua instrução", placeholder="Ex: Adicione uma metáfora com futebol", height=70)

    cr, ca = st.columns(2)
    with cr:
        if st.button("🔁 Refinar", type="primary", use_container_width=True):
            if not original_text.strip(): st.warning("Cole o conteúdo original para refinar.")
            else:
                with st.spinner("Refinando..."):
                    result = refiner.refine(original_content=original_text, instruction=preset,
                        content_type=ct_ref, custom_instruction=custom_ref)
                if result.get("output"):
                    st.session_state["last_refine"] = result
                    st.success(f"✅ Instrução aplicada: **{result['instruction_applied']}**")
                    st.markdown(result["output"])
                    show_downloads(result, content=result["output"],
                        title=f"Refinado — {preset}", agent_name="Refinador")
                    metrics.record("Refinador", preset, output_chars=len(result["output"]))
    with ca:
        if st.button("⚖️ Análise comparativa", use_container_width=True):
            if not original_text.strip(): st.warning("Cole o conteúdo original.")
            elif "last_refine" not in st.session_state: st.info("Refine primeiro para comparar.")
            else:
                with st.spinner("Analisando..."):
                    an = refiner.compare_versions(original_text, st.session_state["last_refine"]["output"], ct_ref)
                st.markdown(an.get("analysis", ""))


# ===============================================================
# HISTÓRICO
# ===============================================================
with tab_history:
    st.header("📁 Histórico de Outputs")
    from tools.history_manager import list_outputs, get_all_agents, read_file_content, delete_file

    outputs_path = Path(manager.news_writer.outputs_dir)
    c1, c2 = st.columns([2, 1])
    with c1: search_q = st.text_input("🔍 Buscar", placeholder="nome do arquivo ou tema...")
    with c2: agent_filt = st.selectbox("Filtrar por agente", get_all_agents())

    files = list_outputs(outputs_path, agent_filter=agent_filt, search=search_q)
    if not files: st.info("Nenhum output encontrado. Execute um agente para começar.")
    else:
        st.caption(f"{len(files)} arquivo(s) encontrado(s)")
        for file in files:
            with st.expander(f"{file['icon']} {file['label']} — {file['modified']}  |  {file['size_kb']} KB"):
                st.caption(f"Agente: {file['agent']} · {file['name']}")
                if file["extension"] == ".md":
                    content = read_file_content(file["path"])
                    if content:
                        st.markdown(content[:2000] + ("..." if len(content) > 2000 else ""))
                        st.download_button("⬇️ .md", data=content, file_name=file["name"],
                            mime="text/markdown", key=f"h_dl_{file['name']}")
                elif file["extension"] == ".pdf":
                    with open(file["path"], "rb") as f:
                        st.download_button("⬇️ .pdf", data=f.read(), file_name=file["name"],
                            mime="application/pdf", key=f"h_dl_{file['name']}")
                if st.button("🗑️ Deletar", key=f"h_del_{file['name']}"):
                    if delete_file(file["path"]): st.success("Removido."); st.rerun()


# ===============================================================
# CALENDÁRIO EDITORIAL
# ===============================================================
with tab_calendar:
    st.header("📅 Calendário Editorial")
    from tools.content_calendar import CONTENT_TYPES, STATUS_OPTIONS

    sub_view, sub_add = st.tabs(["📅 Semana", "➕ Adicionar"])

    with sub_view:
        ref_date = st.date_input("Semana de referência", value=date.today())
        week = calendar.get_week(ref_date)
        DAY_NAMES = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        for i, (day_str, entries) in enumerate(week.items()):
            day_dt = datetime.strptime(day_str, "%Y-%m-%d")
            is_today = day_str == date.today().isoformat()
            label = f"{'📍 ' if is_today else ''}{DAY_NAMES[i]} {day_dt.strftime('%d/%m')}"
            with st.expander(label + (f"  ({len(entries)} item{'s' if len(entries)!=1 else ''})" if entries else "  (vazio)"), expanded=is_today):
                if not entries: st.caption("Nenhum conteúdo planejado.")
                for entry in entries:
                    ce, cs2, cd = st.columns([4, 2, 1])
                    with ce:
                        ct_meta = CONTENT_TYPES.get(entry["content_type"], {})
                        st.markdown(f"{ct_meta.get('icon','📄')} **{entry['topic']}**")
                        if entry.get("notes"): st.caption(entry["notes"])
                    with cs2:
                        new_s = st.selectbox("Status", STATUS_OPTIONS,
                            index=STATUS_OPTIONS.index(entry["status"]) if entry["status"] in STATUS_OPTIONS else 0,
                            key=f"s_{entry['id']}")
                        if new_s != entry["status"]: calendar.update_status(entry["id"], new_s); st.rerun()
                    with cd:
                        if st.button("🗑️", key=f"cd_{entry['id']}"): calendar.delete_entry(entry["id"]); st.rerun()

    with sub_add:
        c1, c2 = st.columns(2)
        with c1:
            cal_date = st.date_input("Data", value=date.today(), key="cal_add_date")
            cal_topic = st.text_input("Tema", placeholder="Ex: Alta da Selic")
        with c2:
            cal_type = st.selectbox("Tipo", list(CONTENT_TYPES.keys()), format_func=lambda x: calendar.get_content_label(x))
            cal_status = st.selectbox("Status", STATUS_OPTIONS)
        cal_notes = st.text_area("Notas (opcional)", height=60)
        if st.button("➕ Adicionar", type="primary", use_container_width=True):
            if not cal_topic.strip(): st.warning("Digite o tema.")
            else:
                calendar.add_entry(scheduled_date=cal_date.isoformat(), content_type=cal_type,
                    topic=cal_topic, notes=cal_notes, status=cal_status)
                st.success(f"✅ Adicionado para {cal_date.strftime('%d/%m/%Y')}"); st.rerun()


# ===============================================================
# TEMPLATES
# ===============================================================
with tab_templates:
    st.header("🔖 Templates Salvos")
    from tools.template_manager import AGENT_FIELDS

    sub_tview, sub_tsave = st.tabs(["📋 Meus templates", "💾 Salvar novo"])

    with sub_tview:
        if not templates.has_templates():
            st.info("Nenhum template salvo. Use 'Salvar novo' para começar.")
        else:
            for ag in templates.get_agents():
                names = templates.get_agent_template_names(ag)
                if not names: continue
                st.subheader(templates.get_agent_label(ag))
                for tname in names:
                    with st.expander(f"🔖 {tname}  —  {templates.get_template_date(ag, tname)}"):
                        desc = templates.get_template_description(ag, tname)
                        if desc: st.caption(desc)
                        cfg_t = templates.load_template(ag, tname)
                        if cfg_t: st.json(cfg_t)
                        if st.button("🗑️ Remover", key=f"dt_{ag}_{tname}"):
                            templates.delete_template(ag, tname); st.success("Removido."); st.rerun()

    with sub_tsave:
        t_agent = st.selectbox("Agente", templates.get_agents(), format_func=templates.get_agent_label)
        t_name  = st.text_input("Nome do template", placeholder="Ex: Post Selic — tom formal")
        t_desc  = st.text_area("Descrição (opcional)", height=60)
        t_config = {}
        for field in AGENT_FIELDS.get(t_agent, []):
            t_config[field] = st.text_input(field.replace("_", " ").title(), key=f"tf_{field}")
        if st.button("💾 Salvar", type="primary", use_container_width=True):
            if not t_name.strip(): st.warning("Dê um nome ao template.")
            else:
                templates.save_template(agent=t_agent, name=t_name, config=t_config, description=t_desc)
                st.success(f"✅ Template '{t_name}' salvo!")


# ===============================================================
# MÉTRICAS
# ===============================================================
with tab_dashboard:
    st.header("📈 Dashboard de Uso")
    total = metrics.total_generations()
    if total == 0:
        st.info("Nenhuma geração registrada. Comece usando os agentes!")
    else:
        try:
            import plotly.express as px

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total gerado", total)
            c2.metric("Chars gerados", f"{metrics.total_chars_generated():,}")
            c3.metric("Taxa de sucesso", f"{metrics.success_rate()}%")
            c4.metric("Sequência", f"{metrics.streak_days()} dias")

            st.divider()
            ca, cb = st.columns(2)
            with ca:
                st.subheader("Por agente")
                by_a = metrics.by_agent()
                if by_a:
                    fig = px.bar(x=list(by_a.values()), y=list(by_a.keys()), orientation="h",
                        color=list(by_a.values()), color_continuous_scale="Blues",
                        labels={"x": "Gerações", "y": "Agente"})
                    fig.update_layout(showlegend=False, height=280, margin=dict(l=0,r=0,t=10,b=0))
                    st.plotly_chart(fig, use_container_width=True)
            with cb:
                st.subheader("Por tipo de conteúdo")
                by_t = metrics.by_content_type()
                if by_t:
                    fig2 = px.pie(names=list(by_t.keys()), values=list(by_t.values()), hole=0.4)
                    fig2.update_layout(height=280, margin=dict(l=0,r=0,t=10,b=0))
                    st.plotly_chart(fig2, use_container_width=True)

            st.subheader("Gerações por dia (últimos 30 dias)")
            by_d = metrics.by_day(30)
            if by_d:
                fig3 = px.bar(x=list(by_d.keys()), y=list(by_d.values()), labels={"x":"Data","y":"Gerações"})
                fig3.update_layout(height=200, margin=dict(l=0,r=0,t=10,b=0))
                st.plotly_chart(fig3, use_container_width=True)

            st.subheader("🕐 Tópicos recentes")
            for t in metrics.recent_topics(8):
                st.markdown(f"• {t}")

        except ImportError:
            st.warning("Instale plotly: `pip install plotly`")
            st.json({"por_agente": metrics.by_agent(), "por_tipo": metrics.by_content_type()})


# ===============================================================
# AGENDAMENTO
# ===============================================================
with tab_scheduler:
    st.header("⚙️ Agendamento Automático")
    import scheduler as sched_mod
    import yaml as _yaml

    _cfg_path = Path("config.yaml")
    _cfg = _yaml.safe_load(_cfg_path.read_text(encoding="utf-8"))
    _sc = _cfg.get("scheduler", {})

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Configuração")
        enabled  = st.toggle("Habilitado", value=_sc.get("enabled", False))
        news_t   = st.text_input("Horário newsletter (HH:MM)", value=_sc.get("newsletter_time", "08:00"))
        DAY_MAP  = {"Seg":0,"Ter":1,"Qua":2,"Qui":3,"Sex":4,"Sáb":5,"Dom":6}
        sel_days = st.multiselect("Dias da newsletter", list(DAY_MAP.keys()),
            default=[k for k,v in DAY_MAP.items() if v in _sc.get("newsletter_days",[1,3,5])])
        if st.button("💾 Salvar configuração", use_container_width=True):
            _cfg["scheduler"]["enabled"] = enabled
            _cfg["scheduler"]["newsletter_time"] = news_t
            _cfg["scheduler"]["newsletter_days"] = [DAY_MAP[d] for d in sel_days]
            _cfg_path.write_text(_yaml.dump(_cfg, allow_unicode=True, default_flow_style=False), encoding="utf-8")
            st.success("✅ Salvo!")

    with c2:
        st.subheader("Controles")
        if sched_mod.is_running():
            st.success("🟢 Scheduler **ativo**")
            if st.button("⏹️ Parar", use_container_width=True):
                sched_mod.stop_scheduler(); st.rerun()
        else:
            st.warning("🔴 Scheduler **inativo**")
            if st.button("▶️ Iniciar", type="primary", use_container_width=True):
                ok = sched_mod.start_scheduler()
                st.success("✅ Iniciado!") if ok else st.error("Verifique APScheduler e config.")
                st.rerun()

        st.divider()
        st.subheader("Execução manual")
        cn, cp2 = st.columns(2)
        with cn:
            if st.button("📰 Newsletter agora", use_container_width=True):
                sched_mod.run_now_newsletter(); st.success("Iniciada!")
        with cp2:
            m_topic = st.text_input("Tema (opcional)", key="sched_t")
            if st.button("🚀 Pipeline agora", use_container_width=True):
                sched_mod.run_now_pipeline(topic=m_topic); st.success("Iniciado!")

    st.divider()
    st.subheader("📋 Log")
    for entry in sched_mod.get_log()[:20]:
        icon = "✅" if entry["success"] else "❌"
        st.markdown(f"`{entry['timestamp']}` {icon} {entry['message']}")
