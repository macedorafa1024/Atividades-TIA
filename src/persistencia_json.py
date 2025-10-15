from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from typing import List, Dict, Any

from .dominio import validar_lote_dict
from .utils import DATA_PATH, log


# ---------- Funções de integridade ----------
def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _save_hash(path: str) -> None:
    dig = _sha256(path)
    with open(path + ".sha256", "w", encoding="utf-8") as f:
        f.write(dig + "\n")

def conferir_hash(path: str) -> bool:
    try:
        with open(path + ".sha256", "r", encoding="utf-8") as f:
            exp = f.read().strip()
        return exp == _sha256(path)
    except FileNotFoundError:
        return False

# ---------- Backup e escrita segura ----------
def _backup_rotativo(path: str, keep: int = 3) -> None:
    if not os.path.exists(path):
        return
    ts = time.strftime("%Y%m%d-%H%M%S")
    bk = f"{path}.{ts}.bak"
    os.replace(path, bk)
    base = os.path.basename(path)
    bks = sorted([p for p in os.listdir(os.path.dirname(path) or ".")
                  if p.startswith(base + ".") and p.endswith(".bak")], reverse=True)
    for velho in bks[keep:]:
        try:
            os.remove(os.path.join(os.path.dirname(path), velho))
        except Exception:
            pass

def _write_atomic(path: str, content: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)

# ---------- Carregar / Salvar ----------
def carregar_json_validado(path: str = DATA_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        log(f"carregar_json: {path} não existe → []")
        return []
    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)
    if not isinstance(dados, list):
        raise ValueError("Raiz do JSON deve ser lista.")
    for l in dados:
        validar_lote_dict(l)
    ids = [l["id"] for l in dados]
    if len(ids) != len(set(ids)):
        raise ValueError("IDs duplicados no JSON.")
    integ = conferir_hash(path)
    log(f"carregar_json: OK ({len(dados)}) | integridade={'OK' if integ else 'N/A'}")
    return dados

def salvar_json_seguro(lotes: List[Dict[str, Any]], path: str = DATA_PATH) -> None:
    """

    :rtype: None
    """
    for l in lotes:
        validar_lote_dict(l)
    _backup_rotativo(path)
    content = json.dumps(lotes, ensure_ascii=False, indent=2)
    _write_atomic(path, content)
    _save_hash(path)
    log(f"salvar_json: OK ({len(lotes)} lotes)")

# ---------- Exportar para CSV ----------
def exportar_csv_lotes(lotes: List[Dict[str, Any]], csv_path: str) -> None:
    campos = ["id","produto","produtor","origem_uf","data_colheita","peso_kg",
              "carbono_neutro","agua_reuso","status","qtd_eventos"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        for l in lotes:
            w.writerow({
                "id": l["id"],
                "produto": l["produto"],
                "produtor": l["produtor"],
                "origem_uf": l["origem_uf"],
                "data_colheita": l["data_colheita"],
                "peso_kg": l["peso_kg"],
                "carbono_neutro": int(bool(l["carbono_neutro"])),
                "agua_reuso": int(bool(l["agua_reuso"])),
                "status": l["status"],
                "qtd_eventos": len(l["eventos"])
            })
    log(f"exportar_csv: OK → {csv_path}")
