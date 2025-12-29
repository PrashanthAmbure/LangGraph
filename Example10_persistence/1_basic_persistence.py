from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict

class JokeState(TypedDict):
    topic: str
    joke: str
    explanation: str

llm = ChatOllama(model='llama3.1')
def generate_joke(state: JokeState):
    response = llm.invoke(f"Generate a joke on the topic: {state['topic']}").content
    return {'joke': response}

def generate_explanation(state: JokeState):
    response = llm.invoke(f"write an explanation for the joke - {state['joke']}").content
    return {'explanation': response}

checkpointer = InMemorySaver()
graph = StateGraph(JokeState)

graph.add_node('joke', generate_joke)
graph.add_node('explanation', generate_explanation)

graph.add_edge(START, 'joke')
graph.add_edge('joke', 'explanation')
graph.add_edge('explanation', END)

workflow = graph.compile(checkpointer=checkpointer)
print(workflow.get_graph().draw_ascii())

while True:
    print('Enter quit or exit or bye to terminate.')
    user_message = input("Topic: ")
    if user_message.strip().lower() in ['quit', 'exit', 'bye']:
        print('Nice talking to you ! Bye for now.')
        break

    #     StateHistory-Pizza - it would fetch the details stored for Pizza thread
    #     StateHistory-Pasta - it would fetch the details stored for Pasta thread
    if 'statehistory' in user_message.strip().lower():
        thread_id = 'thread_'+user_message.split('-')[1]
        print(f'Split ThreadId = {thread_id}')
        config = {'configurable': {'thread_id': thread_id}}
        print('*' * 100)
        print(workflow.get_state(config))

        print('*' * 100)
        print(list(workflow.get_state_history(config)))
    else:
        thread_id = 'thread_'+user_message
        initial_state = {'topic': user_message}
        config = {'configurable': {'thread_id': thread_id}}
        final_state = workflow.invoke(initial_state, config=config)

        print('*'*100)
        print(final_state)

        print('*' * 100)
        print(workflow.get_state(config))

        print('*' * 100)
        print(list(workflow.get_state_history(config)))