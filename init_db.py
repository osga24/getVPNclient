"""Run once to create users.db from vpn.xlsx."""
import sqlite3
from pathlib import Path

import openpyxl

XLSX = Path(__file__).parent / "vpn.xlsx"
DB = Path(__file__).parent / "users.db"


def main():
    wb = openpyxl.load_workbook(XLSX)
    ws = wb.active

    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            student_id TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            vpn_num    INTEGER NOT NULL
        )
    """)

    rows = [
        (str(r[0]).strip(), str(r[1]).strip(), int(r[2]))
        for r in ws.iter_rows(min_row=3, values_only=True)
        if r[0] and r[2] is not None
    ]
    con.executemany(
        "INSERT OR REPLACE INTO users (student_id, name, vpn_num) VALUES (?, ?, ?)",
        rows,
    )
    con.commit()
    con.close()

    print(f"Imported {len(rows)} users into {DB}")


if __name__ == "__main__":
    main()
