import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Skip the .env loading and hardcode the key directly
# Replace 'gsk_...' with your actual key from Groq Cloud
client = Groq(api_key="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")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    
    try:
        # We use 'llama-3.3-70b-versatile' - it's very smart for code
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