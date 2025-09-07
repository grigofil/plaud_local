#!/usr/bin/env python3
"""
Простой тестовый сервер для проверки
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/test")
def test():
    return {"status": "ok"}

if __name__ == "__main__":
    print("Запускаем тестовый сервер...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
