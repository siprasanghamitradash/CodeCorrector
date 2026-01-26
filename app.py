import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
from Components.Functions import *
import os
try:
    # This works on your local computer
    from savedapi import GROQ_API_KEY, GITHUB_TOKEN
except ImportError:
    # This works on Render (the "hidden" dashboard keys)
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    repo_path = clean_github_url(user_message)
    
    if repo_path:
        file_list = get_github_summary_data(repo_path, GITHUB_TOKEN) # Pass token if needed
        if not file_list:
            return jsonify({"response": "Repository not found or private."})

        repo_name = repo_path.split('/')[-1]
        
        # --- NEW LOGIC: Identify and Read core files ---
        important_files = get_high_value_files(repo_name, file_list, client)
        
        audit_data = ""
        for f_path in important_files:
            content = get_file_content(repo_path, f_path, GITHUB_TOKEN)
            audit_data += f"\n--- FILE: {f_path} ---\n{content[:2500]}\n"

        # --- COMBINED PROMPT ---
        prompt = f"""
        Analyze the GitHub repository '{repo_name}'.
        
        1. SUMMARY: Write a 2-sentence non-technical summary of what this app does.
        2. CODE AUDIT: Based on the code samples below, list any bugs, security risks, or clean-code improvements.
        
        CODE SAMPLES:
        {audit_data}
        """
        system_content = "You are a Senior Technical Auditor. Use Markdown. Be concise but critical."
    else:
        prompt = user_message
        system_content = "You are a helpful assistant."

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)