import os, json, requests
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL   = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

API_URL = "https://api.deepseek.com/v1/chat/completions"

def _jdir(job_id: str) -> Path:
    d = DATA_DIR / "jobs" / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def _make_prompt_ru(transcript_text: str) -> list:
    system = (
        "Ты помощник, делающий структурированные резюме русскоязычных встреч. "
        "Отвечай кратко и по делу. Верни строго JSON без лишнего текста."
    )
    user = (
        "Сформируй:\n"
        "1) meeting_summary (5–8 предложений)\n"
        "2) key_points (маркеры)\n"
        "3) action_items (owner, task, due)\n"
        "4) risks (список)\n\n"
        "Верни строго JSON вида:\n"
        "{\n"
        "  \"meeting_summary\": \"...\",\n"
        "  \"key_points\": [\"...\"],\n"
        "  \"action_items\": [{\"owner\":\"\",\"task\":\"\",\"due\":\"\"}],\n"
        "  \"risks\": [\"...\"]\n"
        "}\n\n"
        f"Транскрипт:\n{transcript_text}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

def summarize_job(job_id: str):
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")

    jdir = _jdir(job_id)
    tj = jdir / "transcript.json"
    if not tj.exists():
        raise FileNotFoundError("transcript.json not found")

    transcript = json.loads(tj.read_text("utf-8"))
    text = transcript.get("text", "")

    messages = _make_prompt_ru(text)

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json={"model": DEEPSEEK_MODEL, "messages": messages, "temperature": 0.2},
        timeout=90
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Попытка распарсить в JSON (если LLM вернёт JSON как строку)
    try:
        summary_json = json.loads(content)
    except Exception:
        # fallback — завернем как поле raw
        summary_json = {"raw": content}

    (jdir / "summary.json").write_text(json.dumps(summary_json, ensure_ascii=False, indent=2), "utf-8")
    (jdir / "summary.txt").write_text(
        summary_json.get("meeting_summary", content),
        "utf-8"
    )
    return {"ok": True}
