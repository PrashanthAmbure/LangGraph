import sqlite3

DB_PATH = "./db/mychatbot.db"


def delete_thread(thread_id: str):
    """Completely erase a chat thread including its checkpoints and title metadata."""
    conn = sqlite3.connect(DB_PATH)

    # Delete from LangGraph checkpoint tables
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))

    # Delete title metadata (your UI naming table)
    conn.execute("DELETE FROM thread_title WHERE thread_id = ?", (thread_id,))

    conn.commit()
    conn.close()

delete_thread("c2648c89-473a-4865-8bf5-363d0c7620a2")

