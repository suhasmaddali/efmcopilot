from openai import OpenAI
import streamlit as st
import re
import pandas as pd
import numpy as np
import time
from dotenv import load_dotenv
import subprocess
import os

load_dotenv()

if 'messages_latest' not in st.session_state:
    st.session_state.messages_latest = []

FLAG = 0

base_url = st.secrets['USER CREDENTIALS']['BASE_URL']
api_key = st.secrets['USER CREDENTIALS']['API_KEY']
        
def extract_code(response_text: str):

    code_blocks = re.findall(r"```(python)?(.*?)```", response_text, re.DOTALL)
    code = "\n".join([block[1].strip() for block in code_blocks])

    if code:
        with open("streamlit_test.py", "w") as file:
            file.write(code)
    return code 

def run_streamlit_app(file_name):
    # Ensure the file exists
    if not os.path.exists(file_name):
        print(f"File {file_name} does not exist.")
        return
    
    try:
        # Run the Streamlit script
        print(f"Running Streamlit app: {file_name}")
        subprocess.run(["streamlit", "run", file_name])
    except Exception as e:
        print(f"Error running Streamlit app: {e}")

st.title("Website Creator 📊")
st.markdown("**Create your favorite website in minutes with prompts.** ✨")

model_selected = st.sidebar.selectbox("Select the large language model:", ["meta/llama-3.1-70b-instruct", "Mixtral-8x22B"])
if "llm_model" not in st.session_state:
    st.session_state["llm_model"] = []

if model_selected == "Llama-3":
    st.session_state["llm_model"] = "meta/llama3-70b-instruct"
else:
    st.session_state["llm_model"] = "mistralai/mixtral-8x22b-instruct-v0.1"

client = OpenAI(
    base_url = base_url,
    api_key = api_key
)

if "messages" not in st.session_state:

    system_message = """
    If it is a general purpose query, NEVER follow anything present in triple hiphens. 
    Instead reply like a general purpose large language model without any coding.
    ALWAYS write a full streamlit code to achieve the task whichever user asks. 
    
    ---
    Use any of these packages Pandas, Streamlit and Plotly ONLY. Use streamlit to display ALL the print statements and something that is important for user to see.
    Provide SINGLE CODE BLOCK with a solution for operations research and optimization.

    Provide SINGLE CODE BLOCK when needed.

    INSTRUCTIONS
    - When user gives additional queries, ALWAYS give the FULL and COMPLETE code.
    - USE SINGLE CODE BLOCK with a solution 
    - ALWAYS WRAP UP THE CODE IN A SINGLE CODE BLOCK
    - The code block must start and end with ```python and then end with ```
    - Import ALL necessary modules when executing code 
    ---

    """

    st.session_state.messages = [{"role": "system", "content": system_message}]

i = 0
for message in st.session_state.messages_latest:
    if message['role'] == 'user' or message['role'] == 'assistant':
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    if message['role'] == 'plot':
        st.plotly_chart(message['figure'])
    if message['role'] == 'adhoc':
        st.write(message['message from adhoc query'])
    
if prompt := st.chat_input("Write your lines here..."):

    additional_prompt = "Instruction: Based on this, write a FULLY functional streamlit code to achieve whatever user described just now. ONLY code and nothing else."
    enhanced_prompt = prompt + additional_prompt
    st.session_state.messages.append({"role": "user", "content": enhanced_prompt})
    st.session_state.messages_latest.append({'role': 'user', 'content': prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
            temperature=0.0,
            max_tokens=2048
        )
        response_list = []
        botmsg = st.empty()
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                response_list.append(text)
                result = "".join(response_list).strip()
                botmsg.write(result + "▌")
                time.sleep(0.05)
                response = result
        if result:
            botmsg.write(result)    

        st.session_state.messages.append({"role": "assistant", "content": result})
        st.session_state.messages_latest.append({'role': 'assistant', 'content': result})
        extracted_code = extract_code(result)
        streamlit_file = 'streamlit_test.py'
        run_streamlit_app(streamlit_file)

        # try:
        #     df = pd.ExcelFile('uploaded_data/uploaded_file.xlsx')
        #     with open("streamlit_test.py", 'r') as file:
        #         exec_namespace = {}
        #         exec(file.read(), exec_namespace)
        #     fig_returned = exec_namespace['create_plot'](df)
        #     st.plotly_chart(fig_returned)
        #     st.session_state.messages_latest.append({'role': 'plot', 'figure': fig_returned})   
        # except:
        #     pass

        # try: 
        #     message_returned = exec_namespace['data_exploration'](df)
        #     client = OpenAI(
        #         base_url = "https://integrate.api.nvidia.com/v1",
        #         api_key = "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"
        #     )
        #     stream = client.chat.completions.create(
        #         model="mistralai/mixtral-8x22b-instruct-v0.1",
        #         messages=[
        #             {'role': 'user', 'content': message_returned + ". Re-word this and make it easier to understand. Note that these are the orders for NVIDIA from various customers."}
        #         ],
        #         stream=True,
        #         temperature=0.0,
        #         max_tokens=2048
        #     )
        #     response_list = []
        #     botmsg = st.empty()
        #     for chunk in stream:
        #         text = chunk.choices[0].delta.content
        #         if text:
        #             response_list.append(text)
        #             result = "".join(response_list).strip()
        #             botmsg.write(result + "▌")
        #             time.sleep(0.05)
        #             response = result
        #     if result:
        #         botmsg.write(result) 

        #     augmented_message = "Here is the output as a result of executing the above python code in triple backticks. ```" + \
        #     result + "``` Be sure to use this information when trying to answer any user questions without coding only if possible."
        #     st.session_state.messages.append(
        #         {
        #             'role': 'user',
        #             'content': augmented_message
        #         }
        #     )
            
        #     st.session_state.messages_latest.append({'role': 'adhoc', 'message from adhoc query': result})
        # except Exception as e:
        #     st.write(e)

        


