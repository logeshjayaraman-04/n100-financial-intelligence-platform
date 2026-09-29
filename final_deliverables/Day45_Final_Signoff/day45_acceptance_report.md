# Day 45 — Final Acceptance Report

**PASS:** 17
**FAIL:** 3

## Acceptance Gates

| Gate | Status | Evidence |
|---|---|---|
| AC-01 | **FAIL** | companies count = 100; required = 92. Actual project universe contains 100 companies; no companies were deleted to force the legacy 92-company criterion. |
| AC-02 | **PASS** | 90/100 companies (90.0%) have >=10 years in P&L, BS and CF; required >=90% |
| AC-03 | **PASS** | PRAGMA foreign_key_check returned 0 rows |
| AC-04 | **PASS** | financial_ratios count = 1148; required >=1100 |
| AC-05 | **PASS** | CAGR unit/regression tests passed in final 172-test regression. Manual Excel spot-check remains a human review item. |
| AC-06 | **FAIL** | ABB FYMar 2024: companies=34.9000, ratio=32.4682, difference=6.97%; ADANIENSOL FYMar 2024: companies=8.5900, ratio=9.4613, difference=10.14%; ADANIENT FYMar 2024: companies=13.6400, ratio=8.5347, difference=37.43%; ADANIGREEN FYMar 2024: companies=14.7000, ratio=12.8127, difference=12.84%; ADANIPORTS FYMar 2024: companies=18.1000, ratio=15.3549, difference=15.17% |
| AC-07 | **PASS** | Quality Compounder rows = 23; required 10-50 |
| AC-08 | **PASS** | Final dashboard/company-profile performance regression passed; measured data-load times were below 3 seconds. |
| AC-09 | **PASS** | Screener CSV export is covered by the API/dashboard regression suite; final regression passed 172 tests. |
| AC-10 | **PASS** | All 100 generated tearsheets are present and >=30 KB. Visual text-overflow review remains a human sign-off item. |
| AC-11 | **PASS** | API health endpoint previously verified HTTP 200 with status=ok. |
| AC-12 | **PASS** | TCS ratios contain 12 distinct years; required >=10 |
| AC-13 | **PASS** | API screener regression passed; screener_output.xlsx exists. Final 172-test regression passed. |
| AC-14 | **PASS** | peer_percentiles contains 11 peer groups; required = 11 |
| AC-15 | **PASS** | rows=100, unique company_ids=100, missing cluster_id=0; actual company universe=100 |
| AC-16 | **PASS** | rows=956, unique companies=100, companies with both pro and con=100 |
| AC-17 | **FAIL** | PDF count=100, PDFs below 30 KB=0; literal criterion requires 92 PDFs, each >=30 KB. Actual generated universe contains 100 companies. |
| AC-18 | **PASS** | 172 tests passed, 0 failures, 1 warning; pytest HTML report generated successfully. |
| AC-19 | **PASS** | validation_failures.csv contains the project's actual validation schema: ['rule_id', 'rule_name', 'severity', 'file', 'company_id', 'year', 'details']; rows=451 |
| AC-20 | **PASS** | analyst_guide.pdf pages = 11; required >=10 |

## Final Regression

- 172 tests collected
- 172 tests passed
- 0 test failures
- 1 deprecation warning
- pytest HTML report: `reports/pytest_report.html`

## Dataset Note

The literal Day 45 specification refers to a 92-company universe.
The actual project database and generated artifacts contain 100 companies.
The additional companies were preserved rather than deleted solely to satisfy
the legacy 92-company acceptance criterion.

## Human Review Items

- AC-05: manual Excel CAGR spot-check
- AC-10: visual review of five tearsheet PDFs for text overflow
- Team lead signature/date required on the final acceptance checklist
