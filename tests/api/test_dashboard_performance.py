import time

from src.dashboard.utils.db import (
    get_companies,
    get_pl,
    get_pros_cons,
    get_ratios,
)

TICKERS = [
    "TCS",
    "INFY",
    "RELIANCE",
    "HDFCBANK",
    "SBIN",
]


def measure_company_profile_data_load(ticker):
    start = time.perf_counter()

    companies = get_companies()

    ratios = get_ratios(ticker)

    pl = get_pl(ticker)

    pros_cons = get_pros_cons(ticker)

    elapsed = time.perf_counter() - start

    return {
        "ticker": ticker,
        "elapsed_seconds": round(elapsed, 4),
        "companies_rows": len(companies),
        "ratios_rows": len(ratios),
        "pl_rows": len(pl),
        "pros_cons_rows": len(pros_cons),
    }


def test_company_profile_performance():
    print("\n" + "=" * 70)
    print("DAY 43 — COMPANY PROFILE PERFORMANCE TEST")
    print("=" * 70)

    results = []

    # Clear Streamlit caches so the measurement represents
    # fresh database loading rather than cached results.
    try:
        get_companies.clear()
        get_ratios.clear()
        get_pl.clear()
        get_pros_cons.clear()
    except AttributeError:
        pass

    for ticker in TICKERS:
        result = measure_company_profile_data_load(ticker)
        results.append(result)

        print(
            f"{result['ticker']:10s} "
            f"time={result['elapsed_seconds']:.4f}s "
            f"companies={result['companies_rows']} "
            f"ratios={result['ratios_rows']} "
            f"pl={result['pl_rows']} "
            f"pros_cons={result['pros_cons_rows']}"
        )

    print("-" * 70)

    max_time = max(result["elapsed_seconds"] for result in results)

    average_time = sum(result["elapsed_seconds"] for result in results) / len(results)

    print(f"Average data-load time: {average_time:.4f}s")
    print(f"Maximum data-load time: {max_time:.4f}s")
    print("=" * 70)

    assert len(results) == 5

    for result in results:
        assert result["companies_rows"] == 100
        assert result["ratios_rows"] > 0
        assert result["pl_rows"] > 0

    assert max_time < 3.0
