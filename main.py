import subprocess

def run_script(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run(["python", script_name], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running {script_name}:\n{result.stderr}")
    else:
        print(f"{script_name} completed successfully.\n")

if __name__ == "__main__":
    run_script("scrape_upwork.py")
    run_script("rate_jobs.py")
    run_script("telegram_alert.py")
