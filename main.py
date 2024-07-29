# Operation
from enum import auto
import os
import time
import logging
import werkzeug.exceptions
from dotenv import load_dotenv, find_dotenv
# API
from flask import Flask, request, jsonify
import requests
# LLM
from flask.sansio.scaffold import T_route
from langsmith import traceable
# Import Python modules
import core_functions
import functions
import format_functions
#import assistant
from _Init_ import client
from _Init_ import userID, userID_status
# from core_functions
from core_functions import assistant_id

# from config_keys import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, TABLE_NAME_USERINFO, TABLE_NAME_FILTER, TABLE_NAME_THREAD, LANGCHAIN_API_KEY, LANGCHAIN_TRACING_V2, LANGCHAIN_ENDPOINT, LANGCHAIN_PROJECT

load_dotenv(find_dotenv())
# os.environ["LANGCHAIN_OPENAI_API_KEY"] = str(os.getenv("LANGCHAIN_API_KEY"))
os.environ[
    "LANGCHAIN_OPENAI_API_KEY"] = "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"
os.environ["LANGCHAIN_API_KEY"] = "ls__c457ad9a6e6946f897ec0d4a184ba671"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "langsmith_tut_RealEstate"

# Configure logging
# logging.basicConfig(level=logging.INFO)
# Setup logging configuration
# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

# Check Calendly booking
# test = get_calendly()

# Create Flask app
app = Flask(__name__)


# Route to start the conversation
@app.route('/start', methods=['GET'])
@traceable(name="Chat - Start")
def start_conversation():
    # logging.info("Starting a new conversation...")
    # logging.info(f"New thread created with ID: {thread.id}")
    # Creater userID
    # THIS PART IS MISSING Check if userID is already created
    userID = functions.createUserID()['userID']
    userID_status = "New"

    # Create thread for OpenAI Assistant API
    thread = client.beta.threads.create()
    # Create thread in database
    threadID_DB = functions.createThread_DB(thread.id, userID)

    # Creater userID
    # THIS PART IS MISSING Check if userID is already created


    return jsonify({
        "thread_id": thread.id,
        "userID": userID,
        "userID_status": userID_status
    })


# Route to introduce the conversation
@app.route('/introduction', methods=['POST'])
@traceable(name="Chat - Introduction")
def introduce_conversation():
    f"""
    This function adds the messages in the thread which are created by the front-end during the introduction. 
    """
    global thread_id
    global memory
    global latest_userMessage

    data = request.json
    thread_id = data.get('thread_id')
    vf_memory = data.get('vf_memory')

    @traceable(name="parse_vfmemory")
    def parse_vf_memory(vf_memory):
        messages = []
        lines = vf_memory.split('\n')
        role = None
        content = []

        for line in lines:
            if line.startswith('assistant:'):
                if role and content:
                    messages.append({
                        "role": role,
                        "content": ' '.join(content).strip()
                    })
                role = 'assistant'
                content = [line[len('assistant:'):].strip()]
            elif line.startswith('user:'):
                if role and content:
                    messages.append({
                        "role": role,
                        "content": ' '.join(content).strip()
                    })
                role = 'user'
                content = [line[len('user:'):].strip()]
            else:
                content.append(line.strip())

        if role and content:
            messages.append({
                "role": role,
                "content": ' '.join(content).strip()
            })

        return messages

    messages = parse_vf_memory(vf_memory)
    for message in messages:
        print(message)

  
    addedMessages = core_functions.addMessages_Thread(thread_id, messages)

    # Get short-term memory from the thread
    memory = core_functions.thread_memory(thread_id)

    # Get latest_userMessage
    latest_userMessage = None  #is this ini really needed?
    for message in memory["conversation_memory"]:
        if message["role"] == "user":
            latest_userMessage = message["content"]
            break  # Stop after the first user message

    return jsonify({"response": thread_id})


# Route to for chatting
@app.route('/chat', methods=['POST'])
@traceable(name="Chat - Chatting")
def chat():
    global thread_id
    global user_input
    try:
        data = request.json
    except werkzeug.exceptions.BadRequest as e:
        logging.error(f"Failed to decode JSON object: {e}")
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')
    userID_status = data.get('userID_status')
    userID = data.get('userID')
    #Initzialitation of property related variables
    num_props = 0
    recommandProperty_executed = False
    calendlyLink = ""

    if not thread_id:
        logging.error("Error: Missing thread_id")
        return jsonify({"error": "Missing thread_id"}), 400

    # logging.info(f"Received message: {user_input} for thread ID: {thread_id}")


    ##START###Pre-Processing Messages#################################################################
    ##################################################################################################

    # Create User message
    user_message = core_functions.create_message(thread_id, user_input)

    #Create Short-Term Memory. Thread limitation of last 20 messages....should be fine for the beginning
    global memory
    memory = core_functions.thread_memory(thread_id)

    global latest_userMessage
    latest_userMessage = None

    for message in memory["conversation_memory"]:
        if message["role"] == "user":
            latest_userMessage = message["content"]
            break  # Stop after the first user message

    ##START###Pre-Processing Messages#################################################################
    ##################################################################################################

    # # Retrieve filter
    # filter_response = functions.retrieveFilter(userID)

    # if filter_response['status'] == 'success' and filter_response['data']:
    #     last_filter = filter_response['data'][0] # use filter for personalization
    # else:
    #     last_filter = None

    # personalization = f"""
    # #Personalize the answer for the user based on following information:
    # This is the current filter for the property search of the user:
    # {last_filter}

    # This filter shows the current interest of the user. Take this to personalize your response.
    # For example if the users filter is:
    # - Budget: 1500000
    # - Bedrooms: 2
    # - Amenties: wants a view on Burj Khalifa

    # And the result of the property search is:
    # - Price: 1700000
    # - Bedrooms: 2
    # - View: has a view on the sea

    # Answer in direction of: "Perfect! I found a property that matches your bedroom number. Instead of a view on Burj Khalifa I can offer a view on the sea. The price is slightly above your given budget. Do you want further information on this property?"
    # """

    from additional_instructions import additional_instructions_New, additional_instructions_Registered

    # Create run based on userID_status
    if userID_status == "New":
        tool_choice2 = "auto"
        run = core_functions.create_run(thread_id, assistant_id,
                                        additional_instructions_New,
                                        tool_choice2)

    elif userID_status == "Registered":
        tool_choice3 = "auto"
        run = core_functions.create_run(thread_id, assistant_id,
                                        additional_instructions_Registered,
                                        tool_choice3)
    else:
        print("Unknown user status")

    run_dict = run.dict()  # Convert Pydantic model to dictionary

    if "last_error" in run_dict and run_dict["last_error"]:
        error_code = run_dict["last_error"].get("code")
        error_message = run_dict["last_error"].get("message")
        # if "last_error" in run and run["last_error"]:
        #     error_code = run["last_error"]["code"]
        #     error_message = run["last_error"]["message"]
        # create_PDF = core_functions.create_pdf("reports/debug_report.pdf", error_code)
        data = {
            "response":
            "Sorry, your request could not get processed. Please try again.",
            "num_props": num_props,
            "userID_status": userID_status,
            "userID": userID,
            "recommandProperty_executed": recommandProperty_executed,
            "metadata": "",
            "calendlyLink": ""
        }
        return jsonify(data)

    else:  #This is the standard path for succesfull runs
        run_id = run.id

        #Retrieve and execute Run
        while True:
            retrieveRun = core_functions.retrieve_run(thread_id, run.id)

            if retrieveRun.status == 'completed':
                break

            elif retrieveRun.status == "queued":
                time.sleep(2)

            elif retrieveRun.status == "in_progress":
                runSteps = core_functions.list_runSteps(thread_id, run.id)

                # Assuming runSteps is iterable
                for step in runSteps:
                    runStep_id = step.id
                    retrieveRunStep = core_functions.retrieve_runStep(
                        thread_id, run.id, runStep_id)
                    # Optionally, add a delay here if needed to prevent too frequent polling
                    time.sleep(2)

            elif retrieveRun.status == 'requires_action':
                outputs = []
                tool_calls = retrieveRun.required_action.submit_tool_outputs.tool_calls

                # Call the modified process_tool_output function with a list of tool calls
                output, tool_outputs_to_submit = core_functions.process_tool_output(
                    thread_id, run_id, tool_calls, memory, latest_userMessage,
                    userID, userID_status)

                recommandProperty_executed = output[0]["data"]["recommandProperty_executed"]
                num_props = output[0]["data"]["num_props"]
                metadata = output[0]["data"]["metadata"] if recommandProperty_executed else ''
                calendlyLink = output[0]["data"]["calendlyLink"]

                # Check userID_status before calling extract_user_details
                if userID_status in ["New"]:
                    result = functions.extract_user_details(
                        output, userID,
                        userID_status)  #are the inputs still needed here?
                    if result.get("status") == 1:
                        userID = result["data"].get("userID", userID)
                        userID_status = result["data"].get(
                            "userID_status", userID_status)
                        updateThreadDB = functions.updateThread_DB(
                            thread_id, userID, userID_status)

        messages = client.beta.threads.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value
        memory = core_functions.thread_memory(thread_id)

        data = {
            "response": response,
            "num_props": num_props,
            "userID_status": userID_status,
            "userID": userID,
            "recommandProperty_executed": recommandProperty_executed,
            "metadata": metadata if recommandProperty_executed else '',
            "calendlyLink": calendlyLink
        }

        # Return as JSON response
        return jsonify(data)


# start the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
