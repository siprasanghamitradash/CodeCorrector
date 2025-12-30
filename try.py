
import requests
from flask import Flask, render_template, request, jsonify
from groq import Groq
from savedapi import GROQ_API_KEY

app = Flask(__name__)
client = Groq(api_key=GROQ_API_KEY)
import requests # Make sure this is at the top!

def get_github_summary_data(url):
    # 1. Standardize the URL
    clean_url = url.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    parts = clean_url.split("/")
    
    if len(parts) < 3 or parts[0] != "github.com":
        return None
    
    user = parts[1]
    repo = parts[2]
    repo_path = f"{user}/{repo}"
    
    # Define headers so GitHub doesn't block the script
    headers = {'User-Agent': 'Mozilla/5.0'}
    repo_data = {'dependencies': {}, 'description': "No description", 'files': []}
    
    # 1. Fetch package.json (Try main branch, then master)
    pkg_found = False
    for branch in ["main", "master"]:
        pkg_url = f"https://raw.githubusercontent.com/{repo_path}/{branch}/package.json"
        try:
            pkg_res = requests.get(pkg_url, headers=headers, timeout=5)
            if pkg_res.status_code == 200:
                data = pkg_res.json()
                repo_data['dependencies'] = data.get('dependencies', {})
                repo_data['description'] = data.get('description', "No description")
                pkg_found = True
                break
        except:
            continue

    # 2. Fetch the File List (The Skeleton)
    api_url = f"https://api.github.com/repos/{repo_path}/contents/"
    try:
        api_res = requests.get(api_url, headers=headers, timeout=5)
        if api_res.status_code == 200:
            repo_data['files'] = [f['name'] for f in api_res.json()]
    except Exception as e:
        print(f"API Error: {e}")

    # 3. Handle Empty Results
    # If we found no files AND no package.json, the repo might be private/wrong
    if not repo_data['files'] and not pkg_found:
        return None

    return repo_data

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message", "").strip()
    
    if "github.com" in user_message.lower():
        repo_content = get_github_summary_data(user_message)
        
        if repo_content:
            # We extract the specific parts from the dictionary here
            file_list = repo_content.get('files', [])
            dependencies = list(repo_content.get('dependencies', {}).keys())
            description = repo_content.get('description', "No description")

            prompt = f"""
            Analyze this project based on these details:
            - Files: {file_list}
            - Key Tech/Libraries: {dependencies}
            - Package Description: {description}
            
            Tell me exactly what this app DOES. 
            Look at the libraries (Key Tech) and file names to guess the features.
            """
        else:
            return jsonify({"response": "I couldn't find that repository. Is it public?"})
    else:
        prompt = user_message

    # ... rest of your try/except block stays the same

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