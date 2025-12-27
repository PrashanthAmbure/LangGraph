from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END



class QuadraticState(TypedDict):
    a: int
    b: int
    c: int

    equation: str
    discriminant: str
    result: str

def show_equation(state: QuadraticState) -> QuadraticState:
    equation = f"{state['a']}x2{state['b']}x{state['c']}"
    state['equation'] = equation
    return state

def calculate_discriminant(state: QuadraticState) -> QuadraticState:
    discriminant = state['b']**2 - 4*state['a']*state['c']
    state['discriminant'] = discriminant
    return state

def real_roots(state: QuadraticState):
    root1 = (-state['b'] + state['discriminant']**0.5)/(2*state['a'])
    root2 = (-state['b'] - state['discriminant']**0.5)/(2*state['a'])
    result = f"The roots are {root1} and {root2}"
    return {'result': result}

def repeated_roots(state: QuadraticState):
    root = (-state["b"])/(2*state["a"])
    result = f"Only repeating root is {root}"
    return {'result': result}

def no_real_roots(state: QuadraticState):
    result = f"No real roots"
    return {'result': result}

def check_condition(state: QuadraticState) -> Literal["real_roots", "repeated_roots", "no_real_roots"]:
    if state["discriminant"] > 0:
        return "real_roots"
    elif state["discriminant"] == 0:
        return "repeated_roots"
    else:
        return "no_real_roots"

graph = StateGraph(QuadraticState)

graph.add_node('show_equation', show_equation)
graph.add_node('calculate_discriminant', calculate_discriminant)
graph.add_node('real_roots', real_roots)
graph.add_node('repeated_roots', repeated_roots)
graph.add_node('no_real_roots', no_real_roots)


graph.add_edge(START, 'show_equation')
graph.add_edge('show_equation', 'calculate_discriminant')
graph.add_conditional_edges('calculate_discriminant', check_condition)
graph.add_edge('real_roots', END)
graph.add_edge('repeated_roots', END)
graph.add_edge('no_real_roots', END)

workflow = graph.compile()
print(workflow.get_graph().draw_ascii())

initial_state = {'a': 4, 'b': 2, 'c': 4}

final_state = workflow.invoke(initial_state)

print(final_state)