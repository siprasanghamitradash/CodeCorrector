
import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
from savedapi import GROQ_API_KEY

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)

def get_github_summary_data(url):
    parts = url.rstrip('/').split('/')
    if len(parts) < 2:
        return None
    
    user = parts[-2]
    repo = parts[-1]
    repo_path = f"{user}/{repo}"
    
    # Try to find a README first
    for filename in ["README.md", "README.txt", "readme.md"]:
        raw_url = f"https://raw.githubusercontent.com/{repo_path}/main/{filename}"
        response = requests.get(raw_url)
        if response.status_code == 200:
            return f"README Content:\n{response.text[:2000]}"

    # FALLBACK: If no README, get the list of files in the repo
    # We use the public GitHub API for this
    api_url = f"https://api.github.com/repos/{repo_path}/contents/"
    api_res = requests.get(api_url)
    
    if api_res.status_code == 200:
        files = api_res.json()
        file_names = [f['name'] for f in files]
        return f"This repo has no README. Here is the file list: {', '.join(file_names)}"
    
    return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message", "").strip()
    
    # CHECK: Is this a GitHub link?
    if "github.com" in user_message.lower():
        repo_content = get_github_summary_data(user_message)
        
        if not repo_content:
            return jsonify({"response": "I couldn't find that repository or its README. Please check if the URL is correct and public."})
        
        # Craft a special prompt for the AI to summarize
        prompt = f"Here is the README content of a GitHub repository: \n\n{repo_content}\n\n Please provide a short, 3-sentence summary of what this project does."
    else:
        prompt = user_message

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)