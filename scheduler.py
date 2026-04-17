"""
scheduler.py — Agendamento automático de tarefas usando APScheduler.
Roda em background quando habilitado no config.yaml.
"""

from __future__ import annotations
import threading
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

# Log simples de execuções agendadas
_schedule_log: list[dict] = []
_scheduler_instance: Optional[object] = None
_lock = threading.Lock()


def _load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _log(message: str, success: bool = True):
    _schedule_log.append({
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "message": message,
        "success": success,
    })
    if len(_schedule_log) > 100:
        _schedule_log.pop(0)


def _run_newsletter(on_complete: Optional[Callable] = None):
    """Job: executa o agente Redator."""
    _log("🔄 Iniciando newsletter agendada...")
    try:
        from manager import AgentManager
        mgr = AgentManager()
        result = mgr.run_news_writer()
        msg = f"✅ Newsletter gerada: {result.get('filepath', 'N/A')}"
        _log(msg, success=True)
        if on_complete:
            on_complete(msg)
    except Exception as e:
        _log(f"❌ Erro na newsletter agendada: {e}", success=False)


def _run_pipeline(topic: str = "", on_complete: Optional[Callable] = None):
    """Job: executa o pipeline completo."""
    _log("🔄 Iniciando pipeline completo agendado...")
    try:
        from manager import AgentManager
        mgr = AgentManager()
        mgr.run_full_pipeline(main_topic=topic)
        _log("✅ Pipeline completo executado com sucesso.", success=True)
        if on_complete:
            on_complete("✅ Pipeline completo executado.")
    except Exception as e:
        _log(f"❌ Erro no pipeline agendado: {e}", success=False)


def start_scheduler(config: Optional[dict] = None) -> bool:
    """Inicia o scheduler em background com base no config.yaml."""
    global _scheduler_instance

    if not APSCHEDULER_AVAILABLE:
        _log("❌ APScheduler não instalado. Execute: pip install APScheduler", False)
        return False

    with _lock:
        if _scheduler_instance and _scheduler_instance.running:
            return True

        cfg = config or _load_config()
        sched_cfg = cfg.get("scheduler", {})

        if not sched_cfg.get("enabled", False):
            _log("ℹ️ Scheduler desabilitado no config.yaml.")
            return False

        tz = sched_cfg.get("timezone", "America/Sao_Paulo")
        scheduler = BackgroundScheduler(timezone=tz)

        # Job da newsletter
        news_time = sched_cfg.get("newsletter_time", "08:00")
        news_days = sched_cfg.get("newsletter_days", [1, 3, 5])
        news_hour, news_min = map(int, news_time.split(":"))
        days_of_week = ",".join(str(d) for d in news_days)

        scheduler.add_job(
            _run_newsletter,
            trigger=CronTrigger(
                day_of_week=days_of_week,
                hour=news_hour,
                minute=news_min,
                timezone=tz,
            ),
            id="newsletter_job",
            replace_existing=True,
        )
        _log(f"📅 Newsletter agendada: {news_time} nos dias {news_days}")

        # Job do pipeline (opcional)
        pipeline_time = sched_cfg.get("pipeline_time")
        pipeline_days = sched_cfg.get("pipeline_days", [])
        if pipeline_time and pipeline_days:
            p_hour, p_min = map(int, pipeline_time.split(":"))
            p_days = ",".join(str(d) for d in pipeline_days)
            scheduler.add_job(
                _run_pipeline,
                trigger=CronTrigger(
                    day_of_week=p_days,
                    hour=p_hour,
                    minute=p_min,
                    timezone=tz,
                ),
                id="pipeline_job",
                replace_existing=True,
            )
            _log(f"📅 Pipeline agendado: {pipeline_time} nos dias {pipeline_days}")

        scheduler.start()
        _scheduler_instance = scheduler
        _log("✅ Scheduler iniciado com sucesso.")
        return True


def stop_scheduler() -> bool:
    """Para o scheduler."""
    global _scheduler_instance
    with _lock:
        if _scheduler_instance and _scheduler_instance.running:
            _scheduler_instance.shutdown(wait=False)
            _scheduler_instance = None
            _log("⏹️ Scheduler parado.")
            return True
    return False


def is_running() -> bool:
    return bool(_scheduler_instance and _scheduler_instance.running)


def get_log() -> list[dict]:
    return list(reversed(_schedule_log))


def get_next_runs() -> list[dict]:
    """Retorna próximas execuções agendadas."""
    if not _scheduler_instance or not _scheduler_instance.running:
        return []
    jobs = []
    for job in _scheduler_instance.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "label": "Newsletter" if "newsletter" in job.id else "Pipeline",
            "next_run": next_run.strftime("%d/%m/%Y %H:%M") if next_run else "N/A",
        })
    return jobs


def run_now_newsletter():
    """Executa newsletter imediatamente (fora do horário agendado)."""
    thread = threading.Thread(target=_run_newsletter, daemon=True)
    thread.start()
    _log("▶️ Newsletter executada manualmente.")


def run_now_pipeline(topic: str = ""):
    """Executa pipeline imediatamente."""
    thread = threading.Thread(target=lambda: _run_pipeline(topic=topic), daemon=True)
    thread.start()
    _log("▶️ Pipeline executado manualmente.")
