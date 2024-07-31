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
            "details": e.message,
            # "code": e.code # can be added if needed for debugging
        }

@app.route('/updateUser', methods=['POST'])
async def updateUser():
    userID = functions.createUserID()['userID']
    arguments = {"Name": "Peter"}
    return new_functions.updateUserRecord(arguments, userID)

@app.route('/retrieveUser', methods=['POST'])
async def retrieveUser():
    userID = functions.createUserID()['userID']
    return new_functions.retrieveUserRecord(userID)

######################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)