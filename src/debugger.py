from openai import OpenAI
import streamlit as st

# base_url = st.secrets['USER CREDENTIALS']['BASE_URL']
# api_key = st.secrets['USER CREDENTIALS']['API_KEY']

# class Debugger:
#     def __init__(self, llm_model, kwargs):

#         self.client = OpenAI(
#             base_url = base_url,
#             api_key = api_key
#         )

#         self.llm_model = llm_model
#         self.categorical_columns_dict = kwargs['categorical_columns_dict']
#         self.numerical_columns_dict = kwargs['numerical_columns_dict']

#         self.system_message_file_uploaded = f"""            
#             The following in double backticks (``) is provided for you to get context about the dataset.
#             Do not use this information for plotting but only to help you get understanding of the dataset.
#             ``
#             The following are the categorical columns and the corresponding unique categories per column.

#             <{self.categorical_columns_dict}>

#             The following are the numerical columns present in the data.
        
#             <{self.numerical_columns_dict}>
#             ``
#             Your task is to give the correct code based on the error code which is given by the user. 

#             INSTRUCTIONS
#             - ALWAYS give ONLY the corrected code and nothing else
#             - USE SINGLE CODE BLOCK with a solution 
#             - ALWAYS WRAP UP THE CODE IN A SINGLE CODE BLOCK
#             - The code block must start and end with ```python and then end with ```
#         """

#     def chat(self, messages, stream=True, temperature=0, max_tokens=2048):

#         output_stream = self.client.chat.completions.create(
#             model=self.llm_model,
#             messages=[
#                 {"role": "system", "content": self.system_message_file_uploaded},
#                 messages
#             ],
#             stream=stream,
#             temperature=temperature,
#             max_tokens=max_tokens
#         )

#         return output_stream


