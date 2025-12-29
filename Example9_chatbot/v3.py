from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

llm = ChatOllama(model='llama3.1')

def chat_node(state: ChatState):
    # take user query from state
    messages = state['messages']
    print(f"State of Messages: {messages}")

    # send to llm
    answer = llm.invoke(messages)

    # Store response in state
    return {'messages': [answer]}

checkpointer = MemorySaver()

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)
print(chatbot.get_graph().draw_ascii())

thread_id='1'

while True:
    user_message = input('Type here: ')

    if user_message.strip().lower() in ['exit', 'quit', 'bye']:
        break

    config = {'configurable': {'thread_id': thread_id}}
    response = chatbot.invoke({'messages': [HumanMessage(content=user_message)]}, config=config)

    print(f"AI: {response['messages'][-1].content}")

