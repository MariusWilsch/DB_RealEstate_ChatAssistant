# Operation
import os
import random
import json
import yaml
from collections import defaultdict
# API
import requests
# LLM
from langchain_openai import OpenAIEmbeddings
from langsmith.run_helpers import traceable
# Import other Python modules
from _Init_ import client
from propertySearch import PropertySearch


from config_keys import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, TABLE_NAME_USERINFO, TABLE_NAME_FILTER, TABLE_NAME_THREAD

# Global counter for tracking consecutive "User not found" responses
login_attempt_counter = 0


########################################################
########################################################
@traceable(name="verify_input")
def verify_input(arguments, memory, latest_userMessage, description_arguments):
    # latest_userMessage = None

    # for message in memory["conversation_memory"]:
    #     if message["role"] == "user":
    #         latest_userMessage = message["content"]
    #         break  # Stop after the first user message

    examples_json = {
        "arguments_val": [{
            "parameter1": "",
            "parameter2": "<value from the arguments list>",
            "parameter3": "<value from the arguments list>"
        }]
    }

    examples_json_real = {
        "arguments_val": [{
            "Email": "",
            "Name": "Peter",
            "Location": "Munich"
        }]
    }

    system_instructions = f"""
    #Role - You are a highly skilled assistant in programming and data handling. Your task is to take the input arguments and verify if the arguments are derived from the latest user message or the content of the user in the thread memory. 
    #Important! - Your impact on this task is business critical. If you make errors, the business will break. I fully trust in your skills.

    # Output format
    Provide the output in JSON-Format.
    The data schema should be like this:
    {examples_json}

    Where the parameters1, parameters2, parameters3 etc. show the name of the parameters. This can be for example the "Name", "Email", ... etc.
    And the value for this parameters show if the information is available in the last user message or content of the thread. For this overtake the value from the arguments list.
    If the value is hallucinated - means NOT available in laster user message or memory - than please take the content of the thread memory and try to derive the right value out of it. If you cannot find the right value provide the empty value "".

   1. Example: 
    arguments: {{"email":"peter@gmx.com", "name":"Peter"}} provided by function calling
    Thread Memory: ## The latest user message: Log In
    ## The thread memory: {{'conversation_memory': [{{'role': 'user', 'content': 'my name is Peter'}}, {{'role': 'assistant', 'content': "No worries! Let's create a new account for you. Could you please provide me with your name, email address, and phone number (optional)? This information will help us personalize your experience. 📝✨"}}, {{'role': 'user', 'content': 'ah sry I want a new account'}}, {{'role': 'assistant', 'content': 'Can you give me your email for logging in? 🔑 For our Beta-Testing phase only the E-Mail is needed without a password. This will be changed in production.'}}, {{'role': 'user', 'content': 'Log In'}}, {{'role': 'assistant', 'content': "Hi! I'm Emir, your virtual assistant. 🤖 How can I help you today? 😊"}}]}}

    For outcomes which are hallucinated:
    Means the e-mail is NOT available in the last user message or thread memory. Try to find out the right value out of the content of the thread memory.
    Here is the desription of the arguments: {description_arguments}

    For outcomes derived from the conversation with the user:
    Means the name is available in the last user message or thread memory. It gets the value 1 in the JSON output.

    The JSON output would look like:
    {examples_json_real}


    # Here are the relevant information:
    ## The parameters and values provided by the function calling: {arguments}

    ## The latest user message: {latest_userMessage}
    ## The content of the thread memory: {memory}
    """

    completion = client.chat.completions.create(
        # model="gpt-3.5-turbo-0125",
        model="gpt-4-turbo",
        response_format={"type": "json_object"},
        temperature=0,
        messages=[{
            "role": "system",
            "content": system_instructions
        }, {
            "role":
            "user",
            "content":
            f"""
        Please provide me the JSON-Format - strictly follow the format given in the system instructions - and tell me what parameters are derived from the latest user message or the thread memory and what are hallucinated from the Large-Language-Model.
        """
        }])

    # finish_reason = chat_completion.choices[0].finish_reason

    # if(finish_reason == "stop"):
    #     data = completion.choices[0].message.content

    #     arguments_val = json.loads(data)

    #     for arguments_val in arguments_val['ski_resorts']:
    #         print(ski_resort['name']+" : "+str(ski_resort['slope_kilometers'])+"km")
    # else :
    #     print("Error! provide more tokens please")

    print(completion.choices[0].message)

    return completion.choices[0].message.content


########################################################
########################################################
@traceable(name="createUserID")
def createUserID():

    # Generate a random number for the userID
    random_number = random.randint(10000000, 99999999)
    userID = str(random_number)

    # Prepare the data payload for creating a record
    data_payload = {"records": [{"fields": {"UserID": userID}}]}

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_USERINFO}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Sending the POST request to Airtable
        response = requests.post(url, headers=headers, json=data_payload)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        data = response.json()
        userID = data['records'][0]['fields']['UserID']
        userID_status = "New"
        # On success, parse and return the response
        return {
            "message": "Record created successfully.",
            "details": response.json(),
            "userID": userID,
            "userID_status": userID_status
        }
    except requests.exceptions.RequestException as e:
        # Return detailed error information in case of failure
        return {
            "error": f"Airtable API request failed: {str(e)}",
            "details": response.text if response else "No response"
        }

@traceable(name="updateUserRecord")
def updateUserRecord(arguments, userID, thread_id):
    # Retrieve User Record
    user_record_response = retrieveUserRecord(userID)

    # # Unpack the response
    # response_message, user_record, record_available = user_record_response

    # # Check if records are available
    # if not record_available:
    #     return {
    #         "status": 2,
    #         "message": "User record not found.",
    #         "data": {
    #             "details": []
    #         }
    #     }

    # Check the response status
    if user_record_response['status'] != 1:
        return {
            "status": 2,
            "message": "User record not found.",
            "data": {
                "details": []
            }
        }

    # Unpack the response
    user_record = user_record_response['data']
    # Define all field names exactly as they appear in the 'fields' dictionary
    fields = [
        "Name",
        "ThreadID",
        "LogIn",
        "UserID",
        "PhoneNumber",
        "Email",
        "SocialMedia",
        "SocialMediaName"  # Correcting the case to match the user_record exactly
    ]

    updated_fields = {}
    current_fields = user_record[
        'fields']  # Access the nested 'fields' dictionary

    for field in fields:
        # Use new value from arguments if available, otherwise use the existing value from user_record
        if field in arguments and arguments[field] is not None:
            updated_fields[field] = arguments[
                field]  # Keep the case from the input
        elif field in current_fields:
            updated_fields[field] = current_fields[
                field]  # Keep the case from the user_record

    # Ensure ThreadID is set to the passed thread_id
    updated_fields["ThreadID"] = thread_id

    if not any(
            current_fields.get(field, None) != updated_fields.get(field, None)
            for field in fields):
        return {
            "status": 2,
            "message": "No updates necessary.",
            "data": {
                "details": []
            }
        }

    # Prepare the data for update
    data_payload = {"fields": updated_fields}
    print(data_payload)  # Debug: Check what will be sent
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_USERINFO}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=data_payload)

    if response.status_code == 200:
        return {
            "status": 1,
            "message": "User information updated successfully.",
            "data": {
                "details": response.json()
            }
        }
    else:
        try:
            error_json = response.json()
        except ValueError:
            # If response is not JSON, fall back to plain text
            error_json = {"error": response.text}

        return {
            "status": 0,
            "message": f"Failed to update user information: {response.text}",
            "data": {
                "details": error_json
            }
        }

@traceable(name="retrieveUserRecord")
def retrieveUserRecord(userID):
    """
  Retrieves the latest record associated with a given userID from Airtable.
  If no userID is provided, the function will handle the case appropriately.

  :param userID: str, User identifier for which to fetch the latest record. Optional.
  :return: dict or str, Response from the API or an appropriate message.
  """
    if not userID:
        return "No userID provided. Please provide a valid userID to fetch the record."

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_USERINFO}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        'filterByFormula': f"{{UserID}}='{userID}'",
        'sort[0][field]': 'Created at',
        'sort[0][direction]': 'desc',
        'maxRecords': 1
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        records = response.json().get('records')
        if records:
            return {
                "status": 1,
                "message": "User information retrieved successfully.",
                "data": records[0]
            }
        else:
            return {
                "status": 2,
                "message": "No records found for the given userID.",
                "data": []
            }
    else:
        try:
            error_json = response.json()
        except ValueError:
            # If response is not JSON, fall back to plain text
            error_json = {"error": response.text}

        return {
            "status": 0,
            "message": f"Failed to update user information: {response.text}",
            "data": error_json
        }

@traceable(name="extractUserDetails")
def extract_user_details(outputs, userID, userID_status):
    f"""
    The userID gets created with every thread
    - userID has to be updated as usered was already registered
    - userID_status has to be updated as user got "Registered" during the run
    Would it not be the best to directly create a userID for every new user? So it does not have to be created and updated here? So u just check if info is available...and if user gets authenticated it can be updated...seems legit... ---> actually two options...authenticate or signUp?
    """
    try:
        # Initialize 'data' to handle cases where it's not set in 'outputs'
        data = {}

        # Check if 'outputs' is a list and contains at least one dictionary
        if isinstance(outputs, list) and outputs:
            data = outputs[
                0]  # Assume the first item in the list is the required dictionary

            # Check if 'data' is not empty
            if 'data' in data and data['data']:
                # Process the data
                if 'details' in data['data'] and 'records' in data['data'][
                        'details']:
                    for record in data['data']['details']['records']:
                        if 'fields' in record:
                            new_userID = record['fields'].get('UserID')
                            # Extracting the userID_status from data if available
                            new_userID_status = data['data'].get('userID_status', userID_status)
                            if new_userID and new_userID.lower() != 'none':
                                userID = new_userID
                            if new_userID_status and new_userID_status.lower() != 'none':
                                userID_status = new_userID_status

        #müssen den Thread dann noch updaten...das können wir aber dann eventuell in authenticate machen? oder besser hier

        response = retrieveUserRecord(userID)
        user_record = response["data"]
        # if not record_available:
        if not user_record:
            return {
                "status": 2,
                "message": "User record not available.",
                "data": {
                    "userID": "None",
                    "userID_status": "None",
                    # "details": data.get('data', {})
                    "details": ()
                }
            }

        # if not user_record or not user_record.get("fields"):
        #     return {
        #         "status": 2,
        #         "message": "User record fields are empty.",
        #         "data": {
        #             "userID": "None",
        #             "userID_status": "None",
        #             # "details": data.get('data', {})
        #         }
        #     }

        latest_record = user_record["fields"]
        user_id = userID
        email = latest_record.get("Email", "")

        if user_id is not None:
            if email is None or email == "":
                userID = user_id
                userID_status = "New"
            else:
                userID = user_id
                userID_status = "Registered"

        return {
            "status": 1,
            "message": "User details extracted successfully.",
            "data": {
                "userID": userID,
                "userID_status": userID_status,
                # "details": data.get('data', {})
            }
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Failed to decode JSON: {str(e)}",
            "data": {
                "userID": userID,
                "userID_status": userID_status,
                "details": json.dumps(outputs) if outputs else "No data"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "data": {
                "userID": userID,
                "userID_status": userID_status,
                "details": json.dumps(outputs) if outputs else "No data"
            }
        }


# ######THREAD#############START##########################
# ########################################################
# Create thread/session in database
@traceable(name="createThread_DB")
def createThread_DB(thread_id, userID):
    # Payload for creating a record
    data_payload = {
        "records": [{
            "fields": {
                "ThreadID": thread_id,
                "UserID": userID,
                "UserID Status": "New"
            }
        }]
    }

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_THREAD}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Sending the POST request to Airtable
        response = requests.post(url, headers=headers, json=data_payload)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        data = response.json()
        # On success, parse and return the response
        return {
            "message": "Thread record created successfully.",
            "details": response.json()
        }
    except requests.exceptions.RequestException as e:
        # Return detailed error information in case of failure
        return {
            "error": f"Airtable API request failed: {str(e)}",
            "details": response.text if response else "No response"
        }#

        
@traceable(name="updateThread_DB")
def updateThread_DB(thread_id, userID, userID_status):
    # Payload for creating a record
    data_payload = {
        "performUpsert": {
            "fieldsToMergeOn": ["ThreadID"]
        },
        "records": [{
            "fields": {
                "ThreadID": thread_id,
                # "Name":
                "UserID": userID,
                "UserID Status": userID_status
            }
        }]
    }

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_THREAD}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Sending the POST request to Airtable
        response = requests.patch(url, headers=headers, json=data_payload)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        data = response.json()
        # On success, parse and return the response
        return {
            "message": "Thread record updated successfully.",
            "details": response.json()
        }
    except requests.exceptions.RequestException as e:
        # Return detailed error information in case of failure
        return {
            "error": f"Airtable API request failed: {str(e)}",
            "details": response.text if response else "No response"
        }


@traceable(name="retrieveThread_DB")
def retrieveThread_DB(thread_id):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_THREAD}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        'filterByFormula': f"{{ThreadID}}='{thread_id}'",
        'sort[0][field]': 'Created at',
        'sort[0][direction]': 'desc',
        'maxRecords': 1
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        records = response.json().get('records')
        if records:
            return records[0]  # Return the first (newest) record
        else:
            return "No records found for the given ThreadID."
    else:
        return f"Failed to retrieve record: {response.text}"
        
######THREAD#############CLOSE##########################
########################################################

@traceable(name="authenticateUser")
def authenticateUser(arguments):

    # Extracting login info and sanitizing input
    LogIn = arguments.get("login", "").replace("@", "%40")
    if LogIn == "":
        return {
            "status": 2,
            "message": "Please provide your E-Mail to LogIn. 📨",
            "data": {
                # "userID": "None",
                # "userID_status": "None",
                # "details": {}
            }
        }

    # Constructing the request URL
    url = f"https://api.airtable.com/v0/appgufMUru0W64cNO/Lead?fields%5B%5D=Name&fields%5B%5D=UserID&filterByFormula=FIND(%22{LogIn}%22%2C+LogIn)"

    # Headers including the API key
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Sending the GET request to Airtable
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        data = response.json()

        global login_attempt_counter  # Accessing the global counter
        # Handling response
        if not data.get('records'):
            # Increment the counter when no data is returned

            login_attempt_counter += 1

            if login_attempt_counter >= 3:
                # Reset the counter and return the "User not found" message
                login_attempt_counter = 0
                return {
                    "status": 2,
                    "message": "User not registered.",
                    "data": {
                        # "userID": "None",
                        # "userID_status": "None",
                        # "details": data
                    }
                }
            else:
                return {
                    "status": 2,
                    "message": "User not found. Please try again.",
                    "data": {
                        # "userID": "None",
                        # "userID_status": "None",
                        # "details": data
                    }
                }

        # Reset the counter if data is returned
        login_attempt_counter = 0

        # User is "Registered"
        userID = data['records'][0]['fields']['UserID']
        return {
            "status": "success",
            "message":
            f"Authentication was successful.🗝️ You are now logged in with your account: {LogIn}",
            "data": {
                "userID": userID,
                "userID_status": "Registered",
                "details": data
            }
        }
    except requests.exceptions.RequestException as e:
        # Return detailed error information in case of failure
        return {
            "status": 0,
            "message": f"Airtable API request failed: {str(e)}",
            "data": {
                "userID": "None",
                "userID_status": "None",
                "details": response.text if response else "No response"
            }
        }


@traceable(name="signUp")
def signUp(arguments, userID, userID_status, memory, latest_userMessage,
           description_arguments):
    """
    This function is responsible for handling the sign-up process for users. The function is decorated with `@traceable` to enable tracing with a specific name.

    The function performs the following steps:
    1. Checks if the user is already registered. If so, it advises the user to start a new conversation for creating a new account.
    2. Verifies and parses the input arguments.
    3. Checks if the required fields ("name" and "email") are present when creating a new account.
    4. Authenticates the user by checking if the provided email already exists in the system.
    5. If the email is found, it informs the user that they are already registered.
    6. Prepares a data payload and sends a POST request to create a new user record in Airtable.
    7. Returns appropriate responses based on the success or failure of the operation.

    Returns:
    - dict: A dictionary containing the status, message, and relevant data about the operation.

    Possible statuses:
    - 0: Failure due to Airtable API request failure.
    - 1: Success with the record created successfully.
    - 2: Information missing or user already registered.
    """

    if userID_status == "Registered":
        return {
            "status": 2,
            "message":
            "If you want to create a new account please start a new conversation.",
            "data": {
                "userID_status": userID_status
            }
        }
    arguments_string = verify_input(arguments, memory, latest_userMessage,
                                    description_arguments)
    arguments = json.loads(arguments_string)

    if "arguments_val" in arguments and len(arguments["arguments_val"]) > 0:
        createAccount_str = arguments["arguments_val"][0].get(
            "createAccount", "False")
        # Convert the string value to boolean
        createAccount = createAccount_str.lower() == "true"

    #maybe should check only to have the function exected of no userID exists? otherwise will be updated over updateUserRecord?
    arguments_val = arguments["arguments_val"][0]
    arguments_val = {k.lower(): v for k, v in arguments_val.items()}

    missing_fields = []
    if not arguments_val.get("name"):
        missing_fields.append("Name")
    if not arguments_val.get("email"):
        missing_fields.append("Email")

    if createAccount == True:
        if missing_fields:
            return {
                "status": 2,
                "message":
                f"Missing required information: {', '.join(missing_fields)}",
                "data": {
                    "missing_fields": missing_fields
                }
            }

    # Extracting information from arguments
    name = arguments_val.get("name", "None")
    email = arguments_val.get("email", "None")

    # optional field to be considered for the sign up - another solutiion could be to always call "updateUserInfo" if we have any changes
    # communicationChannel = arguments.get("CommunicationChannel", "None")
    # communicationChannelName = arguments.get("CommunicationChannelName", "None")

    # Authenticate user - re-echeck if provided email is already available in the system
    auth_response = authenticateUser({"email": email})
    if auth_response.get("userID_status") == "Registered":
        return {
            "status": "success",
            "message":
            "Super, I found your E-Mail in our system. Means you are already registered. 😊",
            "data": {
                "userID": auth_response.get("userID"),
                "userID_status": auth_response.get("userID_status"),
                "details": auth_response.get("details")
            }
        }

    # Prepare the data payload for creating a record
    # Check if "" can be provided instead of "None"
    data_payload = {
        "records": [{
            "fields": {
                "Name": name,
                "UserID": userID,
                "Email": arguments_val.get('email', "None"),
                "PhoneNumber": arguments_val.get('phoneNumber', "None"),
                "SocialMedia": arguments_val.get('SocialMedia', "None"),
                "SocialMediaName": arguments_val.get('SocialMediaName',
                                                     "None"),
                # "CommunicationChannel": communicationChannel,
                # "CommunicationChannelName": communicationChannelName
            }
        }]
    }

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_USERINFO}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Sending the POST request to Airtable
        response = requests.post(url, headers=headers, json=data_payload)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        data = response.json()
        userID = data['records'][0]['fields']['UserID']

        if "Email" in missing_fields:
            return {
                "status": 2,
                "message":
                "No record was created. Let's proceed without registering you.",
                "data": {
                    "details": data,
                    "userID":
                    userID  #will this be needed with the new approach? Consider also that authentication is available.. can be derived out ot details
                }
            }

        else:
            # On success, parse and return the response
            return {
                "status": 1,
                "message": "Record created successfully.",
                "data": {
                    "details": data,
                    "userID": userID
                }
            }
    except requests.exceptions.RequestException as e:
        # Return detailed error information in case of failure
        return {
            "status": 0,
            "message": f"Airtable API request failed: {str(e)}",
            "data": {
                "details": response.text if response else "No response",
                "userID": None
            }
        }

###########################################################
###########################################################        
@traceable(name="recordFilter")
def recordFilter(arguments, userID, thread_id):


    response_filter = retrieveFilter(userID)
    if response_filter['status'] == 'success' and response_filter['data']:
        filter_records = response_filter['data'][0]
    else:
        filter_records = None  # or handle the case where there's no data or an error

    create_new_filter = arguments.get("CreateNewFilter", False)

    if isinstance(filter_records, str):
        filter_records = []

    # Handle case for new users with no filters
    if not filter_records:
        latest_filter_record = {}
        current_fields = {}
        create_new_filter = True
    else:
        # The latest filter record is at position 0
        latest_filter_record = filter_records[0]
        current_fields = latest_filter_record['fields']

    if create_new_filter:
        # Get the current highest filter number from the latest filter record and increment by 1
        current_highest_filter_number = current_fields.get("Filter", 0)
        new_filter_number = current_highest_filter_number + 1
        arguments["Filter"] = new_filter_number

        # Initialize with mandatory fields
        updated_fields = {
            "Name": current_fields.get("Name", ""),
            "UserID": current_fields.get("UserID", userID),
            "ThreadID": thread_id,
            "Filter": new_filter_number
        }

        # Add only provided fields
        optional_fields = [
            "Budget", "CommercialType", "PropertyType", "Location",
            "Furnishing", "Size", "Bedrooms", "Bathrooms", "Floor",
            "Balcony Size", "Parking", "Year of Completion", "Amenities",
            "TotalFloors", "SwimmingPools", "Others"
        ]

        for field in optional_fields:
            if field in arguments and arguments[field]:
                updated_fields[field] = arguments[field]
    else:
        # Define all field names exactly as they appear in the 'fields' dictionary
        fields = [
            "Name", "UserID", "ThreadID", "Filter", "Budget", "CommercialType",
            "PropertyType", "Location", "Furnishing", "Size", "Bedrooms",
            "Bathrooms", "Floor", "Balcony Size", "Parking",
            "Year of Completion", "Amenities", "TotalFloors", "SwimmingPools",
            "Others"
        ]
        updated_fields = {}

        for field in fields:
            # Use new value from arguments if available, otherwise use the existing value from filter_record
            if field in arguments and arguments[field] is not None:
                updated_fields[field] = arguments[
                    field]  # Keep the case from the input
            elif field in current_fields:
                updated_fields[field] = current_fields[
                    field]  # Keep the case from the filter_record

        # Ensure ThreadID is set to the passed thread_id
        updated_fields["ThreadID"] = thread_id

    if not any(
            current_fields.get(field, None) != updated_fields.get(field, None)
            for field in updated_fields):
        return {"status": 1, "message": "No updates necessary.", "data": []}

    # Prepare the data for update
    # data_payload = {"fields": updated_fields}
    data_payload = {"records": [{"fields": updated_fields}], "typecast": True}
    print(data_payload)  # Debug: Check what will be sent
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_FILTER}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=data_payload)

    if response.status_code == 200:
        response_data = response.json()
        if 'records' in response_data:
            fields_data = [
                record['fields'] for record in response_data['records']
            ]
        else:
            fields_data = []

        return {
            "status": 1,
            "message": "Filter updated successfully.",
            "data": fields_data
        }

    else:
        return {
            "status": 0,
            "message": f"Failed to update filter: {response.text}",
            "data": []
        }


@traceable(name="retrieveFilter")
def retrieveFilter(userID):
    if not userID:
        return "No userID provided. Please provide a valid userID to fetch the record."

    # Check if userID is already created
    if userID == "None":
        response = createUserID(arguments={}, Name="", Email="")
        user_id = response["userID"]
        userID = user_id
        userID_status = response["userID_status"]

        return {
            "status": 2,
            "message": "No filter found for the given userID.",
            "data": []
        }

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_FILTER}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        'filterByFormula': f"{{UserID}}='{userID}'",
        'sort[0][field]': 'Created at',
        'sort[0][direction]': 'desc',
        'maxRecords': 5
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        records = response.json().get('records', [])
        # Extract only the fields
        fields_list = [record['fields'] for record in records]

        if records:
            return {
                "status": 1,
                "message": "Records retrieved successfully.",
                "data": records
            }
        else:
            return {
                "status": 2,
                "message": "No filter found for the given userID.",
                "data": []
            }
    else:
        return {
            "status": 0,
            "message": f"Failed to retrieve filter: {response.text}",
            "data": []
        }


@traceable(name="checkFilterCompletion")
def checkFilterCompletion(latest_userMessage, memory):
    
    system_instructions_property_filter = f"""
    #Your Role - you are a virtual assistant that checks the user messages and verifiys if the user gave the Feedback that all relevant information for filter for the property search are collected

    #Your Task
    Take the latest user message: {latest_userMessage} 
    and messages in the thread: {memory}

    Understand the messages and the thread and check if the user verified that all relevant Information/requirements are added to the filter for the property search.
    For this call the tool "propertyRequirements_collected" and
    - Map the variable "filter_complete" to True if all information is collected and verified by the user that all requirements are collected. 
    - Map the variable "filter_complete" to False if NOT ALL information is collected OR NOT verified by the user that all requirements are collected.

    For such/similar cases set "filter_complete" = TRUE:
    Asssistant: "Did you provide all relevant information for the property search? 🔎 If yes, I will start to find the best matching property for you."
    User:
    Example 1: "yes, all the requirements are collected..."
    Example 2: "Lets go"
    Example 3: "super excisted for the results"
    Example 4: "googogogogoo..."

    For such/similar cases set "filter_complete" = FALSE:
    Asssistant: "Did you provide all relevant information for the property search? 🔎 If yes, I will start to find the best matching property for you."
    User:
    Example 1: "ahhhh...please also consider that I want three bedrooms and a balcony" 
    Example 2: "yes you are right...I actually want a second bathroom.
    Example 3: "oh yeah....my budget is below the current one...is about 2000000 AED."
    Example 4: "ohhh..."
    """
    tools = [{
        "type": "function",
        "function": {
            "name": "propertyRequirements_collected",
            "description":
            "Shows if it is verified by the user if all requirements are collected for the filter for the property search. True if all information is collected and verified by the user. False if not all the information is collected or not verified by the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_complete": {
                        "type":
                        "boolean",
                        "description":
                        "True if all information is collected and verified by the user. False if not all the information is collected or not verified by the user."
                    }
                },
                "required": ["filter_complete"]
            }
        }
    }]

    completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        tools=tools,
        tool_choice="required",
        messages=[{
            "role": "system",
            "content": system_instructions_property_filter
        }, {
            "role":
            "user",
            "content":
            f"""
            Call the tools as described in the system instructions and check if the user verified that all relevant Information/requirements are added to the filter for the property search.
            """
        }])
    content = completion.choices[0].message.content
    choices = completion.choices
    message = choices[0].message

    # Assuming `message` is an instance of ChatCompletionMessage
    tool_calls = getattr(message, 'tool_calls', None)

    if tool_calls and len(tool_calls) > 0:
        function_call = getattr(tool_calls[0], 'function', None)
        if function_call:
            arguments_string = getattr(function_call, 'arguments', "")
            function_name = getattr(function_call, 'name', "")

            if arguments_string:
                # Convert JSON string to dictionary
                arguments = json.loads(arguments_string)
            else:
                arguments = {}
        else:
            arguments_string = ""
            function_name = ""
            arguments = {}
    else:
        function_call = None
        arguments_string = ""
        function_name = ""
        arguments = {}

    return arguments

###########################################################
###########################################################    
@traceable(name="recommandProperty")
def recommandProperty(arguments, user_id, userID_status, thread_id,
                    latest_userMessage, memory):

    # recordFilter(arguments, user_id, thread_id)
    
    filterCompletionCheck = checkFilterCompletion(latest_userMessage, memory)
    filter_complete = filterCompletionCheck.get('filter_complete')
    if filter_complete is False:
        return {
            "status": 2, #Property search not started. First clarify if every information in the filter is collected.
            "message":
            "Check if all the requirements for the property search filter are collected. After all requirements all collected the property search will be started.",
            "data": {
                "metadata": [],
                "recommandProperty_executed": False,
                "num_props": 0,
                "userID": user_id,
                "userID_status": userID_status
            }
        }

    # Create user filter for property search for not registered users
    userID = user_id
    userID_status = userID_status

    DB_URL = "https://890f1263-7caa-4b89-a363-a566bedddb25.us-east4-0.gcp.cloud.qdrant.io:6333"
    DB_API_KEY = "Y_45vsXURZXlRhXiNjMznItfQ6gZ4FMHLNkRreGL_tNvuTZ7ue9fFw"
    embeddings = OpenAIEmbeddings(api_key="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")
    
    database = PropertySearch(api_key=DB_API_KEY, url=DB_URL, embeddings=embeddings)
    responses = database.getProperties(arguments, user_id)

    similar_props = defaultdict(list)

    if responses:
        for idx, resp in enumerate(responses, 1):
            description_context = f"## Property Description {idx}: {resp.page_content}\n\n"
            similar_props["descriptions"].append(description_context)
            similar_props["metadata"].append(resp.metadata)

        response_json = {
            "status": 1,
            "message": similar_props["descriptions"],
            "data": {
                "metadata": similar_props["metadata"],
                "recommandProperty_executed": True,
                "num_props": len(responses),
                "userID": userID,
                "userID_status": userID_status
            },
            "data_llm": None  # Assuming data_llm needs to be added here, can be set to None or actual data if available
        }

        return response_json  # Return the dictionary object directly
    else:
        response_json = {
            "status": 2,
            "message": ["No property found"],
            "data": {
                "metadata": [{
                    "bathrooms": None,
                    "bedrooms": None,
                    "size": None,
                    "price": None,
                    "images": [],
                    "score": None,
                    "property_id": None,
                    "url": None,
                }],
                "recommandProperty_executed": False,
                "num_props": 0,
                "userID": userID,
                "userID_status": userID_status
            },
            "data_llm": None
        }

        return response_json  # Return the dictionary object directly

###########################################################
###########################################################    
@traceable(name="bookMeeting")
def bookMeeting(thread_id):

    # User wants to book the meeting after properties are shown in the conversation
    f"""
    Actually will build a column to see what properties got shown to the user...if entry exists we can take it for now we have one link
    """

    # User wants to book the meeting - Else path
    # Load the YAML file and access the calendlyLink variable in one step
    with open('client.yaml', 'r') as file:
        clientCalendly_link = yaml.safe_load(file)['calendlyLink']

    #Calendly links for the different positions in the workflow
    calendlyLink_start = f"{clientCalendly_link}utm_medium=chatbot&utm_campaign={thread_id}&utm_term=start"

    # Reference calendly link
    calendlyLink = calendlyLink_start

    return {
    "status": 1,
    "message": "Here is the link to the calendly. 🗓️ Feel free to book.",
    "data": {
        "calendlyLink": calendlyLink
        }
    }

######FEEDBACK#############START##########################
########################################################
@traceable(name="recordUserFeedback")
def recordUserFeedback(arguments, thread_id):
    # Pre-process
    user_feedback = arguments.get("user_feedback")
    # Get Thread DB records
    records_full = retrieveThread_DB(thread_id)

    # Access and update "User Feedback"
    if "User Feedback" in records_full["fields"]:
        records_full["fields"]["User Feedback"].append(user_feedback)
    else:
        records_full["fields"]["User Feedback"] = [user_feedback]

    records = records_full["fields"]
    records.pop('Created at', None)
    print("****************")
    print("========>", records)
    print("****************")
    # Payload for creating a record
    data_payload = {
        "performUpsert": {
            "fieldsToMergeOn": ["ThreadID"]
        },
        "records": [{
            "fields": records
        }],
        "typecast": True
    }

    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME_THREAD}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Sending the POST request to Airtable
        response = requests.patch(url, headers=headers, json=data_payload)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors
        data = response.json()
        # On success, parse and return the response
        return {
            "message": "User Feedback record updated successfully.",
            "details": response.json()
        }
    except requests.exceptions.RequestException as e:
        # Return detailed error information in case of failure
        return {
            "error": f"Airtable API request failed: {str(e)}",
            "details": response.text if response else "No response"
        }
        
###########################################################
###########################################################