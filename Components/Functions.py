import os
import requests

# Try to get the token for local or cloud use
try:
    from savedapi import GithubToken
except ImportError:
    GithubToken = os.environ.get("GithubToken")
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


# ... keep clean_github_url and get_github_summary_data as they are ...

def get_high_value_files(repo_name, file_list, client):
    # Shield 1: Strict extension filtering
    allowed_extensions = ('.py', '.js', '.html', '.css', '.java', '.cpp', '.ts', '.txt', '.php', '.go', '.rb')
    filtered_list = [f for f in file_list if f.lower().endswith(allowed_extensions)]

    # If the list is empty after filtering, just return an empty list to avoid errors
    if not filtered_list:
        return []

    prompt = f"""
    From this list of SOURCE CODE files for '{repo_name}', pick the 3 most important files that contain the main logic.
    Do NOT pick images, icons, or config files.
    Return ONLY the paths separated by commas.
    
    FILES: {filtered_list}
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a code architect. Respond ONLY with file paths."},
                {"role": "user", "content": prompt}
            ]
        )
        picked = completion.choices[0].message.content.strip().split(',')
        return [f.strip() for f in picked]
    except:
        return filtered_list[:3]

def get_file_content(repo_path, file_path):
    """Step 2: Download the actual code from GitHub with binary safety."""
    # Shield 2: Never even try to download known binary formats
    ignored = ('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.exe')
    if file_path.lower().endswith(ignored):
        return "[Binary file ignored]"

    headers = {'Authorization': f'token {GithubToken}'}
    for branch in ["main", "master"]:
        raw_url = f"https://raw.githubusercontent.com/{repo_path}/{branch}/{file_path}"
        try:
            res = requests.get(raw_url, headers=headers, timeout=5)
            if res.status_code == 200:
                # Basic check: if the first few bytes look like binary junk, skip it
                if b'\x00' in res.content[:100]:
                    return "[Binary data detected and skipped]"
                return res.text
        except:
            continue
    return ""