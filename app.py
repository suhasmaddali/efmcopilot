from openai import OpenAI
import streamlit as st
import re
import traceback
import pandas as pd
import numpy as np
import time
from src.debugger import Debugger
from datetime import datetime
import os
from dotenv import load_dotenv
import boto3
import uuid
import time
import plotly.graph_objects as go
from src.prompts_new import (
    system_message_file_uploaded,
    question_generator_system_message,
    questions_additional_prompt
)
from langchain_nvidia_ai_endpoints import register_model, Model, ChatNVIDIA

from streamlit_feedback import streamlit_feedback
import streamlit as st

# Custom modules 
from src import utils

if 'session_timestamp' not in st.session_state:
    st.session_state.session_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# Getting access to credentials for loading data to database
platform = st.secrets['DATABASE']['PLATFORM']
aws_access_key_id = st.secrets['DATABASE']['AWS_ACCESS_KEY_ID']
aws_secret_access_key = st.secrets['DATABASE']['AWS_SECRET_ACCESS_KEY']
region_name = st.secrets['DATABASE']['REGION_NAME']
memory_location = st.secrets['DATABASE']['BUCKET']
number = st.secrets['DATABASE']['NUMBER']

# Getting access to user credentials to validate login
username_credentials = st.secrets['USER CREDENTIALS']['USERNAME']
password_credentials = st.secrets['USER CREDENTIALS']['PASSWORD']

base_url = st.secrets['USER CREDENTIALS']['BASE_URL']
api_key = st.secrets['USER CREDENTIALS']['API_KEY']

# Getting access to NVCF credentials for inference
# NVCF_CHAT_FUNCTION_ID = st.secrets['NVCF CREDENTIALS']['NVCF_CHAT_FUNCTION_ID']
# NVCF_URL = f"https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/{NVCF_CHAT_FUNCTION_ID}"
# NVCF_API_KEY = st.secrets['NVCF CREDENTIALS']['NVCF_API_KEY']
# MODEL = "meta/llama-3.1-8b-instruct"
# os.environ['NVIDIA_API_KEY'] = NVCF_API_KEY

NVCF_CHAT_FUNCTION_ID = st.secrets['NV PRIVATE LARGE MODEL']['NVCF_CHAT_FUNCTION_ID']
NVCF_URL = f"https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions/{NVCF_CHAT_FUNCTION_ID}"
NVCF_API_KEY = st.secrets['NV PRIVATE LARGE MODEL']['NVCF_API_KEY']
MODEL = "meta/llama-3.1-70b-instruct"
os.environ['NVIDIA_API_KEY'] = NVCF_API_KEY


# Initialize S3 client
# s3 = boto3.client(
#     platform,
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key,
#     region_name=region_name
# )

# def aws_credentials_feedback():
#     # AWS S3 Bucket details
#     bucket_name = memory_location

#     filename = f"feedback_data_{st.session_state.session_timestamp}.xlsx"
#     s3_file_path = f'feedback/{filename}'  # Path in the S3 bucket
#     local_file_path = 'feedback_data.xlsx'

#     return bucket_name, s3_file_path, local_file_path, s3


# def aws_credentials_chat_history():
#     # AWS S3 Bucket details
#     bucket_name = memory_location
#     filename = f"chat_history_{st.session_state.session_timestamp}.xlsx"
#     s3_file_path = f'saved_chats/{filename}'  # Path in the S3 bucket
#     local_file_path = 'chat_history.xlsx'

#     return bucket_name, s3_file_path, local_file_path, s3

# bucket_name, s3_file_path_feedback, local_file_path_feedback, s3 = aws_credentials_feedback()
# _, s3_file_path_chat_history, local_file_path_chat_history, _ = aws_credentials_chat_history()

# Encapsulated function to handle saving feedback locally
# def save_feedback_locally(feedback, file_path):
#     current_time = pd.Timestamp.now()
#     feedback_data = pd.DataFrame(
#         {
#             'SessionID': [st.session_state['session_id']],
#             'Timestamp': [current_time], 
#             'Feedback': [feedback]
#         }
#     )
    
#     if os.path.exists(file_path):
#         existing_data = pd.read_excel(file_path)
#         feedback_data = pd.concat([existing_data, feedback_data], ignore_index=True)
    
#     feedback_data.to_excel(file_path, index=False)

# def save_chat_history_locally(data_list, file_path):
#     # Capture the current session ID and timestamp
#     session_id = st.session_state.get('session_id', 'default_session')
#     current_time = pd.Timestamp.now()
    
#     # Convert the list of dictionaries to a DataFrame
#     data_df = pd.DataFrame(data_list)
    
#     # Add SessionID and Timestamp columns
#     data_df.insert(0, 'Timestamp', current_time)  # Insert Timestamp as the first column
#     data_df.insert(0, 'SessionID', session_id)    # Insert SessionID as the first column

#     # If the file already exists, read the existing data and concatenate it with new data
#     if os.path.exists(file_path):
#         existing_data = pd.read_excel(file_path)
#         data_df = pd.concat([existing_data, data_df], ignore_index=True)

#     # Save the updated data back to the Excel file
#     data_df.to_excel(file_path, index=False)

# # Encapsulated function to upload feedback to S3
# def upload_feedback_to_s3(s3_object, file_path, bucket, s3_key):
#     try:
#         s3_object.upload_file(file_path, bucket, s3_key)
#         st.success(f"Thank you for the feedback")
#     except Exception as e:
#         st.error(f"Error uploading file: {e}")

# # Encapsulated function to upload feedback to S3
# def upload_chat_history_to_s3(s3_object, file_path, bucket, s3_key):
#     try:
#         s3_object.upload_file(file_path, bucket, s3_key)
#     except Exception as e:
#         st.error(f"Error uploading file: {e}")

# def feedback_per_conversation():
#     # Dropdown to expand and show feedback options
#     with st.expander("Click to give feedback"):

#         # Check if thumbs up button was clicked
#         if st.button("👍 Thumbs Up", key="thumbs_up"):
#             st.session_state.feedback_type = "positive"
#             st.session_state.show_text_area = True

#         # Check if thumbs down button was clicked
#         if st.button("👎 Thumbs Down", key="thumbs_down"):
#             st.session_state.feedback_type = "negative"
#             st.session_state.show_text_area = True

#         # Show the text area for feedback based on the selection
#         if st.session_state.get('show_text_area', False):
#             if st.session_state.feedback_type == "positive":
#                 feedback = st.text_area("We are glad you liked it! Please provide your feedback (optional):")
#             elif st.session_state.feedback_type == "negative":
#                 feedback = st.text_area("Sorry to hear that! Please provide your feedback (optional):")

#             # Display submit button and thank you message after submission
#             if st.button("Submit Feedback"):
#                 st.session_state.feedback_submitted = True

#         # Display thank you message without clearing other inputs
#         if st.session_state.get('feedback_submitted', False):
#             st.success("Thank you for your feedback!")

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'task_submitted' not in st.session_state:
    st.session_state['task_submitted'] = False

if 'task_selected_state' not in st.session_state:
    st.session_state['task_selected_state'] = None

if 'display_colored_state' not in st.session_state:
    st.session_state['display_colored_state'] = None

if 'share_chat_history_button' not in st.session_state:
    st.session_state['share_chat_history_button'] = None

# First Page: Login Page
def login_page():

    # Inject CSS to change title color
    st.markdown("""
        <style>
        .title {
            color: #76B900;
            font-size: 2.5em;
        }
        </style>
        """, unsafe_allow_html=True)

    # Add your title with a specific CSS class
    st.markdown('<h1 class="title">EFM Co-Pilot 📊</h1>', unsafe_allow_html=True)

    # Wrap the entire form in one large box
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    
    # Create a form inside the single box
    with st.form("login_form"):
        st.header("Account Login")
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        submit_button = st.form_submit_button(label="Login")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Check login on form submit
    if submit_button:
        if username == username_credentials and password == password_credentials:
            st.session_state['logged_in'] = True
            st.rerun()  # Redirect to the next page immediately
        else:
            st.warning("Invalid username or password")

def task_page():
    # Inject CSS to change title color
    st.markdown("""
        <style>
        .title {
            color: #76B900;
            font-size: 2.5em;
        }
        </style>
        """, unsafe_allow_html=True)

    # Add your title with a specific CSS class
    st.markdown('<h1 class="title">EFM Co-Pilot 📊</h1>', unsafe_allow_html=True)

    st.markdown("**Prompt about your data, and get actionable insights (*check for accuracy*)** ✨")

    # Wrap the entire form in one large box
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    
    # Create a form inside the single box
    with st.form("login_form"):

        # logo = Image.open("images/NVIDIA-logo-BL.jpg")
        # st.image(logo, width=500)
        
        help_chat_history = """
        Do you want to allow sharing history of conversations?

        Yes - The chat conversations are recorded for improvement in answer quality, content and code generation.\n
        No - The chat conversations are not recorded."""
        share_chat_history = st.radio("Share chats for product development?", ["Yes", "No"], help=help_chat_history, index=0)
        
        # st.session_state['task_selected_state'] = task_selected
        st.session_state['share_chat_history_button'] = share_chat_history

        submit_button = st.form_submit_button(label="Submit")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Check login on form submit
    if submit_button:
        st.session_state['task_submitted'] = True
        st.rerun()

# Second Page: Content Page
def content_page():

    # logo = Image.open("images/nvidia-logo-horz (1).png")

    # st.sidebar.image(logo, width=150)

    load_dotenv()

    if 'messages_display' not in st.session_state:
        st.session_state.messages_display = []

    if 'debugger_messages' not in st.session_state:
        st.session_state.debugger_messages = []

    if 'old_formatted_date_time' not in st.session_state:
        now = datetime.now()
        st.session_state.old_formatted_date_time = now.strftime("%B %d, %Y %I:%M:%S %p")
    
    if 'new_formatted_date_time' not in st.session_state:
        st.session_state.new_formatted_date_time = None

    if 'conversations' not in st.session_state:
        st.session_state.conversations = {}
        st.session_state.conversations[f'{st.session_state.old_formatted_date_time}'] = []

    if 'flag_new_chat' not in st.session_state:
        st.session_state.flag_new_chat = 0

    if 'conversation_key' not in st.session_state:
        st.session_state.conversation_key = st.session_state.old_formatted_date_time

    if 'button_clicked_flag' not in st.session_state:
        st.session_state.button_clicked_flag = False

    if 'conversation_selected' not in st.session_state:
        st.session_state.conversation_selected = None

    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())

    if 'clear_chat_history_button' not in st.session_state:
        st.session_state.clear_chat_history_button = False

    if 'question_prompt_selected' not in st.session_state:
        st.session_state.question_prompt_selected = None

    if 'question_prompt_clicked' not in st.session_state:
        st.session_state.question_prompt_clicked = False

    # Clearing the LLM generated code 
    with open("llm_generated_code.py", "w") as file:
        pass

    FLAG = 0
            
    def extract_code(response_text: str):

        code_blocks = re.findall(r"```(python)?(.*?)```", response_text, re.DOTALL)
        code = "\n".join([block[1].strip() for block in code_blocks])

        if code:
            with open("llm_generated_code.py", "w") as file:
                file.write(code)
        return code

    def stream_responses(input_stream):

        response_list = []
        botmsg = st.empty()
        for chunk in input_stream:
            text = chunk.choices[0].delta.content
            if text:
                response_list.append(text)
                result = "".join(response_list).strip()
                botmsg.write(result + "▌")
                # time.sleep(0.05)
        if result:
            botmsg.write(result)  
        return result
    
    def stream_responses_static(input_stream):
        response_list = []
        botmsg = st.empty()
        for chunk in input_stream.split(' '):
            response_list.append(chunk)
            result = " ".join(response_list).strip()
            botmsg.write(result + "▌")
            time.sleep(0.1)
        botmsg.write(result)
        return result
    
    # Function to get questions from LLM based on the conversation history
    def generate_questions(
        conversation,
        categorical_columns_dict,
        numerical_columns_dict
    ):

        system_message_question_generator = question_generator_system_message.format(
            categorical_columns_dict=categorical_columns_dict, 
            numerical_columns_dict=numerical_columns_dict
        )

        questions_prompt = questions_additional_prompt
        prompt_dict = {
            "role": "user",
            "content": questions_prompt
        }

        conversation_for_questions = conversation.copy()
        conversation_for_questions.append(prompt_dict)
        # Loading the question generator system message into the main conversation history
        conversation_for_questions[0] = {'role': 'system', 'content': system_message_question_generator}

        questions = client.chat.completions.create(
            model=st.session_state["llm_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in conversation_for_questions
            ],
            stream=False,
            temperature=0.0,
            max_tokens=4096
        )

        questions_split = questions.choices[0].message.content.split("\n")
        return questions_split
            
    # Inject CSS to change title color
    st.markdown("""
        <style>
        .title {
            color: #76B900;
            font-size: 2.5em;
        }
        </style>
        """, unsafe_allow_html=True)

    # Add your title with a specific CSS class
    st.markdown('<h1 class="title">EFM Co-Pilot 📊</h1>', unsafe_allow_html=True)

    st.markdown("**Turn data into insights with advanced analytics (*check for accuracy*)** ✨")

    tab_selected = st.sidebar.tabs(["Configuration", "Chat History", "Feedback"])

    with tab_selected[0]:

        register_model(Model(id=MODEL, model_type="chat", client="ChatNVIDIA", endpoint=NVCF_URL))
        client = ChatNVIDIA(
            model=MODEL,
            temperature=0.0,
            max_tokens=4096
        )
        if "debugger" not in st.session_state:
            st.session_state["debugger"] = []
        st.session_state["llm_model"] = MODEL
        task_selected = "Analyze single data source"
        column_width = 750
        show_code = st.toggle("Show Code", value=True)
        debug_attempts = 3
        share_data = st.session_state['share_chat_history_button']

    with tab_selected[2]:
        st.header("Feedback")
        # feedback = st.text_area("Please provide your feedback here:", height=150)
        # if st.button("Submit", help="Click to submit feedback"):
        #     if feedback:            
        #         save_feedback_locally(feedback, local_file_path_feedback)
        #         upload_feedback_to_s3(
        #             s3_object=s3,
        #             file_path=local_file_path_feedback,
        #             bucket=bucket_name, 
        #             s3_key=s3_file_path_feedback
        #         )

        #         os.remove('feedback_data.xlsx')

    @st.cache_data
    def get_categorical_columns(dfs):

        categorical_columns = {}
        for col in dfs.columns:
            if dfs[col].dtype == "string":
                categorical_columns[col] = list(dfs[col].unique())
        return categorical_columns
    
    # @st.cache_data
    # def compare_categorical_columns(df1, df2):
    #     # Specify the datetime columns to exclude
    #     datetime_columns = ['Ord Date', 'Inv Date', 'Pl. GI Date', 'MAD', 'Allocation Date', 'CRD Date']
        
    #     # Initialize dictionaries to hold unique values
    #     df1_unique = {}  # Values in df1 but not in df2
    #     df2_unique = {}  # Values in df2 but not in df1
    #     intersection = {}  # Intersection of values between df1 and df2
        
    #     # Get the columns common to both dataframes and exclude datetime columns
    #     common_columns = [col for col in df1.columns if col in df2.columns and col not in datetime_columns]
        
    #     # Iterate over the common columns and compare the unique values
    #     for col in common_columns:
    #         if df1[col].dtype == "object" and df2[col].dtype == "object":  # Check if the column is categorical
    #             unique_values_df1 = set(df1[col].unique())  # Get unique values for the column in df1
    #             unique_values_df2 = set(df2[col].unique())  # Get unique values for the column in df2

    #             # Calculate differences and intersections
    #             df1_unique[col] = list(unique_values_df1 - unique_values_df2)  # Values in df1 but not in df2
    #             df2_unique[col] = list(unique_values_df2 - unique_values_df1)  # Values in df2 but not in df1
    #             intersection[col] = list(unique_values_df1 & unique_values_df2)  # Intersection of the two

    #     return df1_unique, df2_unique, intersection

    @st.cache_data
    def get_numerical_columns(dfs):

        numerical_columns = []
        for col in dfs.columns:
            if dfs[col].dtype == "float32":
                numerical_columns.append(col)

        return numerical_columns

    # @st.cache_data
    # def get_datetime_columns(dfs):
    #     datetime_columns = []
    #     actual_datetime_columns = ['Ord Date', 'Inv Date', 'Pl. GI Date', 'MAD', 'Allocation Date', 'CRD Date']
    #     for col in dfs.columns:
    #         if col in actual_datetime_columns:
    #             datetime_columns.append(col)
    #         # if dfs[col].dtype == "<M8[ns]":
    #         #     datetime_columns.append(col)
    #     return datetime_columns

    status_placeholder = st.empty()
    error_occurred = False

    with st.expander("Click to view the data", expanded=True):

        # first_file = st.selectbox("Select the file to analyze:", files_list)
        # df = pd.read_csv('../datasets/EFM_data/EFM BUF Data.csv', encoding='ISO-8859-1')

        # include_columns = [
        #     'Time_Period',
        #     'Marketing Sub Code', 
        #     'Business Unit', 
        #     'End Cust Group PROD (EFM)',
        #     'EC Customer Region',
        #     'Total RSF Rev.',
        #     'Total RSF Qty',
        #     'Actualized RSF Locked LM Rev.',
        #     'Actualized RSF Locked LM Qty',
        #     'Net B/S Qty (EFM)',
        #     'Net B/S Rev. (EFM)',
        #     'Opp EU In-Fcst Qty'
        # ]

        # dfs= df[include_columns].copy()
        # st.dataframe(dfs)

        directory_path = r"\\sapfsp-integ\IBP\PRD\Outbound\BW\Archive"
        dfs = utils.read_and_display_latest_file(directory_path)
        st.dataframe(dfs)

        # Get and display categorical columns
        categorical_columns_dict = get_categorical_columns(dfs)
        categorical_columns_dict_sample = {key: value[:15] for key, value in categorical_columns_dict.items()}

        # Get and display numerical columns
        numerical_columns_list = get_numerical_columns(dfs)

        # Get the current date
        present_date = datetime.now().date()

        # Format with default formatting and remove leading zeros
        present_date_formatted = present_date.strftime("%m/%d/%Y").lstrip("0").replace("/0", "/")

        current_dir = os.getcwd()

        time_profile_path = os.path.join(current_dir, "data", "Time Profile for BOT.csv")
        df_time_profile = pd.read_csv(time_profile_path)
        current_fiscal_quarter = df_time_profile[df_time_profile["Day"] == present_date_formatted]['Fiscal Quarter'].unique()[0]

        system_message = system_message_file_uploaded.format(
            categorical_columns_dict=categorical_columns_dict_sample, 
            numerical_columns_list=numerical_columns_list,
            present_date=present_date
        )

    if "messages" not in st.session_state:

        st.session_state.messages = ["placeholder"]

    st.session_state.messages[0] = {"role": "system", "content": system_message}

    with tab_selected[1]:

        if st.button("📝 Click for new chat", help="Click for new chat"):
            st.session_state.flag_new_chat = 1
            now = datetime.now()
            st.session_state.new_formatted_date_time = now.strftime("%B %d, %Y %I:%M:%S %p")
            st.session_state.conversations[f"{st.session_state.new_formatted_date_time}"] = []
            st.session_state.conversation_selected = st.session_state.new_formatted_date_time
            st.session_state.messages = []
            st.session_state.messages_display = []
            st.session_state.debugger_messages = []
            st.session_state.messages = ["placeholder"]
            st.session_state.messages[0] = {"role": "system", "content": system_message}
            st.session_state.button_clicked_flag = False
        st.markdown('<hr style="border:0.01px solid #cccccc">', unsafe_allow_html=True)
        for selected_conversation in list(st.session_state.conversations.keys()):
            if st.button(selected_conversation):
                st.session_state.conversation_selected = selected_conversation
                st.session_state.button_clicked_flag = True
                st.session_state.messages_display = st.session_state.conversations[selected_conversation]

        st.write(f"**Conversation selected:** *{st.session_state.conversation_selected}*")

    if st.session_state.flag_new_chat == 0:
        st.session_state.conversation_selected = st.session_state.old_formatted_date_time
        st.session_state.conversations[f'{st.session_state.conversation_selected}'] = st.session_state.messages_display

    if st.session_state.flag_new_chat == 1:
        if st.session_state.button_clicked_flag == False:
            st.session_state.conversation_selected = st.session_state.new_formatted_date_time
            st.session_state.conversations[st.session_state.conversation_selected] = st.session_state.messages_display

    i = 0
    for i, message in enumerate(st.session_state.conversations[st.session_state.conversation_selected]):
        if message['role'] == 'user':
            # if i != 0:
            #     if st.session_state['share_chat_history_button'] == "Yes":
            #         feedback_shared = streamlit_feedback(
            #             feedback_type="faces", 
            #             align="flex-start", 
            #             optional_text_label="[Optional] We value your feedback", 
            #             key=f"{i}"
            #         )
            with st.chat_message(message['role'], avatar="🔍"):
                st.markdown(message['content'])
        with st.container():
            if message['role'] == 'assistant':
                with st.status("📟 *Generating the code*...", expanded=show_code):
                    with st.chat_message(message['role'], avatar="🤖"):
                        st.markdown(message['content'])
            if message['role'] == 'plot':
                st.plotly_chart(message['figure'])
            if message['role'] == 'adhoc':
                st.write(message['message from adhoc query'])
            if message['role'] == 'show_data' or message['role'] == 'show_diff_data':
                st.dataframe(message['dataframe'], width=column_width)
            if message['role'] == 'forecast plot':
                st.plotly_chart(message['figure'])
            
    if prompt := st.chat_input("Write your lines here..."):

        additional_message = f"""
        INSTRUCTIONS 
        - If it is a general purpose query, let the user only know your purpose briefly.
        - Use only one function to answer all the questions asked by the user and nothing else. ALWAYS ensure to give only llm_response(df, current_quarter) function.
        - Import the necessary libraries which are needed for the task for running this function. If libraries are not needed, you need not import them. 
        - Try to give as accurate and executable code as possible without syntax errors.

        a) llm_response(df, current_quarter) - Use this function to create a plot, insights from data and tables.
        The output should be of the list format [].
        The elements in the list can 'fig' which is a figure, 'insights' which is a string and 'table' which is a dataframe table.
        You can decide whether to use one element, two elements or all three elements in the list or more. 

        INSTRUCTIONS
        NEVER give anything like example usage or anything outside of this function.
        Be sure to give the output which is strings in single line like insights etc. 
        When giving $, be sure to use \$ ALWAYS when giving insights. 
        Use FY24-Q4 as the current quarter for the time period. 
        The following is the present date:
        <{present_date}>

        The following is the present fiscal quarter and year. Be sure to use the current fiscal quarter and year below unless specified for filtering the Time_Period.
        FY stands for fiscal year. 25 stands for year 2025 and so on. 
        current_quarter={current_fiscal_quarter}

        When the question is about next quarters or past quarters, be sure to use 'Time_Period' which has future fiscal quarters and year
        and past fiscal quarters based on year and quarter
        
        Be sure to use only NVIDIA colors #76B900 when plotting.
        """



        # which is an ExcelFile format along with 'sheet_name'. The 'sheet_name' should be a keyword argument.
        enhanced_prompt = prompt + additional_message
        st.session_state.messages.append({"role": "user", "content": enhanced_prompt})
        st.session_state.messages_display.append({'role': 'user', 'content': prompt})
        with st.chat_message("user", avatar="🔍"):
            st.markdown(prompt)

        status_placeholder = st.empty()
        error_occurred = False
        metadata = {
            'categorical_columns_dict': categorical_columns_dict,
            'numerical_columns_list': numerical_columns_list
        }

        # st.write(st.session_state.messages)

        with status_placeholder.status("📟 *Generating the code*...", expanded=show_code):
            with st.chat_message("assistant", avatar="🤖"):
                response_list = []
                botmsg = st.empty()
                for chunk in client.stream(
                    [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ]
                ):
                    response_list.append(chunk.content)
                    result = "".join(response_list)
                    botmsg.write(result + "▌")
                if result:
                    botmsg.write(result) 

        st.session_state.messages.append({"role": "assistant", "content": result})
        st.session_state.messages_display.append({'role': 'assistant', 'content': result})
        code_generated = extract_code(result)

        with open("llm_generated_code.py", 'r') as file:
            exec_namespace = {}
            file_read = file.read()

            if 'llm_response' in file_read:
                try:
                    exec(file_read, exec_namespace)
                    llm_output_list = exec_namespace['llm_response'](dfs, current_quarter=current_fiscal_quarter)

                    for llm_output in llm_output_list:
                        if isinstance(llm_output, go.Figure):
                            st.plotly_chart(llm_output)
                            st.session_state.messages_display.append({'role': 'plot', 'figure': llm_output}) 
                        elif isinstance(llm_output, str):
                            result = stream_responses_static(input_stream=llm_output) 
                            st.session_state.messages_display.append({'role': 'adhoc', 'message from adhoc query': llm_output})
                        elif isinstance(llm_output, pd.DataFrame):
                            llm_output.reset_index(drop=True, inplace=True)
                            st.dataframe(llm_output, width=column_width)
                            st.session_state.messages_display.append({'role': 'show_data', 'dataframe': llm_output})  
                        else:
                            st.write("Unknown type")
                except Exception as e:    
                    st.write("Thank you for your query. Currently auto-correction of python code is currently in development progress and will be developed soon.")
                    # error_occurred = True
                    # debugger_selected = Debugger(
                    #     llm_model=st.session_state['debugger'],
                    #     kwargs=metadata
                    # )
                    # with status_placeholder.status("🔧 *Fixing the bugs from code*..."):
                    #     while error_occurred: 
                    #         error_count = 0
                    #         error_message = traceback.format_exc()
                    #         correction_message = {"role": "user", "content": f"The following error occurred for this code {code_generated}: {error_message}, give ONLY the correct code and nothing else. Ensure that there is only one output from the function."}
                    #         stream = debugger_selected.chat(
                    #             messages=correction_message,
                    #         )
                    #         result = stream_responses(input_stream=stream) 
                    #         st.session_state.messages.append(correction_message)
                    #         result_message = {"role": "assistant", "content": result}
                    #         st.session_state.messages.append(result_message)
                    #         code_generated = extract_code(result)

                    #         with open("llm_generated_code.py", 'r') as file:
                    #             exec_namespace = {}
                    #             file_read = file.read()
                    #         try:
                    #             exec(file_read, exec_namespace)
                    #             llm_output_list = exec_namespace['llm_response'](df)
                    #             error_occurred = False
                    #         except:
                    #             error_count = error_count + 1
                    #             if error_count > debug_attempts:
                    #                 error_occurred = False
                    # for llm_output in llm_output_list:
                    #     if isinstance(llm_output, go.Figure):
                    #         st.plotly_chart(llm_output)
                    #         st.session_state.messages_display.append({'role': 'plot', 'figure': llm_output}) 
                    #     elif isinstance(llm_output, str):
                    #         result = stream_responses_static(input_stream=llm_output) 
                    #         st.session_state.messages_display.append({'role': 'adhoc', 'message from adhoc query': llm_output})
                    #     elif isinstance(llm_output, pd.DataFrame):
                    #         llm_output.reset_index(drop=True, inplace=True)
                    #         st.dataframe(llm_output, width=column_width)
                    #         st.session_state.messages_display.append({'role': 'show_data', 'dataframe': llm_output})  
                    #     else:
                    #         st.write("Unknown type")


            # if st.session_state["share_chat_history_button"] == "Yes":
            #     # with st.expander("Share Feedback"):
            #     feedback_shared = streamlit_feedback(feedback_type="faces", align="flex-start", optional_text_label="[Optional] We value your feedback")
        
        # if share_data:
        #     save_chat_history_locally(
        #         data_list=st.session_state.messages_display, 
        #         file_path='chat_history.xlsx'
        #     )

        #     upload_chat_history_to_s3(
        #         s3_object=s3, 
        #         file_path=local_file_path_chat_history, 
        #         bucket=bucket_name, 
        #         s3_key=s3_file_path_chat_history
        #     )

        #     os.remove('chat_history.xlsx')

        # Clearing the LLM generated code 
        with open("llm_generated_code.py", "w") as file:
            pass

# Conditional rendering of pages based on login status
if st.session_state['logged_in']:
    if st.session_state['task_submitted']:
        content_page()
    else:
        task_page()
        # content_page()  # Show the second page if logged in
else:
    login_page()    # Show the login page if not logged in


   


