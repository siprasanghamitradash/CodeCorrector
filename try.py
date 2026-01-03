import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
from savedapi import GROQ_API_KEY

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)

def get_github_summary_data(url):
    # 1. Standardize the URL
    clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    parts = clean_url.split("/")
    if len(parts) < 3: return None
    
    repo_path = f"{parts[1]}/{parts[2]}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 2. Use the Recursive Tree API to see ALL files
    # We first check 'main' branch, then 'master'
    files = []
    for branch in ["main", "master"]:
        api_url = f"https://api.github.com/repos/{repo_path}/git/trees/{branch}?recursive=1"
        res = requests.get(api_url, headers=headers)
        if res.status_code == 200:
            tree = res.json().get('tree', [])
            # Extract just the paths of the first 100 files (avoiding huge repos)
            files = [item['path'] for item in tree if item['type'] == 'blob'][:100]
            break

    if not files: return None
    return {"files": files, "name": parts[2]}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message", "").strip()
    
    if "github.com" in user_message.lower():
        repo_data = get_github_summary_data(user_message)
        
        if repo_data:
            # THE KEY CHANGE: Very strict instructions for the AI
            prompt = f"""
            Based on this file list from the '{repo_data['name']}' repository, 
            write one simple, clear paragraph (max 4 sentences) explaining 
            what this project is and its main features. 
            Do not use bullet points or a long intro. Just the facts.

            FILE LIST:
            {repo_data['files']}
            """
        else:
            return jsonify({"response": "Repository not found or private."})
    else:
        prompt = user_message

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                # System message sets the "behavior"
                {"role": "system", "content": "You are a concise technical summarizer. Provide single-paragraph responses."},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)