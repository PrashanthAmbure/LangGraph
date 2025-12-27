from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class BatsmanState(TypedDict):
    runs: int
    balls: int
    fours: int
    sixes: int

    sr: float
    bpb: float
    boundary_percent: float

    summary: str

def calc_sr(state: BatsmanState) -> BatsmanState:
    sr = (state['runs']/state['balls'])*100
    # In Parallel WF execution returning state might confuse langgraph
    # Because it assumes we have modified runs attribute as well though we just used for read
    # So do not return entire state
    # state['sr'] = sr
    # return state
    return {'sr': sr}


def calc_bpb(state: BatsmanState) -> BatsmanState:
    bpb = state['runs']/(state['fours'] + state['sixes'])
    # state['bpb'] = bpb
    # return state
    return {'bpb': bpb}

def calc_boundary_percent(state: BatsmanState) -> BatsmanState:
    boundary_percent = (((state['fours'] * 4) + (state['sixes'] * 6 ))/ state['runs'])/100
    # state['boundary_percent'] = boundary_percent
    # return state
    return {'boundary_percent': boundary_percent}

def summary(state: BatsmanState) -> BatsmanState:
    summary = f"""
    Strike Rate - {state['sr']} \n
    Balls Per Boundary - {state['bpb']} \n
    Boundary Percent - {state['boundary_percent']} \n
"""
    # state['summary'] = summary
    # return state
    return {'summary': summary}

# Define a graph
graph = StateGraph(BatsmanState)

# Add nodes to the graph
graph.add_node('calc_sr', calc_sr)
graph.add_node('calc_bpb', calc_bpb)
graph.add_node('calc_boundary_percent', calc_boundary_percent)
graph.add_node('summary', summary)

# Add edges to the graph
graph.add_edge(START, 'calc_sr')
graph.add_edge(START, 'calc_bpb')
graph.add_edge(START, 'calc_boundary_percent')

graph.add_edge('calc_sr', 'summary')
graph.add_edge('calc_bpb', 'summary')
graph.add_edge('calc_boundary_percent', 'summary')

graph.add_edge('summary', END)

# Compile graph
workflow = graph.compile()
print(workflow.get_graph().draw_ascii())

# Execute graph
initial_state = {"runs": 100, "balls": 55, "fours": 10, "sixes": 6}
final_state = workflow.invoke(initial_state)
print(final_state)
print("="*100)
print(final_state['sr'])
print("="*100)
print(final_state['bpb'])
print("="*100)
print(final_state['boundary_percent'])
print("="*100)