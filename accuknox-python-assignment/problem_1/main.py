import os
import sqlite3
import requests

API_URL = "https://openlibrary.org/search.json"
DB_PATH = os.path.join(os.path.dirname(__file__), "books.db")


def fetch_books(query="python", limit=10):
    params = {"q": query, "limit": limit}

    response = requests.get(API_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict) or "docs" not in data:
        raise ValueError("Unexpected API response format: 'docs' key missing")

    books = []
    for item in data["docs"]:
        title = item.get("title")
        work_key = item.get("key")
        if not title or not work_key:
            continue

        authors = item.get("author_name")
        if isinstance(authors, list) and len(authors) > 0:
            author = ", ".join(authors)
        else:
            author = "Unknown"

        year = item.get("first_publish_year")
        if not isinstance(year, int):
            year = None

        books.append({
            "external_id": work_key,
            "title": title,
            "author": author,
            "publication_year": year,
        })

    if not books:
        raise ValueError("No valid book records found in API response")

    return books


def setup_database(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            publication_year INTEGER
        )
    """)
    conn.commit()


def insert_books(conn, books):
    cursor = conn.cursor()
    query = """
        INSERT OR IGNORE INTO books (external_id, title, author, publication_year)
        VALUES (?, ?, ?, ?)
    """
    inserted_count = 0
    for book in books:
        cursor.execute(
            query,
            (
                book["external_id"],
                book["title"],
                book["author"],
                book["publication_year"],
            ),
        )
        if cursor.rowcount > 0:
            inserted_count += 1

    conn.commit()
    return inserted_count


def get_books_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, author, publication_year
        FROM books
        ORDER BY id ASC
    """)
    return cursor.fetchall()


def display_books(rows):
    if not rows:
        print("No records found in the database.")
        return

    print("\nStored Books (from SQLite):")
    print("-" * 85)
    print(f"{'ID':<4} | {'Title':<40} | {'Author':<25} | {'Year':<6}")
    print("-" * 85)

    for row in rows:
        book_id, title, author, year = row
        title_display = title[:37] + "..." if len(title) > 40 else title
        author_display = author[:22] + "..." if len(author) > 25 else author
        year_display = str(year) if year is not None else "N/A"
        print(f"{book_id:<4} | {title_display:<40} | {author_display:<25} | {year_display:<6}")

    print("-" * 85)
    print(f"Total books in DB: {len(rows)}")


def main():
    try:
        print("Fetching books from Open Library API...")
        books = fetch_books(query="python", limit=10)
        print(f"Fetched {len(books)} valid book records.")
    except requests.exceptions.Timeout:
        print("Error: The API request timed out.")
        return
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"Network error while calling API: {e}")
        return
    except ValueError as e:
        print(f"Invalid data received from API: {e}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        setup_database(conn)

        added = insert_books(conn, books)
        print(f"Inserted {added} new book(s) into {DB_PATH}.")

        rows = get_books_from_db(conn)
        display_books(rows)
    except sqlite3.Error as e:
        print(f"SQLite database error: {e}")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
