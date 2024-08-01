from flask import Flask, request, jsonify
from dotenv import load_dotenv, find_dotenv
import functions, new_functions
# from rich import traceback as rich_traceback

load_dotenv()


app = Flask(__name__)


## user functions
@app.route("/createUser", methods=["POST"])
def createUser():
    try:
        user_info = request.get_json()
        userID = new_functions.createUserID(user_info={"name": user_info["name"]})
        return userID
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@app.route("/retrieveUser/<uuid:user_id>", methods=["GET"])
def retrieveUser(user_id: str):
    if not user_id:
        return "No userID provided. Please provide a valid userID to fetch the record."
    try:
        retrievedUser = new_functions.retrieveUserRecord(user_id)
        return retrievedUser
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@app.route("/updateUser/<uuid:user_id>", methods=["PUT"])
def updateUser(user_id):
    if not user_id:
        return "No userID provided. Please provide a valid userID to update the record."
    update_data = request.get_json()
    try:
        user_info = new_functions.updateUserRecord(update_data, user_id)
        return user_info
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


######################################

#### thread functions


@app.route("/createThread", methods=["POST"])
def createThread():
    try:
        thread_info = request.get_json()
        threadID = new_functions.createThread_DB(
            thread_id=thread_info["thread_id"], user_id=thread_info["user_id"]
        )
        return threadID
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@app.route("/retrieveThread/<string:thread_id>", methods=["GET"])
def retrieveThread(thread_id: str):
    if not thread_id:
        return (
            "No threadID provided. Please provide a valid threadID to fetch the record."
        )
    try:
        retrievedThread = new_functions.retrieveThreadRecord(thread_id)
        return retrievedThread
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@app.route("/updateThread/<string:thread_id>", methods=["PUT"])
def updateThread(thread_id):
    if not thread_id:
        return "No threadID provided. Please provide a valid threadID to update the record."
    update_data = request.get_json()
    try:
        thread_info = new_functions.updateThreadRecord(update_data, thread_id)
        return thread_info
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


###########################################################

##### filter functions

@app.route("/createFilter", methods=["POST"])
def createFilter():
    try:
        filter_info = request.get_json()
        filterID = new_functions.recordFilter(
            filter_object=filter_info, thread_id=filter_info["thread_id"], user_id=filter_info["user_id"]
        )
        return filterID
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }

@app.route("/retrieveFilter/<string:user_id>", methods=["GET"])
def retrieveFilter(user_id: str):
    if not user_id:
        return (
            "No filterID provided. Please provide a valid filterID to fetch the record."
        )
    try:
        retrievedFilter = new_functions.retrieveFilter(user_id=user_id)
        return retrievedFilter
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }

@app.route("/updateFilter/<string:filter_id>", methods=["PUT"])
def updateFilter(filter_id):
    if not filter_id:
        return "No filterID provided. Please provide a valid filterID to update the record."
    update_data = request.get_json()
    try:
        filter_info = new_functions.updateFilterRecord(update_data, filter_id)
        return filter_info
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }



@app.route("/recordUserFeedback/<string:thread_id>", methods=["PUT"])
def recordUserFeedback(thread_id):
    try:
        user_feedback_info = request.get_json()
        user_feedback = new_functions.recordUserFeedback(arguments=user_feedback_info, thread_id=thread_id)
        return user_feedback
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
