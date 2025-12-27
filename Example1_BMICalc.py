from typing import TypedDict
from IPython.display import Image
from langgraph.graph import StateGraph, START, END

# Define State
class BMIState(TypedDict):
    weight_kg: float
    height_m: float
    bmi: float
    category: str

def calculate_bmi(state: BMIState) -> BMIState:
    weight = state['weight_kg']
    height = state['height_m']

    bmi = weight/(height**2)

    state['bmi'] = round(bmi, 2)

    return state

def label_bmi(state: BMIState) -> BMIState:
    bmi = state['bmi']
    if bmi < 18.5:
        state['category'] = 'Underweight'
    elif 18.5 <= bmi < 25:
        state['category'] = 'Normal'
    elif 25 <= bmi < 30:
        state['category'] = "Overweight"
    else:
        state['category'] = 'Obese'

    return state

# Define graph
graph = StateGraph(BMIState)

# Add nodes to the graph
graph.add_node('calculate_bmi', calculate_bmi)
graph.add_node('label_bmi', label_bmi)

# Add edges to the graph
graph.add_edge(START, 'calculate_bmi')
graph.add_edge('calculate_bmi', 'label_bmi')
graph.add_edge('label_bmi', END)

# Compile the graph
workflow = graph.compile()

# Execute the graph
final_state = workflow.invoke({'weight_kg': 65, 'height_m': 1.73})
# Image(workflow.get_graph().draw_mermaid_png())
print(workflow.get_graph().draw_mermaid())

print(final_state)