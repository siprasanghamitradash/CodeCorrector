import os
import requests
try:
    # This works on your local computer
    from savedapi import GROQ_API_KEY, GithubToken
except ImportError:
    # This works on Render (the "hidden" dashboard keys)
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

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

def get_high_value_files(repo_name, file_list):
    """Step 1: Ask AI to pick the 3 most important logic files."""
    prompt = f"From this list of files for the project '{repo_name}', pick the 3 most important files that contain the core logic or main functionality. Ignore configs/images. Return ONLY the paths separated by commas.\nFILES:\n{file_list}"
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a code architect. Respond only with a comma-separated list of file paths."},
                {"role": "user", "content": prompt}
            ]
        )
        picked = completion.choices[0].message.content.strip().split(',')
        return [f.strip() for f in picked]
    except:
        return file_list[:3] # Fallback

def get_file_content(repo_path, file_path):
    """Step 2: Download the actual code from GitHub."""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    # Try 'main' then 'master'
    for branch in ["main", "master"]:
        raw_url = f"https://raw.githubusercontent.com/{repo_path}/{branch}/{file_path}"
        res = requests.get(raw_url, headers=headers)
        if res.status_code == 200:
            return res.text
    return ""