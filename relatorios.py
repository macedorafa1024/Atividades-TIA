from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime
from .dominio import Lote
from .utils import iso_to_date

def kpis(lotes: List[Lote]) -> Dict[str, Any]:
    total = len(lotes)
    if total == 0:
        return {"total": 0, "pct_agua_reuso": 0.0, "pct_carbono_neutro": 0.0,
                "peso_total_kg": 0.0, "por_uf": {}, "lotes_sem_evento_7d": 0}
    agua = sum(1 for l in lotes if l["agua_reuso"])
    carb = sum(1 for l in lotes if l["carbono_neutro"])
    peso_total = sum(l["peso_kg"] for l in lotes)
    por_uf: Dict[str, int] = {}
    for l in lotes:
        por_uf[l["origem_uf"]] = por_uf.get(l["origem_uf"], 0) + 1

    hoje = datetime.now().date()
    sem_evento = 0
    for l in lotes:
        d_col = iso_to_date(l["data_colheita"])
        ult = d_col if not l["eventos"] else datetime.strptime(l["eventos"][-1]["data"], "%Y-%m-%d").date()
        if (hoje - ult).days > 7:
            sem_evento += 1

    return {
        "total": total,
        "pct_agua_reuso": round(100*agua/total, 2),
        "pct_carbono_neutro": round(100*carb/total, 2),
        "peso_total_kg": round(peso_total, 2),
        "por_uf": por_uf,
        "lotes_sem_evento_7d": sem_evento
    }

def formatar_relatorio(k: Dict[str, Any]) -> str:
    linhas = [
        "=== RELATÓRIO DE SUSTENTABILIDADE ===",
        f"Total de lotes: {k['total']}",
        f"% água de reuso: {k['pct_agua_reuso']}%",
        f"% carbono neutro: {k['pct_carbono_neutro']}%",
        f"Peso total (kg): {k['peso_total_kg']}",
        f"Lotes sem evento > 7 dias: {k['lotes_sem_evento_7d']}",
        "Distribuição por UF:"
    ]
    for uf, qtd in k["por_uf"].items():
        linhas.append(f"  {uf}: {qtd}")
    linhas.append("======================================")
    return "\n".join(linhas)
