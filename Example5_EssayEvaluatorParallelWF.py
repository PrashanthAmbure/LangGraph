from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
import operator

model = ChatOllama(model='llama3')

essay = """
In the vast expanse of the cosmos, few phenomena capture the imagination quite like black holes. They are regions of space where the pull of gravity is so intense that nothing, not even light, can escape their grasp. Far from being empty voids, black holes are concentrations of immense mass packed into an incredibly small space, pushing the limits of our understanding of physics, space, and time.
The modern understanding of black holes began with Albert Einstein's theory of general relativity, which explained that mass causes space and time to bend or curve. In 1916, German physicist Karl Schwarzschild used Einstein's equations to describe the existence of a boundary around a sufficiently dense object, beyond which the escape velocity would exceed the speed of light. This boundary, later termed the event horizon, is the "point of no return". At the very center of a black hole lies the singularity, a point of seemingly infinite density where all the mass is concentrated.
Black holes primarily form from the dramatic death of massive stars. During most of a star's life, the outward pressure from nuclear fusion balances the inward pull of its own gravity. When a massive star (more than several times the mass of our Sun) exhausts its nuclear fuel, this balance is lost. The core collapses in on itself under overwhelming gravity, an event often accompanied by a massive explosion called a supernova, which blasts the star's outer layers into space. The remaining core collapses indefinitely to form a black hole.
Astronomers classify black holes into several types based on their mass:
Stellar-mass black holes: These are the most common type, with masses up to 20 times greater than the Sun's. They form from the collapse of individual massive stars.
Supermassive black holes: Found at the center of nearly every large galaxy, including our own Milky Way (which hosts Sagittarius A*), these behemoths can be millions or even billions of times more massive than the Sun.
Intermediate-mass black holes and theoretical primordial black holes also exist, though they are less understood or yet to be definitively confirmed.
Because black holes absorb all light, they are invisible to standard telescopes. Scientists must rely on indirect methods to detect them. They observe the powerful effects of the black hole's gravity on nearby matter and stars. As gas and dust fall toward a black hole, they form a rapidly spinning accretion disk, which heats up and emits brilliant X-rays and other radiation that telescopes can detect. Astronomers also track the unusual, rapid orbits of stars around an invisible center to infer a black hole's mass and location.
Through groundbreaking projects like the Event Horizon Telescope, humanity has captured the first-ever direct images of the glow around a black hole's silhouette, turning a theoretical curiosity into a visual reality. These enigmatic objects, once considered mere mathematical oddities, are now understood to be powerful forces that have played a crucial role in the evolution of galaxies and the universe as we know it. Much remains a mystery, particularly what happens at the singularity and the fate of information that falls in, ensuring black holes will continue to be a frontier of scientific research for decades to come.
"""

class EvaluationSchema(BaseModel):
    feedback: str = Field(description='Detailed feedback for the essay')
    score: int = Field(description='Score out of 10', ge=0, le=10)

structured_model = model.with_structured_output(EvaluationSchema)

class EssayState(TypedDict):
    essay_text: str

    language_feedback: str
    analysis_feedback: str
    clarity_feedback: str
    overall_feedback: str
    individual_scores: Annotated[list[int], operator.add]
    average_score: float

def evaluate_language(state: EssayState):
    prompt = f"Evaluate the language quality of the following essay and provide a feedback and assign a score out of 10 \n {state['essay_text']}"
    response = structured_model.invoke(prompt)

    return {'language_feedback': response.feedback, 'individual_scores': [response.score]}

def evaluate_analysis(state: EssayState):
    prompt = f"Evaluate the depth of analysis of the following essay and provide a feedback and assign a score out of 10 \n {state['essay_text']}"
    response = structured_model.invoke(prompt)

    return {'analysis_feedback': response.feedback, 'individual_scores': [response.score]}

def evaluate_clarity(state: EssayState):
    prompt = f"Evaluate the clarity of thought of the following essay and provide a feedback and assign a score out of 10 \n {state['essay_text']}"
    response = structured_model.invoke(prompt)

    return {'clarity_feedback': response.feedback, 'individual_scores': [response.score]}

def final_evaluation(state: EssayState):
    prompt = f"Based on the following feedbacks create a summarized feedback \n language feedback - {state['language_feedback']} \n depth of analysis feedback = {state['analysis_feedback']} \n clarity of thought feedback - {state['clarity_feedback']}"
    response = model.invoke(prompt).content

    # calc avg scores
    avg_score=sum(state['individual_scores'])/len(state["individual_scores"])

    return {'overall_feedback': response, 'average_score': avg_score}

# Define graph
graph = StateGraph(EssayState)

# Add nodes
graph.add_node('evaluate_language', evaluate_language)
graph.add_node('evaluate_analysis', evaluate_analysis)
graph.add_node('evaluate_clarity', evaluate_clarity)
graph.add_node('final_evaluation', final_evaluation)

# Add edges
graph.add_edge(START, 'evaluate_language')
graph.add_edge(START, 'evaluate_analysis')
graph.add_edge(START, 'evaluate_clarity')

graph.add_edge('evaluate_language', 'final_evaluation')
graph.add_edge('evaluate_analysis', 'final_evaluation')
graph.add_edge('evaluate_clarity', 'final_evaluation')

graph.add_edge('final_evaluation', END)

# Compile graph
workflow = graph.compile()
print(workflow.get_graph().print_ascii())

# Execute Graph
initial_state = {'essay_text': essay}
final_state = workflow.invoke(initial_state)

print(final_state)