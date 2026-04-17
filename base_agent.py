"""
base_agent.py — Classe base compartilhada por todos os agentes.
"""

from __future__ import annotations
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Any

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def detect_model(preferred: str, base_url: str) -> str:
    """
    Detecta automaticamente o modelo disponivel no Ollama.
    Compativel com diferentes versoes da biblioteca ollama-python.
    """
    if not OLLAMA_AVAILABLE:
        return preferred
    try:
        client = ollama.Client(host=base_url)
        response = client.list()

        # A biblioteca ollama pode retornar objetos ou dicts dependendo da versao
        # Tentamos extrair o nome de cada modelo de forma defensiva
        available = []
        models_raw = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])

        for m in models_raw:
            # Objeto com atributo .model ou .name, ou dict com chave "model"/"name"
            if hasattr(m, "model"):
                available.append(m.model)
            elif hasattr(m, "name"):
                available.append(m.name)
            elif isinstance(m, dict):
                name = m.get("model") or m.get("name", "")
                if name:
                    available.append(name)

        if not available:
            print("[AVISO] Nenhum modelo encontrado no Ollama. Instale com: ollama pull mistral:7b")
            return preferred

        # Verifica se o preferido (ou variante) esta disponivel
        pref_base = preferred.split(":")[0]
        for m in available:
            if pref_base in m:
                return m

        # Fallback: usa o primeiro disponivel
        fallback = available[0]
        print(f"[INFO] Modelo '{preferred}' nao encontrado. Usando '{fallback}'.")
        return fallback

    except Exception as e:
        print(f"[AVISO] Erro ao listar modelos Ollama: {e}")
        return preferred


def list_available_models(base_url: str) -> list[str]:
    """Retorna lista de modelos instalados — usado pela UI."""
    if not OLLAMA_AVAILABLE:
        return []
    try:
        client = ollama.Client(host=base_url)
        response = client.list()
        models_raw = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
        result = []
        for m in models_raw:
            if hasattr(m, "model"):
                result.append(m.model)
            elif hasattr(m, "name"):
                result.append(m.name)
            elif isinstance(m, dict):
                name = m.get("model") or m.get("name", "")
                if name:
                    result.append(name)
        return result
    except Exception:
        return []


class BaseAgent:
    name: str = "Agente Base"
    system_prompt: str = "Voce e um assistente util."

    def __init__(self):
        self.config = load_config()
        self.ollama_cfg = self.config["ollama"]
        self.model = detect_model(
            preferred=self.ollama_cfg["model"],
            base_url=self.ollama_cfg["base_url"],
        )
        self.temperature = self.ollama_cfg.get("temperature", 0.7)
        self.history: list[dict] = []
        self.outputs_dir = Path(__file__).parent.parent / self.config["outputs"]["directory"].lstrip("./")
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def _chat(self, user_message: str, extra_context: str = "") -> str:
        if not OLLAMA_AVAILABLE:
            return "[ERRO] Biblioteca 'ollama' nao instalada. Execute: pip install ollama"

        messages = [{"role": "system", "content": self.system_prompt}]
        if extra_context:
            messages.append({"role": "user", "content": f"Contexto adicional:\n{extra_context}"})
            messages.append({"role": "assistant", "content": "Entendido. Vou usar esse contexto."})

        messages += self.history
        messages.append({"role": "user", "content": user_message})

        try:
            client = ollama.Client(host=self.ollama_cfg["base_url"])
            response = client.chat(
                model=self.model,
                messages=messages,
                options={"temperature": self.temperature},
            )
            # Compativel com objeto ou dict
            if isinstance(response, dict):
                reply = response["message"]["content"]
            else:
                reply = response.message.content

            self.history.append({"role": "user", "content": user_message})
            self.history.append({"role": "assistant", "content": reply})
            return reply

        except Exception as e:
            return f"[ERRO Ollama] {type(e).__name__}: {e}"

    def reset_history(self):
        self.history = []

    def _save_output(self, content: str, prefix: str, extension: str = "md") -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filepath = self.outputs_dir / f"{prefix}_{timestamp}.{extension}"
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def _save_json(self, data: Any, prefix: str) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filepath = self.outputs_dir / f"{prefix}_{timestamp}.json"
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return filepath

    def run(self, **kwargs) -> dict:
        raise NotImplementedError("Cada agente deve implementar o metodo run()")

    def status(self) -> dict:
        return {
            "agent": self.name,
            "model": self.model,
            "history_turns": len(self.history) // 2,
        }
