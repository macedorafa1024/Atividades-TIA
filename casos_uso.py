from __future__ import annotations
from typing import List, Dict, Any, Optional
from .dominio import (
    Lote, Evento,
    validar_str_nao_vazia, validar_uf, validar_peso,
    validar_data_br, validar_lote_dict
)


LOTES: List[Lote] = []

def proximo_id() -> int:
    return max((l["id"] for l in LOTES), default=0) + 1

def cadastrar_lote(dados: Dict[str, Any]) -> Lote:
    produto = validar_str_nao_vazia(dados["produto"], "Produto")
    produtor = validar_str_nao_vazia(dados["produtor"], "Produtor")
    uf = validar_uf(dados["origem_uf"])
    data_iso = validar_data_br(dados["data_colheita_br"])
    peso = validar_peso(dados["peso_kg"])
    agua_reuso = bool(dados.get("agua_reuso", False))
    carbono_neutro = bool(dados.get("carbono_neutro", False))

    lote: Lote = Lote(
        id=proximo_id(),
        produto=produto,
        produtor=produtor,
        origem_uf=uf,
        data_colheita=data_iso,
        peso_kg=peso,
        carbono_neutro=carbono_neutro,
        agua_reuso=agua_reuso,
        status="EM_PROCESSAMENTO",
        eventos=[]
    )
    validar_lote_dict(lote)
    return lote

def registrar_evento(lote_id: int, ev_br: Dict[str, Any]) -> bool:
    tipo = validar_str_nao_vazia(ev_br["tipo"], "Tipo").upper()
    data_iso = validar_data_br(ev_br["data_br"])
    local = validar_str_nao_vazia(ev_br["local"], "Local")
    resp = validar_str_nao_vazia(ev_br["responsavel"], "Responsável")
    obs = ev_br.get("observacoes","").strip()

    for l in LOTES:
        if l["id"] == lote_id:
            evento: Evento = Evento(tipo=tipo, data=data_iso, local=local, responsavel=resp, observacoes=obs)
            l["eventos"].append(evento)
            if tipo == "INSPECAO":
                l["status"] = "PRONTO"
            return True
    return False

def listar_lotes(filtros: Optional[Dict[str, Any]] = None) -> List[Lote]:
    if not filtros:
        return LOTES
    res = LOTES
    if uf := filtros.get("origem_uf"):
        res = [l for l in res if l["origem_uf"] == uf.upper()]
    if status := filtros.get("status"):
        res = [l for l in res if l["status"].upper() == status.upper()]
    return res
