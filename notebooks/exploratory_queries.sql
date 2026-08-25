-- N100 Financial Intelligence Platform
-- Sprint 1 - Day 7
-- Exploratory SQL Queries


-- Q1. Total number of companies
SELECT COUNT(*) AS total_companies
FROM companies;


-- Q2. Companies by sector
SELECT
    broad_sector,
    COUNT(*) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;


-- Q3. Companies with the latest available P&L year
SELECT
    company_id,
    MAX(year) AS latest_year
FROM profitandloss
GROUP BY company_id
ORDER BY company_id;


-- Q4. Revenue and net profit for 2024
SELECT
    company_id,
    sales,
    net_profit,
    eps
FROM profitandloss
WHERE year = 'Mar 2024'
ORDER BY sales DESC;


-- Q5. Companies with highest ROE
SELECT
    company_id,
    return_on_equity_pct
FROM financial_ratios
WHERE return_on_equity_pct IS NOT NULL
ORDER BY return_on_equity_pct DESC
LIMIT 10;


-- Q6. Companies with highest market capitalization
SELECT
    company_id,
    year,
    market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;


-- Q7. Latest stock price for each company
SELECT
    company_id,
    MAX(date) AS latest_date
FROM stock_prices
GROUP BY company_id
ORDER BY company_id;


-- Q8. Companies with positive net profit
SELECT
    company_id,
    year,
    net_profit
FROM profitandloss
WHERE net_profit > 0
ORDER BY net_profit DESC
LIMIT 20;


-- Q9. Companies with dividend payout above 50%
SELECT
    company_id,
    year,
    dividend_payout
FROM profitandloss
WHERE dividend_payout > 50
ORDER BY dividend_payout DESC;


-- Q10. Financial-data coverage by company
SELECT
    c.id AS company_id,
    c.company_name,
    COUNT(DISTINCT p.year) AS pnl_years,
    COUNT(DISTINCT b.year) AS balance_sheet_years,
    COUNT(DISTINCT cf.year) AS cashflow_years
FROM companies c
LEFT JOIN profitandloss p
    ON c.id = p.company_id
LEFT JOIN balancesheet b
    ON c.id = b.company_id
LEFT JOIN cashflow cf
    ON c.id = cf.company_id
GROUP BY c.id, c.company_name
ORDER BY pnl_years DESC;