import subprocess
import time
import requests
import os
import signal

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'app'))
UVICORN_CMD = ["uvicorn", "main:app", "--port", "8000"]


def start_server():
    p = subprocess.Popen(UVICORN_CMD, cwd=SRC_DIR)
    time.sleep(2)
    return p


def stop_server(p):
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        p.kill()


if __name__ == '__main__':
    print("Starting FastAPI server...")
    p = start_server()
    try:
        for i in range(10):
            try:
                r = requests.get("http://127.0.0.1:8000/health", timeout=2)
                if r.status_code == 200:
                    print("Health OK")
                    break
            except Exception:
                time.sleep(1)
        else:
            print("Server did not become healthy in time")
            stop_server(p)
            exit(1)

        print("Running benchmark...")
        os.system(f"python tools/benchmark_api.py")
    finally:
        print("Stopping server")
        stop_server(p)
