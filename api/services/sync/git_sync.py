import os
import subprocess


def clone_or_pull(repo_url, target_dir):
    if os.path.isdir(os.path.join(target_dir, ".git")):
        subprocess.run(["git", "pull"], cwd=target_dir, check=True, capture_output=True)
    else:
        os.makedirs(os.path.dirname(target_dir), exist_ok=True)
        subprocess.run(["git", "clone", repo_url, target_dir], check=True, capture_output=True)
