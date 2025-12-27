from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from typing import TypedDict, Literal
from pydantic import BaseModel, Field


model = ChatOllama(model='llama3.1')

class SentimentSchema(BaseModel):
    sentiment: Literal["positive", "negative"] = Field(description="Sentiment of the review either negative, positive")

class DiagnosisSchema(BaseModel):
    issue_type: Literal["UX", "Performance", "Bug", "Support", "Other"] = Field(description='The category of issue mentioned in the review')
    tone: Literal["angry", "frustrated", "disappointed", "calm"] = Field(description='The emotional tone expressed by the user')
    urgency: Literal["low", "medium", "high"] = Field(description='How urgent or critical the issue appears to be')

structured_model_sentiment = model.with_structured_output(SentimentSchema)
structured_model_diagnosis = model.with_structured_output(DiagnosisSchema)

class ReviewState(TypedDict):
    review: str
    sentiment: Literal["positive", "negative"]
    diagnosis: dict
    response: str

def find_sentiment(state: ReviewState):
    prompt = f'For the following review find out the sentiment \n {state["review"]}'
    response = structured_model_sentiment.invoke(prompt)
    print(f"Sentiment identified as - {response.sentiment}")
    return {'sentiment': response.sentiment}

def generate_positive_response(state: ReviewState):
    prompt = f"""Write a warm thank-you message in response to this review:    \n\n\"{state['review']}\"\n Also, kindly ask the user to leave feedback on our website."""
    response = model.invoke(prompt)
    return {"response": response.content}

def run_diagnosis(state: ReviewState):
    prompt = f"""Diagnose this negative review:\n\n{state['review']}\n"        "Return issue_type, tone, and urgency.    """
    response = structured_model_diagnosis.invoke(prompt)
    return {'diagnosis': response.model_dump()}

def generate_negative_response(state: ReviewState):
    diagnosis = state['diagnosis']
    prompt = f"""You are a support assistant.    The user had a '{diagnosis['issue_type']}' issue, sounded '{diagnosis['tone']}', and marked urgency as '{diagnosis['urgency']}'.    Write an empathetic, helpful resolution message."""
    response = model.invoke(prompt)
    return {"response": response.content}

def evaluate(state: ReviewState)-> Literal["generate_positive_response", "run_diagnosis"]:
    if state['sentiment'] == "positive":
        return "generate_positive_response"
    else:
        return "run_diagnosis"

graph = StateGraph(ReviewState)

graph.add_node('find_sentiment', find_sentiment)
graph.add_node('generate_positive_response', generate_positive_response)
graph.add_node('run_diagnosis', run_diagnosis)
graph.add_node('generate_negative_response', generate_negative_response)

graph.add_edge(START, 'find_sentiment')
graph.add_conditional_edges('find_sentiment', evaluate)
graph.add_edge('generate_positive_response', END)
graph.add_edge('run_diagnosis', 'generate_negative_response')
graph.add_edge('generate_negative_response', END)

workflow = graph.compile()
print(workflow.get_graph().draw_mermaid())
print(workflow.get_graph().draw_ascii())

positive_review = """
I recently upgraded to the Samsung Galaxy S24 Ultra, and I must say, its an absolute power house! The snapdragon 8 Gen 3 processor makes everything lightning fast-weather I'm gaming, multitasking, or editing photos. The 500mAH battery easily
lasts a full day even with heavy use, and the 45w fast charging is a life saver.

The S-Pen integration is a great touch for note-taking a quick sketches, though I don't use it often. What really blew me away is the 200MP camera-the night mode is stunning, capturing crisp, vibrant images even in low light. Zooming up to 
100x actually works well for distant objects, but anything beyond 30x loses quality.

However, the weight and size make it a bit uncomfortable for one-handed use. Also, Samsung's One UI still comes with bloatware-why do I need five different Samsung apps for things Google already provides? The $1,300 price tag is also a hard
pill to swallow.

Pros:
Insanely powerful processor (great for gaming and productivity)
Stunning 200MP camera with incredible zoom capabilities
Long battery life with fast charging
S-Pen support is unique and useful.

Cons:
Bulky and heavy-not great for one-handed use
Bloatware still exists in one UI
Expensive compared to competitors  
"""

negative_review = "I’ve been trying to log in for over an hour now, and the app keeps freezing on the authentication screen. I even tried reinstalling it, but no luck. This kind of bug is unacceptable, especially when it affects basic functionality."

initial_state = {'review': positive_review}

final_state = workflow.invoke(initial_state)

print(final_state)