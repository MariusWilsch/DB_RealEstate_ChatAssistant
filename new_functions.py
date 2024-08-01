import os, sys, requests

# basic path include
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib")
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib/RepositoryPattern")


# inport the base repository
from lib.user_repository.user_repo import user_repo
from lib.thread_repository.thread_repo import threads_repo
from lib.filter_repository.filter_repo import filter_repo
from langsmith.run_helpers import traceable
import traceback
from rich import console
from dotenv import load_dotenv

load_dotenv()

## user functions

# Rich console
console = console.Console()


@traceable(name="createUserID")
def createUserID(user_info: dict):
    try:
        created_user = user_repo().create(data=user_info)  # Pass the data argument
        console.log(created_user)
        return {
            "message": "Record created successfully.",
            "details": created_user,
            "userID": created_user[0][
                "user_id"
            ],  # Access the created user data correctly
            "userID_status": created_user["status"],
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),  # Use str(e) to get the exception message
        }


@traceable(name="updateUserRecord")
def updateUserRecord(arguments, userID, thread_id=None):
    try:
        if not userID:
            return "No userID provided. Please provide a valid userID to update the record."
        retrieved_user = retrieveUserRecord(userID)
        if not retrieved_user:
            return {
                "status": 2,
                "message": "User record not found.",
                "data": {"details": []},
            }
        updated_user = user_repo().update(userID, arguments)
        return {
            "status": 1,
            "message": "User information updated successfully.",
            "data": {"details": updated_user},
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@traceable(name="retrieveUserRecord")
def retrieveUserRecord(userID):
    if not userID:
        return "No userID provided. Please provide a valid userID to fetch the record."
    try:
        retrieved_user = user_repo().read(value=userID, column=None)
        return retrieved_user[0]
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": e.message,
            # "code": e.code # can be added if needed for debugging
        }


######################################


#### filters functions


@traceable(name="createThread_DB")
async def createThread_DB(
    thread_id, user_id
):  # here a dict shoulb be passed instead of two arguments
    # Payload for creating a record
    try:
        if not user_id:
            return "No userID provided. Please provide a valid userID to create a new thread."
        if not thread_id:
            return "No threadID provided. Please provide a valid threadID to create a new thread."

        created_thread = await threads_repo().create(
            data={"user_id": user_id, "thread_id": thread_id}
        )
        return {
            "message": "Thread record created successfully.",
            "details": created_thread,
        }
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@traceable(name="retreiveThreadRecord")
def updateThreadRecord(arguments, threadID):
    try:
        if not threadID:
            return "No threadID provided. Please provide a valid threadID to update the record."
        retrieved_thread = threads_repo().read(value=threadID, column=None)
        if not retrieved_thread:
            return {
                "status": 2,
                "message": "Thread record not found.",
                "data": {"details": []},
            }
        updated_thread = threads_repo().update(threadID, arguments)
        return {
            "status": 1,
            "message": "Thread information updated successfully.",
            "data": {"details": updated_thread},
        }
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@traceable(name="retrieveThreadRecord")
def retrieveThreadRecord(threadID):
    if not threadID:
        return (
            "No threadID provided. Please provide a valid threadID to fetch the record."
        )
    try:
        retrieved_thread = threads_repo().read(value=threadID, column=None)
        return retrieved_thread[0]
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": e.message,
            # "code": e.code # can be added if needed for debugging
        }


############################################################

#################3 filter functions
