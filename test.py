from flask import Flask, request, jsonify
from dotenv import load_dotenv, find_dotenv
import functions, new_functions
load_dotenv()

app = Flask(__name__)

## user functions
@app.route('/createUser', methods=['POST'])
async def createUser():
    try:
        user_info = request.get_json()
        userID = await new_functions.createUserID(user_info={'name': user_info['name']})
        return userID
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }


@app.route('/retrieveUser/<uuid:user_id>', methods=['GET'])
def retrieveUser(user_id: str):
    if not user_id:
        return "No userID provided. Please provide a valid userID to fetch the record."
    try:

        retrievedUser =  new_functions.retrieveUserRecord(user_id)
        return retrievedUser
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }

@app.route('/updateUser/<uuid:user_id>', methods=['PUT'])
def updateUser(user_id):
    update_data = request.get_json()
    try:
        user_info =  new_functions.updateUserRecord(update_data, user_id)
        return user_info
    except Exception as e:
        return {
            "error": f"supabase API request failed: {str(e)}",
            "details": str(e),
            # "code": e.code # can be added if needed for debugging
        }





######################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)