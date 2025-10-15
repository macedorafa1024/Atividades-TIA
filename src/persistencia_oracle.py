from __future__ import annotations
import os
from typing import List, Dict, Any, Optional

from .utils import b2sn, sn2b, iso_to_date, log

try:
    import oracledb
except Exception:
    oracledb = None  # permite que o app rode sem Oracle instalado

HOST     = os.getenv("ORACLE_HOST", "oracle.fiap.com.br")
PORT     = os.getenv("ORACLE_PORT", "1521")
SERVICE  = os.getenv("ORACLE_SERVICE", "ORCL")
USER     = os.getenv("ORACLE_USER", "rm566955")
PASSWORD = os.getenv("ORACLE_PASSWORD", "250500")

SCHEMA_QUERY = os.getenv("ORACLE_SCHEMA", "").strip()

AUTO_INIT = os.getenv("ORACLE_AUTO_INIT", "1").strip().lower() in ("1", "true", "yes")

def T(name: str) -> str:
    """Qualifica o nome da tabela com SCHEMA_QUERY, se definindo para consultas/CRUD.
    Use APENAS para SELECT/INSERT/UPDATE/DELETE. A criação é no usuário logado."""
    return f"{SCHEMA_QUERY}.{name}" if SCHEMA_QUERY else name


def conectar_oracle_from_env():
    """
    Conecta no Oracle com as variáveis do .env.
    Se AUTO_INIT estiver habilitado, cria as tabelas no usuário logado (se não existirem).
    """
    if oracledb is None:
        raise RuntimeError("Pacote 'oracledb' não está instalado. pip install oracledb")

    if not all([HOST, PORT, SERVICE, USER, PASSWORD]):
        raise RuntimeError("Variáveis ORACLE_* ausentes/invalidas no .env")

    dsn = f"{HOST}:{PORT}/{SERVICE}"  # formato FIAP: host:1521/SERVICE
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=dsn)
    conn.autocommit = False

    if AUTO_INIT:
        try:
            criar_tabelas_se_nao_existirem(conn)
        except Exception as e:
            # não impede o uso; apenas loga
            log(f"Oracle AUTO_INIT falhou: {e}")

    return conn


def _table_exists(conn, table_name: str) -> bool:
    # user_tables enxerga apenas o schema do USUÁRIO LOGADO
    sql = "SELECT COUNT(*) FROM user_tables WHERE table_name = :T"
    with conn.cursor() as cur:
        cur.execute(sql, {"T": table_name.upper()})
        (cnt,) = cur.fetchone()
        return cnt > 0

def _index_exists(conn, index_name: str) -> bool:
    sql = "SELECT COUNT(*) FROM user_indexes WHERE index_name = :I"
    with conn.cursor() as cur:
        cur.execute(sql, {"I": index_name.upper()})
        (cnt,) = cur.fetchone()
        return cnt > 0

def criar_tabelas_se_nao_existirem(conn) -> None:
    """Cria LOTE/EVENTO e índices se não existirem (no schema do usuário logado)."""
    with conn.cursor() as cur:
        # Tabela LOTE
        if not _table_exists(conn, "LOTE"):
            cur.execute("""
                CREATE TABLE LOTE (
                  ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                  PRODUTO         VARCHAR2(60)  NOT NULL,
                  PRODUTOR        VARCHAR2(100) NOT NULL,
                  ORIGEM_UF       CHAR(2)       NOT NULL,
                  DATA_COLHEITA   DATE          NOT NULL,
                  PESO_KG         NUMBER(12,3)  CHECK (PESO_KG >= 0),
                  CARBONO_NEUTRO  CHAR(1) DEFAULT 'N' CHECK (CARBONO_NEUTRO IN ('S','N')),
                  AGUA_REUSO      CHAR(1) DEFAULT 'N' CHECK (AGUA_REUSO IN ('S','N')),
                  STATUS          VARCHAR2(30)  DEFAULT 'EM_PROCESSAMENTO'
                )
            """)
            log("Oracle: tabela LOTE criada.")

        # Tabela EVENTO
        if not _table_exists(conn, "EVENTO"):
            cur.execute("""
                CREATE TABLE EVENTO (
                  ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                  LOTE_ID      NUMBER NOT NULL REFERENCES LOTE(ID) ON DELETE CASCADE,
                  TIPO         VARCHAR2(20) CHECK (TIPO IN ('COLHEITA','TRANSPORTE','ARMAZENAGEM','INSPECAO')),
                  DATA_EVENTO  DATE NOT NULL,
                  LOCAL        VARCHAR2(120),
                  RESPONSAVEL  VARCHAR2(100),
                  OBSERVACOES  VARCHAR2(400)
                )
            """)
            log("Oracle: tabela EVENTO criada.")

        # Índices
        if not _index_exists(conn, "IDX_EVENTO_LOTE"):
            cur.execute("CREATE INDEX IDX_EVENTO_LOTE ON EVENTO(LOTE_ID)")
            log("Oracle: índice IDX_EVENTO_LOTE criado.")
        if not _index_exists(conn, "IDX_LOTE_UF"):
            cur.execute("CREATE INDEX IDX_LOTE_UF ON LOTE(ORIGEM_UF)")
            log("Oracle: índice IDX_LOTE_UF criado.")
        if not _index_exists(conn, "IDX_LOTE_STATUS"):
            cur.execute("CREATE INDEX IDX_LOTE_STATUS ON LOTE(STATUS)")
            log("Oracle: índice IDX_LOTE_STATUS criado.")

    conn.commit()


def inserir_lote(conn, lote: Dict[str, Any]) -> int:
    """
    Insere no Oracle e retorna o novo ID.
    Corrigido o DPY-2005: o bind :NEW_ID é passado dentro do dicionário.
    """
    sql = f"""
    INSERT INTO {T('LOTE')} (PRODUTO, PRODUTOR, ORIGEM_UF, DATA_COLHEITA, PESO_KG,
                             CARBONO_NEUTRO, AGUA_REUSO, STATUS)
    VALUES (:PROD, :PDR, :UF, :DC, :PESO, :CARB, :AGUA, :ST)
    RETURNING ID INTO :NEW_ID
    """
    with conn.cursor() as cur:
        new_id = cur.var(oracledb.NUMBER)
        params = {
            "PROD": lote["produto"],
            "PDR": lote["produtor"],
            "UF": lote["origem_uf"].upper(),
            "DC": iso_to_date(lote["data_colheita"]),
            "PESO": float(lote["peso_kg"]),
            "CARB": b2sn(bool(lote["carbono_neutro"])),
            "AGUA": b2sn(bool(lote["agua_reuso"])),
            "ST": lote.get("status", "EM_PROCESSAMENTO"),
            "NEW_ID": new_id,
        }
        cur.execute(sql, params)
        conn.commit()
        val = new_id.getvalue()
        novo = int(val[0] if isinstance(val, list) else val)
        log(f"DB inserir_lote: {novo}")
        return novo

def atualizar_lote_status(conn, lote_id: int, status: str) -> int:
    sql = f"UPDATE {T('LOTE')} SET STATUS=:S WHERE ID=:ID"
    with conn.cursor() as cur:
        cur.execute(sql, {"S": status, "ID": lote_id})
        conn.commit()
        return cur.rowcount

def listar_lotes_db(conn, uf: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = f"""SELECT ID, PRODUTO, PRODUTOR, ORIGEM_UF, DATA_COLHEITA, PESO_KG,
                     CARBONO_NEUTRO, AGUA_REUSO, STATUS
              FROM {T('LOTE')} WHERE 1=1"""
    params = {}
    if uf:
        sql += " AND ORIGEM_UF = :UF"; params["UF"] = uf.upper()
    if status:
        sql += " AND STATUS = :ST"; params["ST"] = status
    sql += " ORDER BY ID DESC"

    out: List[Dict[str, Any]] = []
    with conn.cursor() as cur:
        for (ID, PROD, PDR, UF, DC, PESO, CARB, AGUA, ST) in cur.execute(sql, params):
            out.append({
                "id": int(ID),
                "produto": PROD,
                "produtor": PDR,
                "origem_uf": UF,
                "data_colheita": DC.strftime("%Y-%m-%d"),
                "peso_kg": float(PESO),
                "carbono_neutro": sn2b(CARB),
                "agua_reuso": sn2b(AGUA),
                "status": ST,
                "eventos": []
            })
    return out

def deletar_lote(conn, lote_id: int) -> int:
    sql = f"DELETE FROM {T('LOTE')} WHERE ID=:ID"
    with conn.cursor() as cur:
        cur.execute(sql, {"ID": lote_id})
        conn.commit()
        return cur.rowcount


def inserir_evento(conn, lote_id: int, ev_iso: Dict[str, Any]) -> int:
    sql = f"""
    INSERT INTO {T('EVENTO')} (LOTE_ID, TIPO, DATA_EVENTO, LOCAL, RESPONSAVEL, OBSERVACOES)
    VALUES (:LID, :TP, :DT, :LOC, :RESP, :OBS)
    RETURNING ID INTO :NEW_ID
    """
    with conn.cursor() as cur:
        new_id = cur.var(oracledb.NUMBER)
        params = {
            "LID": lote_id,
            "TP": ev_iso["tipo"].upper(),
            "DT": iso_to_date(ev_iso["data"]),
            "LOC": ev_iso.get("local", ""),
            "RESP": ev_iso.get("responsavel", ""),
            "OBS": ev_iso.get("observacoes", ""),
            "NEW_ID": new_id,
        }
        cur.execute(sql, params)
        # INSPECAO muda status pra PRONTO
        if ev_iso["tipo"].upper() == "INSPECAO":
            cur.execute(f"UPDATE {T('LOTE')} SET STATUS='PRONTO' WHERE ID=:ID", {"ID": lote_id})
        conn.commit()
        val = new_id.getvalue()
        novo = int(val[0] if isinstance(val, list) else val)
        log(f"DB inserir_evento: {novo} (lote {lote_id})")
        return novo

def listar_eventos_do_lote(conn, lote_id: int) -> List[Dict[str, Any]]:
    sql = f"""SELECT ID, TIPO, DATA_EVENTO, LOCAL, RESPONSAVEL, OBSERVACOES
              FROM {T('EVENTO')} WHERE LOTE_ID=:ID ORDER BY DATA_EVENTO"""
    out: List[Dict[str, Any]] = []
    with conn.cursor() as cur:
        for (ID, TP, DT, LOC, RESP, OBS) in cur.execute(sql, {"ID": lote_id}):
            out.append({
                "id": int(ID),
                "tipo": TP,
                "data": DT.strftime("%Y-%m-%d"),
                "local": LOC,
                "responsavel": RESP,
                "observacoes": OBS
            })
    return out


def df_lotes(conn):
    """Retorna um DataFrame com os lotes (se pandas estiver instalado)."""
    try:
        import pandas as pd
    except Exception:  # pandas é opcional
        raise RuntimeError("pandas não está disponível neste ambiente.")
    sql = f"""SELECT ID, PRODUTO, PRODUTOR, ORIGEM_UF,
                     TO_CHAR(DATA_COLHEITA, 'YYYY-MM-DD') AS DATA_COLHEITA,
                     PESO_KG, CARBONO_NEUTRO, AGUA_REUSO, STATUS
              FROM {T('LOTE')} ORDER BY ID DESC"""
    return pd.read_sql(sql, conn)

def df_eventos(conn, lote_id: Optional[int] = None):
    """Retorna um DataFrame com eventos (filtra por lote_id se informado)."""
    try:
        import pandas as pd
    except Exception:
        raise RuntimeError("pandas não está disponível neste ambiente.")
    sql = f"""SELECT ID, LOTE_ID, TIPO,
                     TO_CHAR(DATA_EVENTO, 'YYYY-MM-DD') AS DATA_EVENTO,
                     LOCAL, RESPONSAVEL, OBSERVACOES
              FROM {T('EVENTO')}"""
    params = {}
    if lote_id is not None:
        sql += " WHERE LOTE_ID = :LID"
        params["LID"] = lote_id
    sql += " ORDER BY LOTE_ID, DATA_EVENTO"
    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    # monta DataFrame manualmente para não depender do cx_Oracle cursor_factory
    import pandas as pd
    return pd.DataFrame(rows, columns=cols)
