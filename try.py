import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from savedapi import GROQ_API_KEY

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_message}]
        )
        
        ai_response = completion.choices[0].message.content
        return jsonify({"response": ai_response})

    except Exception as e:
        return jsonify({"response": f"Groq Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)