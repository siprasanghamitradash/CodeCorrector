import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
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

def clean_github_url(url):
    print(f"DEBUG: Cleaning URL: {url}")
    url = url.strip().lower()
    url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    parts = [p for p in url.split('/') if p]
    
    if len(parts) >= 3 and "github.com" in parts[0]:
        res = f"{parts[1]}/{parts[2]}"
        print(f"DEBUG: Cleaned Path Result: {res}")
        return res
    print("DEBUG: URL cleaning failed - not a valid GitHub link")
    return None

def get_github_summary_data(repo_path):
    # GitHub API sometimes requires a User-Agent or it returns 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/vnd.github.v3+json',
        'Authorization' : f'token {GithubToken}'
    }
    files = []

    for branch in ["main", "master"]:
        api_url = f"https://api.github.com/repos/{repo_path}/git/trees/{branch}?recursive=1"
        print(f"DEBUG: Attempting GitHub API call to: {api_url}")
        try:
            res = requests.get(api_url, headers=headers, timeout=10)
            print(f"DEBUG: GitHub API Status Code: {res.status_code}")
            
            if res.status_code == 200:
                tree = res.json().get('tree', [])
                files = [item['path'] for item in tree if item['type'] == 'blob'][:150]
                print(f"DEBUG: Successfully found {len(files)} files.")
                break
            elif res.status_code == 403:
                print("DEBUG: Rate limit exceeded or forbidden. Try again later.")
        except Exception as e:
            print(f"DEBUG: API Request Error: {e}")
            continue
    
    return files if files else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    print("\n--- NEW REQUEST RECEIVED ---")
    try:
        data = request.get_json()
        if not data:
            print("DEBUG: No JSON data received")
            return jsonify({"response": "No data received"}), 400
            
        user_message = data.get("message", "").strip()
        print(f"DEBUG: User Message: {user_message}")

        repo_path = clean_github_url(user_message)
        
        if repo_path:
            file_list = get_github_summary_data(repo_path)
            
            if file_list:
                repo_name = repo_path.split('/')[-1]
                prompt = f"""
                Identify what this application is and what it does for a user based on the file list for '{repo_name}'.
                Write one simple paragraph (max 4 sentences). 
                Focus ONLY on purpose and features. No tech talk.

                FILES:
                {file_list}
                """
                print("DEBUG: Prompt generated for AI.")
            else:
                print("DEBUG: GitHub data fetch returned None.")
                return jsonify({"response": "I couldn't access that repository. It might be private or doesn't exist."})
        else:
            print("DEBUG: Treating as regular chat.")
            prompt = user_message

        print("DEBUG: Calling Groq AI...")
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a product analyst. Explain purpose only. No code talk."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_response = completion.choices[0].message.content
        print("DEBUG: AI responded successfully.")
        return jsonify({"response": ai_response})

    except Exception as e:
        print(f"DEBUG CRITICAL ERROR: {str(e)}")
        return jsonify({"response": f"Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)