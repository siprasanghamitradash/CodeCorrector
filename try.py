import os
from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv,find_dotenv
# env_file = find_dotenv()
# print(f"--- DEBUG INFO ---")
# print(f"Looking for .env at: {os.path.abspath('savedapi.env')}")

# # Load it
# load_status = load_dotenv(env_file)
# print(f"Did .env load successfully? {load_status}")

# # Check the key
# api_key = os.getenv("GEMINI_API_KEY")
# if api_key:
#     print(f"Key found! Starts with: {api_key[:4]}...")
# else:
#     print("Key NOT found in environment.")
# print(f"------------------")
# client = genai.Client(api_key=api_key)

# TEMPORARY TEST ONLY
client = genai.Client(api_key="AIzaSyChBA1Td1T_X7Wwi7FZgXoD7qkDCmyyspU")
app = Flask(__name__)

# Initialize Gemini Client
# Make sure to set GEMINI_API_KEY in a .env file
# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat_session = client.chats.create(model="gemini-2.0-flash")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get("message")
        
        # DEBUG: Print to terminal to see if message arrived
        print(f"User sent: {user_message}") 

        # Call Gemini
        response = chat_session.send_message(user_message)
        
        return jsonify({"response": response.text})

    except Exception as e:
        # This will print the EXACT error to your terminal
        print(f"ERROR OCCURRED: {e}") 
        return jsonify({"response": f"System Error: {str(e)}"}), 500
if __name__ == '__main__':
    app.run(debug=True)