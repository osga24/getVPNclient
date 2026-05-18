"""Rebuild users.db from vpn.xlsx."""
import sqlite3
from pathlib import Path

import openpyxl

XLSX = Path(__file__).parent / "vpn.xlsx"
DB = Path(__file__).parent / "users.db"
TA_PASSWORD = "ousu0518"


def rebuild_db() -> int:
    if not XLSX.exists():
        raise FileNotFoundError(f"Missing source workbook: {XLSX}")

    wb = openpyxl.load_workbook(XLSX)
    ws = wb.active

    if DB.exists():
        DB.unlink()

    con = sqlite3.connect(DB)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            vpn_num    INTEGER NOT NULL,
            password   TEXT
        )
    """
    )

    rows = []
    for r in ws.iter_rows(min_row=3, values_only=True):
        if not r[0] or r[2] is None:
            continue
        student_id = str(r[0]).strip()
        name = str(r[1]).strip() if r[1] is not None else ""
        password = TA_PASSWORD if student_id.startswith("TA") else None
        rows.append((student_id, name, int(r[2]), password))
    con.executemany(
        """
        INSERT INTO users (student_id, name, vpn_num, password)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )
    con.commit()
    con.close()

    return len(rows)


def main():
    count = rebuild_db()
    print(f"Imported {count} users into {DB}")


if __name__ == "__main__":
    main()
