from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

VALID_TICKER = "ABB"
INVALID_TICKER = "ZZZZ_INVALID"


def test_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert data["uptime"] == "running"
    assert "db_row_counts" in data
    assert data["db_row_counts"]["companies"] == 100


def test_list_companies():
    response = client.get("/api/v1/companies")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 100

    first = data[0]

    assert "id" in first
    assert "company_name" in first
    assert "broad_sector" in first
    assert "sub_sector" in first


def test_list_companies_search_filter():
    response = client.get(
        "/api/v1/companies",
        params={"search": "ABB"},
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        "ABB" in str(row["id"]).upper() or "ABB" in str(row["company_name"]).upper()
        for row in data
    )


def test_company_profile():
    response = client.get(f"/api/v1/companies/{VALID_TICKER}")

    assert response.status_code == 200

    data = response.json()

    assert "profile" in data
    assert "sector" in data
    assert "latest_kpis" in data

    assert data["profile"]["id"].upper() == VALID_TICKER


def test_company_profile_invalid_ticker():
    response = client.get(f"/api/v1/companies/{INVALID_TICKER}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"


def test_company_profit_loss():
    response = client.get(f"/api/v1/companies/{VALID_TICKER}/pl")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "history" in data
    assert isinstance(data["history"], list)


def test_company_balance_sheet():
    response = client.get(f"/api/v1/companies/{VALID_TICKER}/bs")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "history" in data
    assert isinstance(data["history"], list)


def test_company_cash_flow():
    response = client.get(f"/api/v1/companies/{VALID_TICKER}/cashflow")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "history" in data
    assert isinstance(data["history"], list)


def test_company_ratios():
    response = client.get(f"/api/v1/companies/{VALID_TICKER}/ratios")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "history" in data
    assert isinstance(data["history"], list)


def test_company_ratios_year_filter():
    response = client.get(
        f"/api/v1/companies/{VALID_TICKER}/ratios",
        params={"year": "2024"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert isinstance(data["history"], list)


def test_company_invalid_year():
    response = client.get(
        f"/api/v1/companies/{VALID_TICKER}/ratios",
        params={"year": "invalid"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Year must use YYYY or YYYY-MM format.")


def test_company_tearsheet():
    response = client.get(f"/api/v1/companies/{VALID_TICKER}/tearsheet")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert len(response.content) > 0


def test_screener():
    response = client.get("/api/v1/screener")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "results" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["results"], list)


def test_screener_quality_filter():
    response = client.get(
        "/api/v1/screener",
        params={"min_quality_score": 0},
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["results"], list)

    for row in data["results"]:
        assert row["composite_quality_score"] >= 0


def test_list_sectors():
    response = client.get("/api/v1/sectors")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "sectors" in data
    assert isinstance(data["sectors"], list)
    assert data["count"] > 0

    first = data["sectors"][0]

    assert "broad_sector" in first
    assert "company_count" in first
    assert "total_index_weight_pct" in first


def test_sector_companies():
    sectors_response = client.get("/api/v1/sectors")

    assert sectors_response.status_code == 200

    sectors = sectors_response.json()["sectors"]

    assert len(sectors) > 0

    sector_name = sectors[0]["broad_sector"]

    response = client.get(f"/api/v1/sectors/{sector_name}/companies")

    assert response.status_code == 200

    data = response.json()

    assert data["sector"] == sector_name
    assert data["count"] > 0
    assert isinstance(data["companies"], list)


def test_invalid_sector():
    response = client.get("/api/v1/sectors/ZZZZ_INVALID_SECTOR/companies")

    assert response.status_code == 404


def test_list_peer_groups():
    response = client.get("/api/v1/peers")

    assert response.status_code == 200

    data = response.json()

    assert "count" in data
    assert "peer_groups" in data
    assert isinstance(data["peer_groups"], list)


def test_company_peers():
    response = client.get(f"/api/v1/peers/{VALID_TICKER}")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "company_name" in data
    assert "peers" in data
    assert isinstance(data["peers"], list)


def test_peer_compare():
    response = client.get(f"/api/v1/peers/{VALID_TICKER}/compare")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "company_name" in data
    assert "comparisons" in data
    assert isinstance(data["comparisons"], list)


def test_invalid_peer_ticker():
    response = client.get(f"/api/v1/peers/{INVALID_TICKER}")

    assert response.status_code == 404


def test_valuation():
    response = client.get(f"/api/v1/valuation/{VALID_TICKER}")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "company_name" in data
    assert "count" in data
    assert "valuation" in data
    assert isinstance(data["valuation"], list)


def test_invalid_valuation_ticker():
    response = client.get(f"/api/v1/valuation/{INVALID_TICKER}")

    assert response.status_code == 404


def test_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 10
    assert "kpis" in data
    assert isinstance(data["kpis"], dict)
    assert data["kpis"]["company_count"] == 100
    assert data["ratio_companies"] == 100


def test_company_documents():
    response = client.get(f"/api/v1/documents/{VALID_TICKER}")

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"].upper() == VALID_TICKER
    assert "company_name" in data
    assert "count" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_invalid_documents_ticker():
    response = client.get(f"/api/v1/documents/{INVALID_TICKER}")

    assert response.status_code == 404
