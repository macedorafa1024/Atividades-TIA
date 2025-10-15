from __future__ import annotations
from typing import Dict, Any, Callable
from dotenv import load_dotenv

from .casos_uso import LOTES, cadastrar_lote, registrar_evento, listar_lotes
from .relatorios import kpis, formatar_relatorio
from .persistencia_json import carregar_json_validado, salvar_json_seguro, exportar_csv_lotes
from .utils import DATA_PATH, iso_to_br, log
from .dominio import (
    validar_str_nao_vazia, validar_uf, validar_data_br, validar_peso
)

DB = None

# ==============================
# Conexão opcional com Oracle
# ==============================
def try_connect_db():
    global DB
    try:
        from .persistencia_oracle import conectar_oracle_from_env
        DB = conectar_oracle_from_env()
        log("Oracle conectado.")
    except Exception as e:
        DB = None
        log(f"Oracle indisponível ({e}); seguindo apenas com JSON.")

def boot():
    load_dotenv()
    try:
        dados = carregar_json_validado(DATA_PATH)
        LOTES.clear()
        LOTES.extend(dados)
    except Exception as e:
        print("⚠️ Falha ao carregar data/dados.json (veja logs/app.log).")
        log(f"ERRO carregar: {e}")
    try_connect_db()

# ==============================
# Entradas com revalidação
# ==============================
def ask_until_valid(prompt: str, validator: Callable[[str], Any]) -> Any:
    """Pergunta e usa uma função validadora que retorna o valor convertido
    (ou lança ValueError). Repete até ficar válido."""
    while True:
        txt = input(prompt).strip()
        try:
            return validator(txt)
        except ValueError as e:
            print(f"⚠️ {e}")

def ask_str(field: str) -> str:
    return ask_until_valid(f"{field}: ", lambda s: validar_str_nao_vazia(s, field))

def ask_uf() -> str:
    return ask_until_valid("UF (ex: SP): ", validar_uf)

def ask_data_br(label: str) -> str:
    # retorna ISO; a validação já converte BR -> ISO
    return ask_until_valid(f"{label} (DD/MM/YYYY): ", validar_data_br)

def ask_peso() -> float:
    return ask_until_valid("Peso (kg): ", validar_peso)

def ask_bool(msg: str) -> bool:
    while True:
        r = input(msg + " [s/n]: ").strip().lower()
        if r in ("s", "sim"): return True
        if r in ("n", "nao", "não"): return False
        print("⚠️ Responda com 's' ou 'n'.")

# ==============================
# Ações do menu (com reentrada)
# ==============================
def acao_cadastrar_lote():
    # Coleta campo a campo, validando e repetindo quando necessário
    produto = ask_str("Produto")
    produtor = ask_str("Produtor")
    uf = ask_uf()
    data_iso = ask_data_br("Data da colheita")   # já volta ISO
    peso = ask_peso()
    agua_reuso = ask_bool("Usa reuso de água?")
    carbono_neutro = ask_bool("É carbono neutro?")

    dados: Dict[str, Any] = {
        "produto": produto,
        "produtor": produtor,
        "origem_uf": uf,
        "data_colheita_br": iso_to_br(data_iso),  # cadastrar_lote espera BR; convertemos de volta
        "peso_kg": str(peso),
        "agua_reuso": agua_reuso,
        "carbono_neutro": carbono_neutro
    }

    try:
        lote = cadastrar_lote(dados)
        LOTES.append(lote)
        salvar_json_seguro(LOTES, DATA_PATH)
        print(f"✅ Lote {lote['id']} cadastrado.")
        if DB:
            from .persistencia_oracle import inserir_lote
            novo_id = inserir_lote(DB, lote)
            lote["id"] = novo_id
            salvar_json_seguro(LOTES, DATA_PATH)
    except Exception as e:
        print("⚠️ Erro inesperado ao cadastrar:", e)
        log(f"ERRO cadastrar: {e}")

def acao_registrar_evento():
    # ID do lote (validar que é inteiro e existe)
    while True:
        try:
            lote_id = int(input("ID do lote: ").strip())
            # checagem básica de existência
            if any(l["id"] == lote_id for l in LOTES):
                break
            print("⚠️ Lote não encontrado. Tente novamente.")
        except ValueError:
            print("⚠️ Digite um número inteiro para o ID.")

    # Dados do evento com validação e reentrada
    tipo = ask_until_valid(
        "Tipo (COLHEITA/TRANSPORTE/ARMAZENAGEM/INSPECAO): ",
        lambda s: s.strip().upper() if s.strip().upper() in {"COLHEITA","TRANSPORTE","ARMAZENAGEM","INSPECAO"} else (_ for _ in ()).throw(ValueError("Tipo de evento inválido."))
    )
    data_iso = ask_data_br("Data do evento")     # volta ISO
    local = ask_str("Local")
    responsavel = ask_str("Responsável")
    observacoes = input("Observações: ").strip()

    ev_br = {
        "tipo": tipo,
        "data_br": iso_to_br(data_iso),  # registrar_evento espera BR
        "local": local,
        "responsavel": responsavel,
        "observacoes": observacoes
    }

    try:
        ok = registrar_evento(lote_id, ev_br)
        if not ok:
            print("❌ Lote não encontrado (concorrência).")
            return
        salvar_json_seguro(LOTES, DATA_PATH)
        print("✅ Evento registrado.")
        if DB:
            from .persistencia_oracle import inserir_evento
            from .dominio import validar_data_br
            inserir_evento(DB, lote_id, {
                "tipo": tipo,
                "data": validar_data_br(ev_br["data_br"]),
                "local": local,
                "responsavel": responsavel,
                "observacoes": observacoes
            })
    except Exception as e:
        print("⚠️ Erro inesperado ao registrar evento:", e)
        log(f"ERRO evento: {e}")

def acao_listar_lotes():
    uf = input("Filtrar por UF (enter para ignorar): ").strip().upper()
    status = input("Filtrar por Status (enter para ignorar): ").strip().upper()
    filtros = {}
    if uf: filtros["origem_uf"] = uf
    if status: filtros["status"] = status
    lista = listar_lotes(filtros)
    print("\n--- LOTES ---")
    for l in lista:
        print(f"ID {l['id']} | {l['produto']} | {l['produtor']} | {l['origem_uf']} | "
              f"colheita {iso_to_br(l['data_colheita'])} | peso {l['peso_kg']} kg | "
              f"água_reuso={l['agua_reuso']} | carbono_neutro={l['carbono_neutro']} | {l['status']}")
    print("-------------\n")

def acao_relatorio():
    r = kpis(LOTES)
    print()
    print(formatar_relatorio(r))
    print()

def acao_exportar_importar():
    sub = input("[E]xportar CSV ou [I]mportar JSON? ").strip().lower()
    if sub.startswith("e"):
        caminho = input("Caminho do CSV (ex: lotes.csv): ").strip() or "lotes.csv"
        try:
            exportar_csv_lotes(LOTES, caminho)
            print(f"✅ CSV gerado: {caminho}")
        except Exception as e:
            print("⚠️ Erro ao exportar CSV:", e)
    else:
        try:
            novos = carregar_json_validado(DATA_PATH)
            LOTES.clear(); LOTES.extend(novos)
            print("✅ Importado de data/dados.json")
        except Exception as e:
            print("⚠️ Erro ao importar JSON:", e)

# ==============================
# Menu
# ==============================
def menu():
    boot()
    while True:
        print("""
[Rastreabilidade Sustentável]
1) Cadastrar lote
2) Registrar evento
3) Listar lotes
4) Relatório de sustentabilidade
5) Exportar CSV / Importar JSON
0) Sair
""")
        op = input("Escolha: ").strip()
        if op == "1": acao_cadastrar_lote()
        elif op == "2": acao_registrar_evento()
        elif op == "3": acao_listar_lotes()
        elif op == "4": acao_relatorio()
        elif op == "5": acao_exportar_importar()
        elif op == "0":
            print("Até mais!")
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    menu()
