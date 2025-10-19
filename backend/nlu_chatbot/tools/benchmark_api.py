import time
import requests
import statistics
from tqdm import tqdm

BACKEND = "http://127.0.0.1:8000"

# Vessels to test
VESSELS = ["ABIGAIL", "+BRAVA"]


def run_once_by_name(vessel_name, timeout=120):
    t0 = time.time()
    r = requests.get(f"{BACKEND}/admin/describe_vessel", params={"vessel": vessel_name, "limit": 100}, timeout=timeout)
    t1 = time.time()
    return t1 - t0, r.status_code, r.text[:500]


if __name__ == "__main__":
    for vessel in VESSELS:
        times = []
        print(f"Benchmarking vessel: {vessel}")
        for i in tqdm(range(3)):
            try:
                delta, code, snippet = run_once_by_name(vessel)
                print(f"  Run {i+1}: {delta:.3f}s status={code}")
                times.append(delta)
            except Exception as e:
                print(f"  Run {i+1} failed: {e}")
        if times:
            print(f"  --- stats for {vessel} ---")
            print(f"  min {min(times):.3f}s, max {max(times):.3f}s, mean {statistics.mean(times):.3f}s")
