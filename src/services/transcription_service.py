import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import httpx

from src.config.settings import DATA_DIR, TRANSCRIBE_SERVER_URL

def jobs_dir(job_id: str) -> Path:
    """Get job directory path"""
    return DATA_DIR / "jobs" / job_id

def ensure_dirs(path: Path):
    """Ensure directories exist"""
    path.mkdir(parents=True, exist_ok=True)

async def send_to_transcribe_server(job_id: str, audio_path: str, language: str) -> bool:
    """Send audio file to transcription server via HTTP"""
    try:
        with open(audio_path, "rb") as audio_file:
            files = {"file": audio_file}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{TRANSCRIBE_SERVER_URL}/transcribe?job_id={job_id}&language={language}",
                    files=files,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    print(f"File successfully sent to transcription server for job_id: {job_id}")
                    return True
                else:
                    print(f"Error sending to transcription server: {response.status_code} - {response.text}")
                    return False
                    
    except Exception as e:
        print(f"Error sending to transcription server: {e}")
        return False

def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get job status"""
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        return {"status": "not_found"}
    
    transcript = jdir / "transcript.json"
    summary = jdir / "summary.json"
    
    if summary.exists():
        return {"status": "done"}
    if transcript.exists():
        return {"status": "transcribed_waiting_summary"}
    
    return {"status": "processing"}

def get_job_result(job_id: str) -> Dict[str, Any]:
    """Get job result"""
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        raise FileNotFoundError("Job not found")
    
    result = {"job_id": job_id}
    
    # Load transcript
    transcript_file = jdir / "transcript.json"
    if transcript_file.exists():
        try:
            result["transcript"] = json.loads(transcript_file.read_text("utf-8"))
        except Exception as e:
            result["transcript_error"] = f"transcript_read_error: {str(e)}"
    
    # Load summary
    summary_file = jdir / "summary.json"
    if summary_file.exists():
        try:
            result["summary"] = json.loads(summary_file.read_text("utf-8"))
        except Exception as e:
            result["summary_error"] = f"summary_read_error: {str(e)}"
    
    return result

def delete_job(job_id: str) -> bool:
    """Delete job and all related files"""
    jdir = jobs_dir(job_id)
    if not jdir.exists():
        return False
    
    try:
        import shutil
        shutil.rmtree(jdir)
        return True
    except Exception:
        return False