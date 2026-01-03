import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
from savedapi import GROQ_API_KEY

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)

def get_github_summary_data(url):
    # 1. Standardize and clean the URL
    clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    parts = clean_url.split("/")
    if len(parts) < 3 or parts[0] != "github.com":
        return None
    
    user = parts[1]
    repo = parts[2]
    repo_path = f"{user}/{repo}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 2. Recursive Tree Scan (gets every file in the project)
    files = []
    for branch in ["main", "master"]:
        api_url = f"https://api.github.com/repos/{repo_path}/git/trees/{branch}?recursive=1"
        try:
            res = requests.get(api_url, headers=headers, timeout=5)
            if res.status_code == 200:
                tree = res.json().get('tree', [])
                # Extract first 150 files to keep the AI focused
                files = [item['path'] for item in tree if item['type'] == 'blob'][:150]
                break
        except:
            continue

    if not files:
        return None
        
    return {"files": files, "name": repo}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message", "").strip()
    
    if "github.com" in user_message.lower():
        repo_data = get_github_summary_data(user_message)
        
        if repo_data:
            # The prompt forces the AI to be a "Product Expert"
            prompt = f"""
            Based on the following file list from the project '{repo_data['name']}', 
            identify what this application is and what it does for a user.
            
            Instruction: Write one clear, simple paragraph (max 4 sentences). 
            Do NOT mention programming languages, file extensions, or technical stacks. 
            Focus only on the purpose and the main features from a user's perspective.
            
            FILES:
            {repo_data['files']}
            """
        else:
            return jsonify({"response": "I couldn't find that repository. Please check if it's public."})
    else:
        # Fallback for general questions
        prompt = user_message

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a product analyst. You explain software utility to non-technical users. Never mention code or tech stacks."},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)