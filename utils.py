from __future__ import annotations
import os
from datetime import datetime, date
from typing import Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

DATA_PATH = os.path.join(DATA_DIR, "dados.json")
LOG_PATH = os.path.join(LOG_DIR, "app.log")

# Datas BR <-> ISO
def br_to_iso(date_br: str) -> str:
    try:
        return datetime.strptime(date_br, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Data inválida. Use DD/MM/YYYY.")

def iso_to_br(date_iso: str) -> str:
    return datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")

def iso_to_date(date_iso: str) -> date:
    return datetime.strptime(date_iso, "%Y-%m-%d").date()

# Booleans para Oracle
def b2sn(b: bool) -> str:
    return "S" if b else "N"

def sn2b(s: Optional[str]) -> bool:
    if not s:
        return False
    return s.strip().upper() == "S"

# Log
def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")
