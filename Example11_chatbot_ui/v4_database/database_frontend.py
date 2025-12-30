import streamlit as st

from backend import chatbot, retrieve_all_threads, save_thread_title, load_persisted_title
from langchain_core.messages import HumanMessage, AIMessage
import uuid
from langchain_ollama import ChatOllama

llm = ChatOllama(model='llama3.1')

# **************************************** utility functions *************************

def generate_thread_id():
    thread_id = uuid.uuid4()
    return str(thread_id)

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []
    st.session_state["thread_names"][thread_id] = None  # No title yet

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Check if messages key exists in state values, return empty list if not
    return state.values.get('messages', [])



# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if "thread_names" not in st.session_state:
    st.session_state["thread_names"] = {}  # {thread_id: "Title"}

for t in st.session_state['chat_threads']:
    if t not in st.session_state["thread_names"]:
        title = load_persisted_title(t)
        st.session_state["thread_names"][t] = title if title else ""

add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('My Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id in st.session_state['chat_threads'][::-1]:
    chat_title = st.session_state["thread_names"].get(thread_id)

    # Skip fresh chats that have no title yet (ChatGPT behavior)
    if not chat_title:
        continue
    # If no title assigned, show fallback
    # display = chat_title if chat_title else "New Chat"

    if st.sidebar.button(chat_title.replace('"',''), key=f"thread_{thread_id}"):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    # Create a short tile for this conversation.
    current = st.session_state["thread_id"]
    thread_name = st.session_state["thread_names"].get(current)
    if not thread_name:
        # chat_title = llm.invoke(f"Create a very short chat title for this message: {user_input}").content
        chat_title = llm.invoke(f"Return only a short chat title (max 3 words). Do not add any explanation, prefix, or extra text. Message: {user_input}").content
        st.session_state["thread_names"][current] = chat_title
        save_thread_title(current, chat_title)  # Persist to DB checkpoint metadata


    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

     # first add the message to message_history
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage):
                    # yield only assistant tokens
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})