\# Sprint 2 Retrospective — Financial Ratio Engine



\## Sprint

Sprint 2 — Epic 02: Financial Ratio Engine



\## Sprint Period

Day 08–14



\## Sprint Goal



Implement and validate the financial ratio engine, including profitability,

leverage, efficiency, CAGR, cash-flow KPIs, capital allocation patterns,

financial-sector handling, and edge-case logging.



\---



\## 1. Sprint Outcome



Sprint 2 engineering implementation is complete.



The financial ratio engine successfully populated the SQLite

`financial\_ratios` table with 1,148 company-year rows.



The complete automated test suite passes with zero failures.



\### Validation Results



\- Financial ratio rows: 1,148

\- Required KPI columns: populated

\- Null-only KPI columns: 0

\- ETL tests: 48 passed

\- Full test suite: 102 passed

\- Foreign-key errors: 0

\- Screener unique companies: 40

\- Git working tree: clean

\- GitHub main branch: synchronized



\---



\## 2. Formula Decisions



\### Profitability



Net Profit Margin:



&#x20;   Net Profit / Sales × 100



Operating Profit Margin:



&#x20;   Operating Profit / Sales × 100



ROE:



&#x20;   Net Profit / (Equity Capital + Reserves) × 100



ROCE:



&#x20;   EBIT / (Equity Capital + Reserves + Borrowings) × 100



ROA:



&#x20;   Net Profit / Total Assets × 100



Zero or invalid denominators return None where specified by the

ratio-engine rules.



\---



\## 3. Leverage and Efficiency



Debt-to-Equity:



&#x20;   Borrowings / (Equity Capital + Reserves)



Debt-free companies return 0 for D/E.



High-leverage warnings are suppressed for Financials because high

leverage is structurally normal for that sector.



Interest Coverage Ratio:



&#x20;   (Operating Profit + Other Income) / Interest



When interest is zero, ICR returns None and the display label is

"Debt Free".



Interest coverage warning threshold:



&#x20;   ICR < 1.5



Net Debt:



&#x20;   Borrowings - Investments



Asset Turnover:



&#x20;   Sales / Total Assets



\---



\## 4. CAGR Edge Cases



The CAGR engine handles:



\- Positive to Positive

\- Positive to Negative — DECLINE\_TO\_LOSS

\- Negative to Positive — TURNAROUND

\- Negative to Negative — BOTH\_NEGATIVE

\- Zero Base — ZERO\_BASE

\- Insufficient historical data — INSUFFICIENT



CAGR values are not forced when the mathematical or data conditions

make the calculation invalid.



\---



\## 5. Cash Flow and Capital Allocation



Free Cash Flow:



&#x20;   Operating Activity + Investing Activity



Negative FCF is allowed.



Cash-flow KPIs and capital allocation classifications were generated.



The capital allocation output is stored in:



&#x20;   output/capital\_allocation.csv



The ratio edge-case output is stored in:



&#x20;   output/ratio\_edge\_cases.log



\---



\## 6. Financials Sector Handling



Financial companies are excluded from the standard high-leverage warning

because high leverage is structurally normal for banks, NBFCs and insurers.



The financial-sector company universe was checked during Day 13.



\---



\## 7. Edge Cases and Source Data



Computed ratio-engine values are retained for analytics when source

pre-computed ratio values materially differ.



Source anomalies are documented in:



&#x20;   output/ratio\_edge\_cases.log



The log records the affected company/year, metric, calculated value,

source value, difference, category and explanation.



Source-data anomalies are not silently used to overwrite the ratio-engine

calculation.



\---



\## 8. Day 12 Manual Spot Check



The final database values retrieved for three companies were:



| Company | Year | ROE % | Revenue CAGR 5Y % |

|---|---|---:|---:|

| ABB | Mar 2024 | 32.468235 | 9.716101 |

| TCS | Mar 2024 | 50.944314 | 10.463615 |

| RELIANCE | Mar 2024 | 9.958651 | 9.606097 |



These values were retrieved from the populated `financial\_ratios` table.



\---



\## 9. Day 14 Screener



Screener condition:



&#x20;   ROE > 15%

&#x20;   AND

&#x20;   D/E < 1



Result:



&#x20;   40 unique companies



The required range was 15–50 companies.



Result: PASS.



\---



\## 10. Automated Testing



ETL test suite:



&#x20;   48 passed



Full test suite:



&#x20;   102 passed



Failures:



&#x20;   0



\---



\## 11. Sprint 1 Dataset Scope Note



The original Sprint 1 specification targeted 92 companies.



The actual loaded source dataset contains 100 companies.



The current database therefore contains:



&#x20;   companies = 100



Foreign-key validation:



&#x20;   0 errors



The available source dataset was retained rather than artificially

removing companies solely to force the specified count.



This scope difference should be noted during project review.



\---



\## 12. Lessons Learned



1\. Source financial data can contain inconsistent pre-computed ratios.

2\. Ratio calculations should use clearly defined formulas for analytics.

3\. Financial-sector leverage requires sector-specific interpretation.

4\. CAGR calculations require explicit treatment of negative and zero bases.

5\. Merge keys must be unique at the company-year level to prevent duplicate

&#x20;  financial-ratio rows.

6\. Automated tests and database validation are essential before sprint

&#x20;  completion.

7\. Source anomalies should be logged rather than silently modified.



\---



\## 13. Sprint 2 Final Status



Engineering implementation:



&#x20;   COMPLETE



Automated validation:



&#x20;   COMPLETE



Database population:



&#x20;   COMPLETE



Documentation:



&#x20;   COMPLETE



Remaining formal activity:



&#x20;   Team-lead review and sign-off



\---



\## 14. Sign-Off



Team Lead:



Name: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



Signature: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



Date: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



Sprint 2 Status:



\[ ] Approved



\[ ] Changes Required

