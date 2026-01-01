from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_classic.tools import tool
from typing import TypedDict, Annotated
import requests


ALPHA_ADVANTAGE_API_KEY=''

llm = ChatOllama(model='llama3.1')

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
def purchase_stock(symbol: str, quantity: int) -> dict:
    """
    Simulate purchasing a given quantity of a stock symbol.

    HUMAN-IN-THE-LOOP:
    Before confirming the purchase, this tool will interrupt
    and wait for a human decision ("yes" / anything else).
    """
    decision = interrupt(f"Approve buying {quantity} shares of {symbol}? (Y/N)")
    if isinstance(decision, str) and decision.lower() == "y":
        return {
            "status": "success",
            "message": f"Purchase order placed for {quantity} shares of {symbol}.",
            "symbol": symbol,
            "quantity": quantity,
        }

    else:
        return {
            "status": "cancelled",
            "message": f"Purchase of {quantity} shares of {symbol} was declined by human.",
            "symbol": symbol,
            "quantity": quantity,
        }

tools = [get_stock_price, purchase_stock]
llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    response = llm_with_tools.invoke(state['messages'])
    return {'messages': [response]}

tool_node = ToolNode(tools)

builder = StateGraph(ChatState)

builder.add_node('chat_node', chat_node)
builder.add_node('tools', tool_node)

builder.add_edge(START, 'chat_node')
builder.add_conditional_edges('chat_node', tools_condition)
builder.add_edge('tools', 'chat_node')

checkpointer=InMemorySaver()

workflow = builder.compile(checkpointer=checkpointer)
print(workflow.get_graph().draw_mermaid())

config = {'configurable': {'thread_id': 'hitl_2'}}

while True:
    user_message = input('Please type your query. (Type exit/bye/quit to terminate):\n')
    if user_message in ['exit', 'quit', 'bye']:
        print('Terminating the session, have a good day!')
        break
    initial_state = {'messages': HumanMessage(user_message)}
    result = workflow.invoke(initial_state, config=config)

    # Check for HITL interrupt from purchase_stock
    interrupts = result.get('__interrupt__', [])

    if interrupts:
        # Our interrupt payload is the string we passed to interrupt(...)
        prompt_to_human = interrupts[0].value
        print(f"HITL: {prompt_to_human}")
        decision = input("Your decision: ").strip().lower()

        result = workflow.invoke(Command(resume=decision), config=config)

    # Get the latest message from the assistant
    messages = result["messages"]
    last_msg = messages[-1]
    print(f"Bot: {last_msg.content}\n")


