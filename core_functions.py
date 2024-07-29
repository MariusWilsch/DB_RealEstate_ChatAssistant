# Operation
import os
import sys
import json
import logging
# Import python modules
from _Init_ import client
from config import workflowConfig, assistant_instructions, signUp_tool
import config
import functions
# LLM Imports
from langsmith.run_helpers import traceable
# Reporting
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# from config_keys import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, TABLE_NAME_USERINFO, TABLE_NAME_FILTER, TABLE_NAME_THREAD, LANGCHAIN_API_KEY, LANGCHAIN_TRACING_V2, LANGCHAIN_ENDPOINT, LANGCHAIN_PROJECT

os.environ[
    "LANGCHAIN_OPENAI_API_KEY"] = ""
os.environ["LANGCHAIN_API_KEY"] = "ls__c457ad9a6e6946f897ec0d4a184ba671"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "langsmith_tut_RealEstate"

# from config_keys import LANGAIRTABLE_API_KEY, AIRTABLE_BASE_ID, TABLE_NAME_USERINFO, TABLE_NAME_FILTER, TABLE_NAME_THREAD
# logging.basicConfig(level=logging.DEBUG)


def create_pdf(file_path, run_object):
    """
    Create a PDF file and print the attributes of the run_object into it.

    :param file_path: The path where the PDF will be saved.
    :param run_object: The object whose attributes need to be printed.
    """
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 40, "Debugging Variables Report")

    # Print each attribute
    y = height - 80
    for key, value in run_object.__dict__.items():
        c.setFont("Helvetica", 12)
        c.drawString(100, y, f"{key}: {value}")
        y -= 20

    c.save()

# Ensure the 'reports' directory exists
os.makedirs('reports', exist_ok=True)

# Get File_Ids for Assistant
def get_resource_file_ids(client):
  file_ids = []
  resources_folder = 'resources'
  if os.path.exists(resources_folder):
    for filename in os.listdir(resources_folder):
      file_path = os.path.join(resources_folder, filename)
      if os.path.isfile(file_path):
        with open(file_path, 'rb') as file:
          response = client.files.create(file=file, purpose='assistants')
          file_ids.append(response.id)
  return file_ids

###############START#####Core OpenAI Assistant Functions###################
@traceable(name="create_instructions")
def create_instructions(workflowConfig, assistant_instructions):
    """
    Check if workflowConfig contains all chapters in assistant_instructions using OpenAI's GPT-3.5,
    and extract instructions for different workflow statuses.

    Parameters:
    workflowConfig (list): The configuration details for the workflow as a list of dictionaries.
    assistant_instructions (str): The instructions provided to the assistant.

    Returns:
    tuple: A tuple containing three strings (instructions_None, instructions_New, instructions_Registered).
    """

    # Log input values
    logging.info(f"Received workflowConfig: {workflowConfig}")
    logging.info(f"Received assistant_instructions: {assistant_instructions}")

    # Prepare the prompt
    prompt = f"""
    The following are the workflow configurations and assistant instructions for a virtual assistant.

    First, check if all chapters in the assistant instructions are included in the workflow config. If any chapters are missing in the workflow config, list them. Otherwise, confirm that all chapters are present.

    Example 1:
    Workflow Config: [
        {{"#Role": ["None", "New", "Registered"]}},
        {{"#Goal of the conversation": ["None", "New", "Registered"]}}
    ]
    Assistant Instructions:
    #Role
    - You are a virtual assistant of the real estate agent Umar.

    #Goal of the conversation
    - The user should be excited about buying a property.

    #Skills
    - Knowledgeable in real estate terms.

    Missing chapters: ["#Skills"]

    Example 2:
    Workflow Config: [
        {{"#Role": ["None", "New", "Registered"]}},
        {{"#Goal of the conversation": ["None", "New", "Registered"]}},
        {{"#Skills": ["None", "New", "Registered"]}}
    ]
    Assistant Instructions:
    #Role
    - You are a virtual assistant of the real estate agent Umar.

    #Goal of the conversation
    - The user should be excited about buying a property.

    #Skills
    - Knowledgeable in real estate terms.

    All chapters are present.

    Your task:
    Workflow Config:
    Assistant Instructions:
    Check if all chapters are present and list any missing chapters.
    """

    # Call OpenAI API
    try:
        response = completion = client.chat.completions.create(
          model="gpt-4o",
          messages=[
            {"role": "system", "content": f"{prompt}"},
            {"role": "user", "content": f" Workflow Config:{workflowConfig}, Assistant Instructions:{assistant_instructions}"}
          ]
        )
        check_result = completion.choices[0].message.content

        # If there are missing chapters, raise an error
        if "missing" in check_result.lower():
            logging.error(check_result)
            raise ValueError(check_result)
        else:
            logging.info("All chapters are present in the workflow config.")

    except Exception as e:
        logging.error(f"Error during OpenAI API call: {e}")
        raise

@traceable(name="generate_instructions")
def generate_instructions(assistant_instructions, workflowConfig):
    def extract_chapters(instructions):
        chapters = {}
        lines = instructions.split('\n')
        current_chapter = None
        current_content = []

        for line in lines:
            if line.startswith('#'):
                if current_chapter:
                    chapters[current_chapter] = '\n'.join(current_content).strip()
                current_chapter = line.strip()
                current_content = []
            else:
                current_content.append(line)
        if current_chapter:
            chapters[current_chapter] = '\n'.join(current_content).strip()

        return chapters

    def filter_chapters(chapters, status):
        filtered_chapters = {}
        for chapter, content in chapters.items():
            for config in workflowConfig:
                if chapter in config and status in config[chapter]:
                    filtered_chapters[chapter] = content
        return filtered_chapters

    def compile_instructions(filtered_chapters):
        return '\n'.join(f"{chapter}\n{content}" for chapter, content in filtered_chapters.items())

    chapters = extract_chapters(assistant_instructions)

    instructions_None = compile_instructions(filter_chapters(chapters, "None"))
    instructions_New = compile_instructions(filter_chapters(chapters, "New"))
    instructions_Registered = compile_instructions(filter_chapters(chapters, "Registered"))

    return instructions_None, instructions_New, instructions_Registered

instructions_None, instructions_New, instructions_Registered = generate_instructions(assistant_instructions, workflowConfig)

# Create or load assistant
@traceable(name="create_assistant")
def create_assistant(client, workflowConfig, assistant_instructions):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file, load the assistant
  if os.path.exists(assistant_file_path):
        if os.path.getsize(assistant_file_path) > 0:  # Check if file is not empty
            try:
                with open(assistant_file_path, 'r') as file:
                    assistant_data = json.load(file)
                    assistant_id = assistant_data['assistant_id']
                    instructions_None = assistant_data.get('instructions_None', [])
                    instructions_New = assistant_data.get('instructions_New', [])
                    instructions_Registered = assistant_data.get('instructions_Registered', [])
                    print("Loaded existing assistant ID and instructions.")
                    return assistant_id, instructions_None, instructions_New, instructions_Registered
            except json.JSONDecodeError:
                print("Error: assistant.json file is corrupted. Creating a new assistant.")
        else:
            print("assistant.json file is empty. Creating a new assistant.")
        
  else:
    # Create a new assistant

    #######################################
    #######################################

    # Find and validate all given files
    file_ids = get_resource_file_ids(client)

    # Create the assistant
    assistant = client.beta.assistants.create(
        instructions=config.assistant_instructions,
        # temperature=1,
        model="gpt-3.5-turbo-0125",
        temperature = 0,
        tools=[
            # {
            #     "type": "retrieval"
            # },
            # Define all of your available tools here
            config.authenticateUser_tool,
            config.signUp_tool,
            config.retrieveFilter_tool,
            config.recordFilter_tool,
            config.recommandProperty_tool,
            config.updateUserRecord_tool,
            config.recordUserFeedback_tool,
            config.bookMeeting_tool
        ],
        # Assuming file_ids is defined elsewhere in your code
        # file_ids=file_ids
    )

    assistant_id = assistant.id
    # Print the assistant ID or any other details you need
    print(f"Assistant ID: {assistant.id}")

    # Call the function and get the result
    instructions_workflow = generate_instructions(assistant_instructions, workflowConfig)
      
      # create_instructions(workflowConfig, assistant_instructions)

    # Unpacking the returned tuple into three variables
    instructions_None, instructions_New, instructions_Registered = instructions_workflow

    # Create a assistant.json file to save the assistant ID and instructions
    with open(assistant_file_path, 'w') as file:
          json.dump({
              'assistant_id': assistant_id,
              'instructions_None': instructions_None,
              'instructions_New': instructions_New,
              'instructions_Registered': instructions_Registered
          }, file)
          print("Created a new assistant and saved the ID and instructions.")

    # assistant_id = assistant.id

  return assistant_id, instructions_None, instructions_New, instructions_Registered

# Create or load assistant
assistant_id, instructions_None, instructions_New, instructions_Registered = create_assistant(client, workflowConfig, assistant_instructions)


###########################################################################
# Assistant running
@traceable(name="UserMessage_Add")
def create_message(thread_id, user_input):
  """
  This function constructs and sends a message to a specified thread and returns the response.
  Parameters:
  - thread_id (str): The identifier of the thread.
  - user_input (str): The user's input to be included in the message.
  Returns:
  - str: The message creation response or error details.
  """
  content = f"{user_input}"

  try:
      # Attempt to create a message
    messages_created = client.beta.threads.messages.create(thread_id=thread_id,
                                          role="user",
                                          content=content)
    # Returning the list of messages created
    return messages_created
  except Exception as e:
    # Handle any errors that occur during the message creation process
    return f"Function failed: {str(e)}"  # Returning the error message

@traceable(name="addMessages_Thread")
def addMessages_Thread(thread_id, messages):
    for message in messages:
        response = client.beta.threads.messages.create(
            thread_id=thread_id,
            role=message['role'],
            content=message['content'])
        # print(f"Added message: {response['content']}")


@traceable(name="Thread_Memory")
def thread_memory(thread_id):
    thread_messages = client.beta.threads.messages.list(thread_id)
    memory = {"conversation_memory": []}

    for message in thread_messages:
        role = message.role
        content_list = message.content

        for content in content_list:
            if content.type == "text":
                text_value = content.text.value
                memory["conversation_memory"].append({
                    "role": role,
                    "content": text_value
                })

    return memory


@traceable(name="runThread")
def create_run(thread_id, assistant_id, additional_instructions, tool_choice):
    # max_retries = 3
    # for attempt in range(max_retries):
    #     try:
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant_id,
                additional_instructions=additional_instructions,
                temperature=0,
                tool_choice=tool_choice
            )
            return run
        # except openai.error.RateLimitError as e:
        #     if attempt < max_retries - 1:
        #         wait_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)  # Exponential backoff
        #         print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
        #         time.sleep(wait_time)
        #     else:
        #         print("Max retries exceeded. Please check your plan and billing details.")
        #         return None  # Indicate failure after max retries
        # except Exception as e:
        #     print(f"An unexpected error occurred: {e}")
        #     return None  # Indicate failure on other exceptions

@traceable(name="########run########")
def retrieve_run(thread_id, run_id):
    retrieve_run = client.beta.threads.runs.retrieve(
    thread_id=thread_id,
    run_id=run_id
  )
    return retrieve_run

@traceable(name="list_runSteps")
def list_runSteps(thread_id, run_id):
    list_runSteps= client.beta.threads.runs.steps.list(
        thread_id=thread_id,
        run_id=run_id
    )
    return list_runSteps

@traceable(name="retrieve_Step")
def retrieve_runStep(thread_id, run_id, step_id):
    retrieve_runStep = client.beta.threads.runs.steps.retrieve(
    thread_id=thread_id,
    run_id=run_id,
    step_id=step_id
  )
    return retrieve_runStep


@traceable(name="toolOutputs")
def process_tool_output(thread_id, run_id, tool_calls, memory, latest_userMessage, userID, userID_status):
    tool_outputs_to_submit = []  # Reset for this iteration
    outputs = []  # Initialize outputs list
    recommandProperty_executed = False
    num_props = 0

    # Iterate over each tool call
    for tool_call in tool_calls:
        tool_call_id = tool_call.id  # Use dot notation to access attributes
        function_name = tool_call.function.name  # Use dot notation to access attributes
        arguments = json.loads(tool_call.function.arguments)  # Use dot notation to access attributes

        if hasattr(functions, function_name):
            function_to_call = getattr(functions, function_name)

            # Process function call based on the function name
            if function_name in ["updateUserRecord", "recordFilter"]:
                output = function_to_call(arguments, userID, thread_id)
            elif function_name == "recommandProperty":
                output = function_to_call(arguments, userID, userID_status, thread_id, latest_userMessage, memory)
            elif function_name == "retrieveFilter":
                output = function_to_call(userID)
            elif function_name == "signUp":
                output = function_to_call(arguments, userID, userID_status, memory, latest_userMessage, signUp_tool)
            elif function_name == "recordUserFeedback":
                output = function_to_call(arguments, thread_id)
            elif function_name == "bookMeeting":
                output = function_to_call(thread_id)
            else:
                output = function_to_call(arguments)

            if isinstance(output, str):
                output = json.loads(output)  # Parse JSON string to dictionary if necessary

            # Initialize output dictionary with potential empty values
            output_dict = {
                "status": output.get("status", ""),
                "message": output.get("message", ""),
                "data": output.get("data", {}),
                "data_llm": output.get("data_llm", {})  # currently not used
            }

            # Create function output dictionary
            function_output = {
                "function_name": function_name,
                "status": output_dict["status"],
                "message": output_dict["message"],
                "data": output_dict["data"],
                "data_llm": output_dict["data_llm"],
                "size": sys.getsizeof(json.dumps(output_dict))
            }

            outputs.append(function_output)

            tool_output_to_submit = {
                "tool_call_id": tool_call_id,
                "output": json.dumps(output_dict)
            }
            tool_outputs_to_submit.append(tool_output_to_submit)

            # Debugging statement to print tool_call_id and tool_outputs_to_submit
            print(f"Processing tool_call_id: {tool_call_id}")
            print(f"tool_outputs_to_submit: {tool_outputs_to_submit}")

        # Ensure recommandProperty_executed is added to all outputs
        for function_output in outputs:
            # Ensure "data" exists and is a dictionary
            if "data" not in function_output or not isinstance(function_output["data"], dict):
                function_output["data"] = {}

            # # Update the "data" dictionary based on the function_name
            # if function_output["function_name"] == "recommandProperty":
            #     function_output["data"]["recommandProperty_executed"] = output_dict["data"].get("recommandProperty_executed", False)
            #     function_output["data"]["num_props"] = output_dict["data"].get("num_props", 0)
            # else:
            #     function_output["data"]["recommandProperty_executed"] = False
            #     function_output["data"]["num_props"] = 0

            # Update the "data" dictionary based on the function_name
            if function_output["function_name"] == "recommandProperty":
                if isinstance(output_dict["data"], dict):
                    # If data is a dictionary, handle it directly
                    function_output["data"]["recommandProperty_executed"] = output_dict["data"].get("recommandProperty_executed", False)
                    function_output["data"]["num_props"] = output_dict["data"].get("num_props", 0)
                elif isinstance(output_dict["data"], list):
                    # If data is a list, iterate through to find the relevant dictionary
                    for item in output_dict["data"]:
                        if item.get("function_name") == "recommandProperty":
                            function_output["data"]["recommandProperty_executed"] = item.get("recommandProperty_executed", False)
                            function_output["data"]["num_props"] = item.get("num_props", 0)
                            break
                    else:
                        # If no matching dictionary is found, set default values
                        function_output["data"]["recommandProperty_executed"] = False
                        function_output["data"]["num_props"] = 0
            else:
                function_output["data"]["recommandProperty_executed"] = False
                function_output["data"]["num_props"] = 0

            # Update the "data" dictionary based on the function_name
            if function_output["function_name"] == "bookMeeting":
                function_output["data"]["calendlyLink"] = output_dict["data"].get("calendlyLink", "")
            else:
                function_output["data"]["calendlyLink"] = ""
                
                

    # Submit all collected outputs together
    if tool_outputs_to_submit:
        client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs_to_submit)

    return outputs, tool_outputs_to_submit

###############END#####Core OpenAI Assistant Functions###################
#########################################################################

