from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command


llm = ChatOllama(model='llama3.1')

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    decision = interrupt(
        {
            "type": "approval",
            "reason": "Model is about to answer a user question.",
            "question": state['messages'][-1].content,
            "instruction": "Approve this question? (Y/N)"
        }
    )

    if decision['approved'] == 'N':
        return {"messages": AIMessage(content='Not Approved')}
    else:
        response = llm.invoke(state['messages'])
        return {"messages": [response]}

checkpointer = InMemorySaver()

builder = StateGraph(ChatState)

builder.add_node('chat_node', chat_node)

builder.add_edge(START, 'chat_node')
builder.add_edge('chat_node', END)

workflow = builder.compile(checkpointer=checkpointer)
print(workflow.get_graph().draw_ascii())

config = {'configurable': {"thread_id": "hitl_1"}}

initial_state = {'messages': [("user", "Explain gradient descent in simple terms")]}

final_state = workflow.invoke(initial_state, config)

user_question = final_state['__interrupt__'][0].value

user_approval = input(f"Please answer: \n {user_question}\n")

final_result = workflow.invoke(Command(resume={"approved": user_approval}), config=config)

print(final_result)