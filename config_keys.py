import os

# LLM
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'default_api_key_service_1')

# LangChain
LANGCHAIN_OPENAI_API_KEY = os.getenv('LANGCHAIN_OPENAI_API_KEY', 'default_api_key_service_2')
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY', 'default_api_key_service_2')
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_PROJECT = "langsmith_tut_RealEstate"

# DataBase
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY', 'default_api_key_service_2')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'default_base') 

# Database - Tables
TABLE_NAME_USERINFO = 'Lead'
TABLE_NAME_FILTER = 'Filter'
TABLE_NAME_THREAD = 'Thread'