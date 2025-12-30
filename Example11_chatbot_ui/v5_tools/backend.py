from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
import requests


ALPHA_ADVANTAGE_API_KEY=''
WEATHER_API_KEY=''
DB_PATH = "../v4_database/db/mychatbot.db"

# -------------------
# 1. LLM
# -------------------
llm = ChatOllama(model='llama3.1')


# -------------------
# 2. Tools
# -------------------
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """

    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero is not allowed"}
            result = first_num / second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}

        return {"first_num": first_num, "second_num": second_num, "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_ADVANTAGE_API_KEY}"
    r = requests.get(url)
    return r.json()

@tool
def get_weather(city: str) -> str:
    """
    Given a city name, fetch the current weather conditions
    :param city:
    :return:
    """
    url = f"http://api.weatherstack.com/current?access_key={WEATHER_API_KEY}&query={city}"
    return requests.get(url).json()

tools = [search_tool, calculator, get_stock_price, get_weather]
llm_with_tools = llm.bind_tools(tools)

# -------------------
# 3. State
# -------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------------------
# 4. Nodes
# -------------------
def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

# -------------------
# 5. Checkpointer
# -------------------
connection = sqlite3.connect(database=DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=connection)

# -------------------
# 6. Graph
# -------------------
graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)

print(chatbot.get_graph().draw_mermaid())

# -------------------
# 7. Helper
# -------------------
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)


# Now this runs only INSERT/UPDATE, no table creation
def save_thread_title(thread_id: str, title: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO thread_title (thread_id, title) VALUES (?, ?)",
        (thread_id, title.strip())
    )
    conn.commit()
    conn.close()

def load_persisted_title(thread_id: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT title FROM thread_title WHERE thread_id = ?", (thread_id,)).fetchone()
    conn.close()
    return row[0] if row else ""



