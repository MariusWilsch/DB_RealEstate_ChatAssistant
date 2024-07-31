import os, sys, requests

# basic path include
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib")
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib/RepositoryPattern")


# inport the base repository
from lib.user_repository.user_repo import user_repo
from langsmith.run_helpers import traceable

from dotenv import load_dotenv
load_dotenv()

@traceable(name="createUserID")
async def createUserID(user_info: dict):
    try:
        created_user = await user_repo().create(data=user_info)  # Pass the data argument
        return {
            "message": "Record created successfully.",
            "details": created_user,
            "userID": created_user["user_id"],  # Access the created user data correctly
            "userID_status": created_user["status"]
        }
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),  # Use str(e) to get the exception message
        }

# async def createUserID():
#     try:
#         created_user = await user_repo.create()
#         return {
#             "message": "Record created successfully.",
#             "details": created_user,
#             "userID": created_user.user_id,
#             "userID_status": created_user.status
#         }
#     except Exception as e:
#         return {
#             "error": f"supabase API request failed: {str(e)}",
#             "details": e.message,
#             # "code": e.code # can be added if needed for debugging
#         }

@traceable(name="updateUserRecord")
async def updateUserRecord(arguments, userID, thread_id):
    try:
        if not userID:
            return "No userID provided. Please provide a valid userID to update the record."
        retrieved_user = await retrieveUserRecord(userID)
        if not retrieved_user:
            return {
                "status": 2,
                "message": "User record not found.",
                "data": {
                    "details": []
                }
            }
        updated_user = await user_repo.update(userID, arguments)
        return  {
                "status": 1,
                "message": "User information updated successfully.",
                "data": {
                    "details": updated_user
                }
            }
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": e.message,
            # "code": e.code # can be added if needed for debugging
        }

@traceable(name="retrieveUserRecord")
async def retrieveUserRecord(userID):
    if not userID:
        return "No userID provided. Please provide a valid userID to fetch the record."
    try:
        retrieved_user = await user_repo.read(userID)[0]
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": e.message,
            # "code": e.code # can be added if needed for debugging
        }
    return retrieved_user

