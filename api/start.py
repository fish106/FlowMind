import subprocess
import signal
import sys
import os
import time

from dotenv import load_dotenv

# Store subprocess PIDs
processes = []

load_dotenv()

def start_process(cmd):
    print(f"Starting: {cmd}")
    process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
    processes.append(process)
    return process

def handle_signal(signum, frame):
    print(f"Received signal {signum}, forwarding to subprocesses...")
    for p in processes:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass  # Process may have already exited

# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

try:
    taskiq = start_process("taskiq worker api.broker:broker --fs-discover --tasks-pattern 'api/jobs/*_jobs.py'")
    uvicorn = start_process("uvicorn api.main:app --host 0.0.0.0 --port 8100 --workers 2")

    print(f"TaskIQ started with PID {taskiq.pid}")
    print(f"Uvicorn started with PID {uvicorn.pid}")

    # Wait for both processes to finish
    while True:
        time.sleep(0.1)
        all_done = all(p.poll() is not None for p in processes)
        if all_done:
            break

finally:
    print("Cleaning up...")
    for p in processes:
        if p.poll() is None:  # Still running
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                p.wait()
            except ProcessLookupError:
                pass

    print("All subprocesses have exited. Exiting.")

# Exit with the exit code of the last process that finished
exit_code = max((p.returncode for p in processes if p.returncode is not None), default=0)
sys.exit(exit_code)
