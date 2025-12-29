from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage

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


graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile()
print(chatbot.get_graph().draw_ascii())

initial_state = {'messages': [HumanMessage(content='What is the capital on India?')]}

final_state = chatbot.invoke(initial_state)

print(final_state['messages'][-1].content)

