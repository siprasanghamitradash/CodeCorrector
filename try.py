
from flask import Flask, render_template, request, jsonify
from groq import Groq
from savedapi import GROQ_API_KEY

app = Flask(__name__) #creates a webapp named app
client = Groq(api_key=GROQ_API_KEY) #connects the api key to groq client

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mess', methods=['POST']) #waits for the website to send a 'message' or anything
def chat():
    user_message = request.json.get("message") #gets the message sent by the user
    try:
        #asking ai for reply
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_message}] #user for human assistant for ai and system for setting rules
        )  
        
        ai_response = completion.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({"response": f"Groq Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True) #runs the webapp in debug mode means the page will restart if you change code