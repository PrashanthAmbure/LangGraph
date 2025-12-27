from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from typing import TypedDict


model = ChatOllama(model='llama3')

class LLMState(TypedDict):
    question: str
    answer: str

def llm_qa(state: LLMState) -> LLMState:
    # Extract the question from the state
    question = state['question']

    # Form a prompt
    prompt = f"Answer the following question {question}"

    # Ask the question the LLM
    answer = model.invoke(prompt).content

    # Update the answer in the state
    state['answer'] = answer

    return state

graph = StateGraph(LLMState)

# Add Node
graph.add_node('llm_qa', llm_qa)

# Add Edge
graph.add_edge(START, 'llm_qa')
graph.add_edge('llm_qa', END)

# Compile the graph
workflow = graph.compile()
print(workflow.get_graph().draw_mermaid())

initial_state = {'question': 'Capital of India?'}
final_state = workflow.invoke(initial_state)

print(final_state)


