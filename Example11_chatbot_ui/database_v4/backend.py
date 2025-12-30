import sqlite3
from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver


llm = ChatOllama(model = 'llama3.1')

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

# Run this ONCE when backend module loads
def create_table_thread_title(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS thread_title (
            thread_id TEXT PRIMARY KEY,
            title TEXT
        )
    """)
    conn.commit()
    # conn.close()

connection = sqlite3.connect(database='db/mychatbot.db', check_same_thread=False)

create_table_thread_title(connection)

checkpointer = SqliteSaver(conn=connection)

graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)


# Now this runs only INSERT/UPDATE, no table creation
def save_thread_title(thread_id: str, title: str):
    conn = sqlite3.connect("db/mychatbot.db")
    conn.execute(
        "INSERT OR REPLACE INTO thread_title (thread_id, title) VALUES (?, ?)",
        (thread_id, title.strip())
    )
    conn.commit()
    conn.close()

def load_persisted_title(thread_id: str):
    conn = sqlite3.connect("db/mychatbot.db")
    row = conn.execute("SELECT title FROM thread_title WHERE thread_id = ?", (thread_id,)).fetchone()
    conn.close()
    return row[0] if row else ""




