import csv
import os
import sqlite3

base_dir = os.path.dirname(__file__)
csv_file = os.path.join(base_dir, "users.csv")
db_file = os.path.join(base_dir, "users.db")


def import_csv_to_sqlite():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL
        )
    """)

    inserted = 0
    skipped = 0

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            email = row["email"].strip().lower()
            role = row["role"].strip()

            if not name or not email:
                continue

            try:
                cursor.execute(
                    "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
                    (name, email, role),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                print(f"Duplicate email skipped: {email}")
                skipped += 1

    conn.commit()
    conn.close()
    print(f"\nInserted: {inserted}, Skipped duplicates: {skipped}")


def verify_records():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    print(f"\nTotal rows in users table: {total}")

    cursor.execute("SELECT id, name, email, role FROM users ORDER BY id")
    rows = cursor.fetchall()

    print("Records in database:")
    for row in rows:
        print(f"ID={row[0]} | {row[1]} | {row[2]} | {row[3]}")

    conn.close()


if __name__ == "__main__":
    try:
        import_csv_to_sqlite()
        verify_records()
    except FileNotFoundError:
        print(f"Could not find CSV file: {csv_file}")
    except (csv.Error, sqlite3.Error) as err:
        print(f"Error: {err}")
