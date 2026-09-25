import threading
import time

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

RESULTS = []
LOCK = threading.Lock()


def run_screener_call(call_number):
    start = time.perf_counter()

    try:
        response = client.get("/api/v1/screener")

        elapsed = time.perf_counter() - start

        with LOCK:
            RESULTS.append(
                {
                    "call": call_number,
                    "status_code": response.status_code,
                    "elapsed_seconds": round(elapsed, 4),
                    "success": response.status_code == 200,
                }
            )

    except Exception as exc:
        elapsed = time.perf_counter() - start

        with LOCK:
            RESULTS.append(
                {
                    "call": call_number,
                    "status_code": None,
                    "elapsed_seconds": round(elapsed, 4),
                    "success": False,
                    "error": str(exc),
                }
            )


def test_10_concurrent_screener_calls():
    RESULTS.clear()

    threads = []

    overall_start = time.perf_counter()

    for call_number in range(1, 11):
        thread = threading.Thread(
            target=run_screener_call,
            args=(call_number,),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    overall_elapsed = time.perf_counter() - overall_start

    assert len(RESULTS) == 10

    RESULTS.sort(key=lambda row: row["call"])

    print("\n" + "=" * 60)
    print("DAY 43 — CONCURRENT SCREENER LOAD TEST")
    print("=" * 60)

    for result in RESULTS:
        print(
            f"Call {result['call']:02d}: "
            f"status={result['status_code']} "
            f"time={result['elapsed_seconds']:.4f}s "
            f"success={result['success']}"
        )

    print("-" * 60)
    print(f"Total wall-clock time: {overall_elapsed:.4f}s")
    print(f"Successful calls: {sum(r['success'] for r in RESULTS)}/10")
    print("=" * 60)

    assert all(result["success"] for result in RESULTS)
    assert overall_elapsed < 10.0
