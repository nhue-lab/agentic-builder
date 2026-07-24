import os
import sys
import shutil
import subprocess

def copy_recursive(src: str, dest: str):
    ignore_items = {
        "node_modules", "dist", ".git", ".venv", "__pycache__", 
        "package.json", "package-lock.json", "tsconfig.json"
    }
    os.makedirs(dest, exist_ok=True)
    
    for item in os.listdir(src):
        if item in ignore_items or item.endswith(".ts") or item.endswith(".js"):
            continue
            
        src_path = os.path.join(src, item)
        dest_path = os.path.join(dest, item)
        
        if os.path.isdir(src_path):
            copy_recursive(src_path, dest_path)
        else:
            shutil.copy2(src_path, dest_path)

def github_onboarding(target_dir: str):
    print("\n=== GitHub Onboarding ===")
    # Use input with a default or check if running in non-interactive environment (e.g. tests)
    # If stdin is not a TTY or in test, we skip
    if not sys.stdin.isatty():
        print("[GitHub Setup] Non-interactive session, skipping.")
        return

    choice = input("Voulez-vous connecter ce nouveau projet à un dépôt GitHub distant ? (y/n) [n]: ").strip().lower()
    if choice != "y":
        print("[GitHub Setup] Skipped.")
        return

    # Check git configuration
    try:
        git_check = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if git_check.returncode != 0:
            print("[GitHub Setup] Warning: git is not installed or not in PATH. Skipping.")
            return

        email_check = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True)
        if not email_check.stdout.strip():
            print("[GitHub Setup] Warning: git user.email is not configured. Skipping.")
            return
    except Exception as e:
        print(f"[GitHub Setup] Warning: Error checking git: {e}. Skipping.")
        return

    repo_url = input("Entrez l'URL de votre dépôt GitHub (ex: https://github.com/username/repo.git): ").strip()
    if not repo_url:
        print("[GitHub Setup] No URL provided. Skipped.")
        return

    print(f"[GitHub Setup] Initializing git repository and connecting to {repo_url}...")
    try:
        subprocess.run(["git", "init"], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "chore: initial commit from agentic-builder template"], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=target_dir, check=True, capture_output=True)
        print("[GitHub Setup] Pushing initial commit to main branch...")
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=target_dir, check=True, capture_output=True)
        print("[GitHub Setup] Successful connection and push to GitHub.")
    except Exception as e:
        error_msg = str(e)
        if isinstance(e, subprocess.CalledProcessError):
            error_msg = e.stderr.decode() if e.stderr else str(e)
        print(f"[GitHub Setup] Warning: Push to GitHub failed: {error_msg}")
        print("[GitHub Setup] Le projet local a été configuré, mais le push initial a échoué. Vous pourrez pousser manuellement plus tard.")

def main():
    if len(sys.argv) < 2:
        print("Error: Target directory not specified.")
        print("Usage: python scripts/create_project.py <target_directory>")
        sys.exit(1)
        
    target_dir = os.path.abspath(sys.argv[1])
    source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    if source_dir == target_dir:
        print("Error: Target directory cannot be the same as template directory.")
        sys.exit(1)
        
    print(f"\n=== Creating Project from Template ===")
    print(f"Source: {source_dir}")
    print(f"Destination: {target_dir}\n")
    
    try:
        # Copy template structures
        copy_recursive(source_dir, target_dir)
        print("[Creator] Files copied successfully.")
        
        # Clean defaults for the target session state
        state_dir = os.path.join(target_dir, ".agent")
        os.makedirs(state_dir, exist_ok=True)
        
        state_file = os.path.join(state_dir, "state.json")
        with open(state_file, "w", encoding="utf-8") as f:
            f.write('{"session_id": "initial", "status": "IDLE"}')
            
        # Create virtual env in target
        venv_path = os.path.join(target_dir, ".venv")
        print(f"[Creator] Creating virtual environment at {venv_path}...")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        
        # Install packages in virtual env
        print("[Creator] Installing dependencies...")
        pip_exe = os.path.join(venv_path, "Scripts", "pip") if os.name == "nt" else os.path.join(venv_path, "bin", "pip")
        subprocess.run([pip_exe, "install", "-e", target_dir], check=True)
        
        # Connect to GitHub
        github_onboarding(target_dir)
        
        print(f"\n[SUCCESS] Successfully initialized project at: {target_dir}")
        print("To get started, activate the virtual environment and run:")
        print(f"  cd {target_dir}")
        print("  python src/main.py \"your prompt here\"")
        
    except Exception as e:
        print(f"[Creator] Failed to initialize project: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
