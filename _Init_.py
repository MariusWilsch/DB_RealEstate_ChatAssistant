# Operation
from dotenv import load_dotenv, find_dotenv
import logging

# LLM related imports
import openai
from openai import OpenAI
from langsmith import wrappers

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Check OpenAI version compatibility
def check_openai_version():
  required_version = version.parse("1.1.1")
  current_version = version.parse(openai.__version__)
  if current_version < required_version:
    raise ValueError(
        f"Error: OpenAI version {openai.__version__} is less than the required version 1.1.1"
    )
  else:
    logging.info("OpenAI version is compatible.")

# Initialize OpenAI client
from config_keys import OPENAI_API_KEY
if not OPENAI_API_KEY:
  raise ValueError("No OpenAI API key found in environment variables")
client = wrappers.wrap_openai(OpenAI())

# Initialize userID and userID_status
global userID, userID_status
userID = "None"
userID_status = "None"

