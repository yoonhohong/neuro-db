import sqlite3
import csv
import os
import platform
from datetime import datetime
from pathlib import Path


def get_db_path() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("USERPROFILE", Path.home()))
    else:
        base = Path.home()
    db_dir = base / "Documents" / "neuro-db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "neuro_db.sqlite"


DB_PATH = get_db_path()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name    TEXT,
                hosp_id         TEXT,
                remarks         TEXT,
                sex             TEXT,
                age_at_dx       INTEGER,
                dx              TEXT,
                dx_others       TEXT,
                date_onset      TEXT,
                date_dx         TEXT,
                onset_b         INTEGER DEFAULT 0,
                onset_c         INTEGER DEFAULT 0,
                onset_t         INTEGER DEFAULT 0,
                onset_l         INTEGER DEFAULT 0,
                lmn_b           INTEGER DEFAULT 0,
                lmn_c           INTEGER DEFAULT 0,
                lmn_t           INTEGER DEFAULT 0,
                lmn_l           INTEGER DEFAULT 0,
                lmn_none        INTEGER DEFAULT 0,
                umn_b           INTEGER DEFAULT 0,
                umn_c           INTEGER DEFAULT 0,
                umn_t           INTEGER DEFAULT 0,
                umn_l           INTEGER DEFAULT 0,
                umn_none        INTEGER DEFAULT 0,
                emg_b           INTEGER DEFAULT 0,
                emg_c           INTEGER DEFAULT 0,
                emg_t           INTEGER DEFAULT 0,
                emg_l           INTEGER DEFAULT 0,
                emg_none        INTEGER DEFAULT 0,
                emg_not_checked INTEGER DEFAULT 0,
                pseudobulbar_affect TEXT,
                dementia        TEXT,
                riluzole_start  TEXT,
                riluzole_end    TEXT,
                edaravone_start TEXT,
                edaravone_end   TEXT,
                progression_onset2dx  TEXT,
                progression_afterdx   TEXT,
                height_cm       REAL,
                gastrostomy_date TEXT,
                niv_date        TEXT,
                tracheostomy_date TEXT,
                death_date      TEXT,
                brain_mri       TEXT,
                spine_mri       TEXT,
                genetic_test    TEXT,
                cognitive_test  TEXT,
                chest_ct        TEXT,
                abdomen_ct      TEXT,
                buffy_coat      TEXT,
                plasma          TEXT,
                serum           TEXT,
                csf             TEXT,
                created_at      TEXT,
                updated_at      TEXT,
                UNIQUE(patient_name, hosp_id)
            );

            CREATE TABLE IF NOT EXISTS body_weight (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id  INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
                weight_kg   REAL,
                date        TEXT,
                is_premorbid INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS fvc_records (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id  INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
                fvc_percent REAL,
                date        TEXT
            );

            CREATE TABLE IF NOT EXISTS alsfrs_records (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id  INTEGER NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
                score       INTEGER,
                date        TEXT
            );
        """)


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _insert_timeseries(conn, patient_id: int, parsed: dict):
    conn.execute("DELETE FROM body_weight WHERE patient_id=?", (patient_id,))
    for entry in parsed.get("body_weight", []):
        conn.execute(
            "INSERT INTO body_weight(patient_id, weight_kg, date, is_premorbid) VALUES(?,?,?,?)",
            (patient_id, entry["weight_kg"], entry.get("date"), entry.get("is_premorbid", 0)),
        )

    conn.execute("DELETE FROM fvc_records WHERE patient_id=?", (patient_id,))
    for entry in parsed.get("fvc_records", []):
        conn.execute(
            "INSERT INTO fvc_records(patient_id, fvc_percent, date) VALUES(?,?,?)",
            (patient_id, entry["fvc_percent"], entry["date"]),
        )

    conn.execute("DELETE FROM alsfrs_records WHERE patient_id=?", (patient_id,))
    for entry in parsed.get("alsfrs_records", []):
        conn.execute(
            "INSERT INTO alsfrs_records(patient_id, score, date) VALUES(?,?,?)",
            (patient_id, entry["score"], entry["date"]),
        )


PATIENT_FIELDS = [
    "patient_name", "hosp_id", "remarks", "sex", "age_at_dx",
    "dx", "dx_others", "date_onset", "date_dx",
    "onset_b", "onset_c", "onset_t", "onset_l",
    "lmn_b", "lmn_c", "lmn_t", "lmn_l", "lmn_none",
    "umn_b", "umn_c", "umn_t", "umn_l", "umn_none",
    "emg_b", "emg_c", "emg_t", "emg_l", "emg_none", "emg_not_checked",
    "pseudobulbar_affect", "dementia",
    "riluzole_start", "riluzole_end", "edaravone_start", "edaravone_end",
    "progression_onset2dx", "progression_afterdx",
    "height_cm",
    "gastrostomy_date", "niv_date", "tracheostomy_date", "death_date",
    "brain_mri", "spine_mri", "genetic_test", "cognitive_test",
    "chest_ct", "abdomen_ct",
    "buffy_coat", "plasma", "serum", "csf",
]


def insert_patient(parsed: dict) -> int:
    now = _now()
    values = {f: parsed.get(f) for f in PATIENT_FIELDS}
    values["created_at"] = now
    values["updated_at"] = now

    cols = ", ".join(values.keys())
    placeholders = ", ".join(["?"] * len(values))
    sql = f"INSERT INTO patients ({cols}) VALUES ({placeholders})"

    with get_connection() as conn:
        cur = conn.execute(sql, list(values.values()))
        patient_id = cur.lastrowid
        _insert_timeseries(conn, patient_id, parsed)
    return patient_id


def update_patient(patient_id: int, parsed: dict):
    now = _now()
    values = {f: parsed.get(f) for f in PATIENT_FIELDS}
    values["updated_at"] = now

    set_clause = ", ".join(f"{k}=?" for k in values.keys())
    sql = f"UPDATE patients SET {set_clause} WHERE patient_id=?"

    with get_connection() as conn:
        conn.execute(sql, list(values.values()) + [patient_id])
        _insert_timeseries(conn, patient_id, parsed)


def get_patient_by_id(patient_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM patients WHERE patient_id=?", (patient_id,)
        ).fetchone()
        if not row:
            return None
        p = dict(row)
        p["body_weight"] = [
            dict(r) for r in conn.execute(
                "SELECT * FROM body_weight WHERE patient_id=? ORDER BY is_premorbid DESC, date ASC",
                (patient_id,)
            )
        ]
        p["fvc_records"] = [
            dict(r) for r in conn.execute(
                "SELECT * FROM fvc_records WHERE patient_id=? ORDER BY date ASC",
                (patient_id,)
            )
        ]
        p["alsfrs_records"] = [
            dict(r) for r in conn.execute(
                "SELECT * FROM alsfrs_records WHERE patient_id=? ORDER BY date ASC",
                (patient_id,)
            )
        ]
    return p


def get_all_patients(search: str = "") -> list[dict]:
    sql = """
        SELECT
            p.*,
            (SELECT weight_kg FROM body_weight
             WHERE patient_id=p.patient_id AND is_premorbid=0
             ORDER BY date DESC LIMIT 1) AS latest_bwt,
            (SELECT date FROM body_weight
             WHERE patient_id=p.patient_id AND is_premorbid=0
             ORDER BY date DESC LIMIT 1) AS latest_bwt_date,
            (SELECT fvc_percent FROM fvc_records
             WHERE patient_id=p.patient_id
             ORDER BY date DESC LIMIT 1) AS latest_fvc,
            (SELECT date FROM fvc_records
             WHERE patient_id=p.patient_id
             ORDER BY date DESC LIMIT 1) AS latest_fvc_date,
            (SELECT score FROM alsfrs_records
             WHERE patient_id=p.patient_id
             ORDER BY date DESC LIMIT 1) AS latest_alsfrs,
            (SELECT date FROM alsfrs_records
             WHERE patient_id=p.patient_id
             ORDER BY date DESC LIMIT 1) AS latest_alsfrs_date
        FROM patients p
    """
    params = []
    if search:
        sql += " WHERE p.patient_name LIKE ? OR p.hosp_id LIKE ? OR p.dx LIKE ?"
        like = f"%{search}%"
        params = [like, like, like]
    sql += " ORDER BY p.date_dx DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def delete_patient(patient_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM patients WHERE patient_id=?", (patient_id,))


def export_to_csv(patient_ids: list[int] | None, filepath: str):
    """patient_ids=None 이면 전체 내보내기."""
    with get_connection() as conn:
        if patient_ids is None:
            rows = conn.execute("SELECT * FROM patients ORDER BY date_dx DESC").fetchall()
        else:
            placeholders = ",".join("?" * len(patient_ids))
            rows = conn.execute(
                f"SELECT * FROM patients WHERE patient_id IN ({placeholders}) ORDER BY date_dx DESC",
                patient_ids,
            ).fetchall()

        if not rows:
            return

        base_cols = list(rows[0].keys())

        # 시계열 최대 개수 파악
        max_bwt = max_fvc = max_alsfrs = 0
        timeseries: dict[int, dict] = {}
        for row in rows:
            pid = row["patient_id"]
            bwts = conn.execute(
                "SELECT * FROM body_weight WHERE patient_id=? ORDER BY is_premorbid DESC, date ASC",
                (pid,),
            ).fetchall()
            fvcs = conn.execute(
                "SELECT * FROM fvc_records WHERE patient_id=? ORDER BY date ASC", (pid,)
            ).fetchall()
            alsfrs = conn.execute(
                "SELECT * FROM alsfrs_records WHERE patient_id=? ORDER BY date ASC", (pid,)
            ).fetchall()
            timeseries[pid] = {"bwt": bwts, "fvc": fvcs, "alsfrs": alsfrs}
            max_bwt = max(max_bwt, len(bwts))
            max_fvc = max(max_fvc, len(fvcs))
            max_alsfrs = max(max_alsfrs, len(alsfrs))

        # 헤더 구성
        extra_cols = []
        extra_cols.append("bwt_premorbid")
        for i in range(1, max_bwt + 1):
            extra_cols += [f"bwt_{i}_kg", f"bwt_{i}_date"]
        for i in range(1, max_fvc + 1):
            extra_cols += [f"fvc_{i}_pct", f"fvc_{i}_date"]
        for i in range(1, max_alsfrs + 1):
            extra_cols += [f"alsfrs_{i}_score", f"alsfrs_{i}_date"]

        all_cols = base_cols + extra_cols

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=all_cols)
            writer.writeheader()

            for row in rows:
                record = dict(row)
                pid = row["patient_id"]
                ts = timeseries[pid]

                # premorbid 체중
                premorbid = next((b for b in ts["bwt"] if b["is_premorbid"]), None)
                record["bwt_premorbid"] = premorbid["weight_kg"] if premorbid else ""

                # 날짜별 체중 (premorbid 제외)
                dated_bwts = [b for b in ts["bwt"] if not b["is_premorbid"]]
                for i, b in enumerate(dated_bwts, 1):
                    record[f"bwt_{i}_kg"] = b["weight_kg"]
                    record[f"bwt_{i}_date"] = b["date"]

                for i, fv in enumerate(ts["fvc"], 1):
                    record[f"fvc_{i}_pct"] = fv["fvc_percent"]
                    record[f"fvc_{i}_date"] = fv["date"]

                for i, al in enumerate(ts["alsfrs"], 1):
                    record[f"alsfrs_{i}_score"] = al["score"]
                    record[f"alsfrs_{i}_date"] = al["date"]

                writer.writerow({c: record.get(c, "") for c in all_cols})
