from __future__ import annotations
from typing import TypedDict, Literal, List, Dict, Any
from datetime import datetime
from .utils import br_to_iso

UF_VALIDAS = {
    "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
    "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"
}
EVENTOS_VALIDOS = {"COLHEITA","TRANSPORTE","ARMAZENAGEM","INSPECAO"}

EventoTipo = Literal["COLHEITA", "TRANSPORTE", "ARMAZENAGEM", "INSPECAO"]

class Evento(TypedDict):
    tipo: EventoTipo
    data: str
    local: str
    responsavel: str
    observacoes: str

class Lote(TypedDict):
    id: int
    produto: str
    produtor: str
    origem_uf: str
    data_colheita: str
    peso_kg: float
    carbono_neutro: bool
    agua_reuso: bool
    status: str
    eventos: List[Evento]

def validar_str_nao_vazia(s: str, campo: str) -> str:
    s2 = s.strip()
    if not s2:
        raise ValueError(f"{campo} não pode ser vazio.")
    return s2

def validar_uf(uf: str) -> str:
    uf2 = uf.strip().upper()
    if uf2 not in UF_VALIDAS:
        raise ValueError("UF inválida.")
    return uf2

def validar_peso(p: str | float | int) -> float:
    try:
        f = float(p)
        if f < 0:
            raise ValueError
        return f
    except Exception:
        raise ValueError("Peso inválido (use número >= 0).")

def validar_data_br(data_br: str) -> str:
    return br_to_iso(data_br)

def validar_evento_dict(ev: Dict[str, Any]) -> None:
    for k in ["tipo", "data", "local", "responsavel", "observacoes"]:
        if k not in ev:
            raise ValueError(f"Evento faltando campo: {k}")
    if ev["tipo"].upper() not in EVENTOS_VALIDOS:
        raise ValueError("Tipo de evento inválido.")
    try:
        datetime.strptime(ev["data"], "%Y-%m-%d")
    except Exception:
        raise ValueError("Data do evento inválida (use ISO YYYY-MM-DD)")

def validar_lote_dict(l: Dict[str, Any]) -> None:
    obrig = ["id","produto","produtor","origem_uf","data_colheita","peso_kg",
             "carbono_neutro","agua_reuso","status","eventos"]
    for k in obrig:
        if k not in l:
            raise ValueError(f"Lote faltando campo: {k}")
    if l["origem_uf"] not in UF_VALIDAS:
        raise ValueError("UF inválida.")
    try:
        datetime.strptime(l["data_colheita"], "%Y-%m-%d")
    except Exception:
        raise ValueError("Data de colheita inválida (ISO YYYY-MM-DD).")
    if float(l["peso_kg"]) < 0:
        raise ValueError("Peso não pode ser negativo.")
    if not isinstance(l["eventos"], list):
        raise ValueError("Eventos deve ser lista.")
    for ev in l["eventos"]:
        validar_evento_dict(ev)
