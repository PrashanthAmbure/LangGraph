from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from langchain_ollama import ChatOllama

model = ChatOllama(model='llama3')

class BlogState(TypedDict):
    title: str
    outline: str
    content: str
    evaluate: float

def create_outline(state: BlogState) -> BlogState:
    # Fetch title
    title = state['title']

    # Prepare a prompt
    prompt = f"Create an detailed outline on the given title - {title}"

    # Ask LLM
    answer = model.invoke(prompt).content

    state['outline'] = answer

    return state


def create_blog(state: BlogState) -> BlogState:
    # Fetch title and outline
    title = state['title']
    outline = state['outline']

    # Prepare a prompt
    prompt = f"Create a detailed blog on the given title - {title} based on the outline {outline}"

    # Ask LLM
    answer = model.invoke(prompt).content

    state['content'] = answer

    return state

def evaluate_blog(state: BlogState) -> BlogState:
    # Fetch title, outline and Blog
    outline = state['outline']
    content = state['content']

    # Prepare a prompt
    prompt = f"Based on the outline - {outline}, rate my blog - {content} on a scale of 100"

    # Ask LLM
    answer = model.invoke(prompt).content

    state['evaluate'] = answer

    return state


# Define graph
graph = StateGraph(BlogState)

# Add Nodes
graph.add_node('create_outline', create_outline)
graph.add_node('create_blog', create_blog)
graph.add_node('evaluate_blog', evaluate_blog)

# Add Edges
graph.add_edge(START, 'create_outline')
graph.add_edge('create_outline', 'create_blog')
graph.add_edge('create_blog', 'evaluate_blog')
graph.add_edge('evaluate_blog', END)

# Compile graph
workflow = graph.compile()
print(workflow.get_graph().draw_mermaid())
# print(workflow.get_graph().draw_ascii())
print(workflow.get_graph().print_ascii())

# Execute graph
initial_state = {'title' : "Raise of AI in India"}
final_state = workflow.invoke(initial_state)

print(final_state['outline'])
print(f"="*200)
print(final_state['content'])
print(f"="*200)
print(final_state['evaluate'])