\# Day 43 — Performance \& Integration Test Notes



\*\*Project:\*\* N100 Financial Intelligence Platform  

\*\*Sprint:\*\* Sprint 6  

\*\*Day:\*\* 43 — Performance \& Integration Testing  

\*\*Test date:\*\* 18 September 2026



\---



\## 1. Performance Testing Summary



Day 43 performance testing covered:



1\. Concurrent FastAPI screener requests.

2\. Company Profile data-loading performance for five representative tickers.

3\. Simultaneous FastAPI and Streamlit service availability.

4\. SQLite index review.



The current processed/database universe contains \*\*100 companies\*\*. The Sprint specification references 92 companies in several places; the measured results in this document use the actual 100-company database without removing companies.



\---



\## 2. FastAPI Concurrent Screener Load Test



\### Test objective



Run 10 concurrent requests against:



`GET /api/v1/screener`



The Day 43 target was for all 10 requests to complete within 10 seconds.



\### Test implementation



Test file:



`tests/api/test\_performance.py`



The test uses Python threading and FastAPI `TestClient` to execute 10 screener requests concurrently.



\### Result



| Metric | Result |

|---|---:|

| Concurrent requests | 10 |

| Successful requests | 10/10 |

| Failed requests | 0 |

| Total wall-clock time | 0.3003 seconds |

| Slowest individual request | 0.2992 seconds |

| Fastest individual request | 0.2307 seconds |

| Target | < 10 seconds |

| Status | \*\*PASS\*\* |



\### Assessment



The measured concurrent screener workload completed substantially below the 10-second Day 43 target.



No API-side performance bottleneck was identified from this load test.



\---



\## 3. Company Profile Performance



\### Test objective



Measure the data-loading path used by the Company Profile screen for five representative companies.



The Day 43 target was less than 3 seconds per company.



\### Test implementation



Test file:



`tests/api/test\_dashboard\_performance.py`



The measurement loads the Company Profile data sources used by the dashboard:



\- Company master data

\- Financial ratios

\- Profit and loss data

\- Pros/cons data



Representative tickers:



\- TCS

\- INFY

\- RELIANCE

\- HDFCBANK

\- SBIN



\### Results



| Ticker | Load time |

|---|---:|

| TCS | 0.0304 seconds |

| INFY | 0.0121 seconds |

| RELIANCE | 0.0133 seconds |

| HDFCBANK | 0.0102 seconds |

| SBIN | 0.0120 seconds |



\*\*Average:\*\* 0.0156 seconds  

\*\*Maximum:\*\* 0.0304 seconds  

\*\*Target:\*\* < 3 seconds  

\*\*Status:\*\* \*\*PASS\*\*



\### Data verification



Each tested ticker returned:



\- 100 company master rows

\- 12 financial-ratio rows

\- 13 P\&L rows

\- Pros/cons data where available



\### Measurement limitation



This test measures the Company Profile \*\*data-loading path\*\*, not complete browser rendering time.



The dashboard uses Streamlit, Plotly, and Streamlit runtime components for the final visual rendering. The automated test directly exercises the underlying database-loading functions outside a full browser session.



Therefore, the measured 0.0304-second maximum should be interpreted as database/data-preparation performance rather than a precise end-user browser page-load measurement.



The test generated Streamlit `No runtime found` / `missing ScriptRunContext` warnings when the cached dashboard functions were executed outside the normal Streamlit runtime. These warnings did not cause test failures.



\---



\## 4. FastAPI + Streamlit End-to-End Availability



\### FastAPI



FastAPI was started on:



`127.0.0.1:8000`



Health endpoint:



`/api/v1/health`



Observed result:



\- HTTP status: \*\*200 OK\*\*

\- API version: \*\*1.0.0\*\*

\- Companies: \*\*100\*\*

\- Financial ratios: \*\*1,148\*\*

\- Profit and loss: \*\*1,262\*\*

\- Balance sheet: \*\*1,225\*\*

\- Cash flow: \*\*1,164\*\*

\- Sectors: \*\*92\*\*

\- Peer groups: \*\*56\*\*



\### Streamlit



Streamlit was started on:



`127.0.0.1:8501`



The dashboard root endpoint returned:



\- HTTP status: \*\*200 OK\*\*

\- Content type: HTML

\- Streamlit application page successfully served



\### Concurrent service check



Both services were running simultaneously on separate ports:



| Service | Port | Result |

|---|---:|---|

| FastAPI | 8000 | \*\*HTTP 200 OK\*\* |

| Streamlit | 8501 | \*\*HTTP 200 OK\*\* |



No port conflict was observed.



This confirms that the FastAPI API service and Streamlit dashboard can be started simultaneously using their configured ports.



\### End-to-end scope note



The HTTP checks verify that both services are available simultaneously and that the dashboard server returns its Streamlit application page.



The Company Profile performance test separately verifies that the dashboard's underlying data-loading functions successfully retrieve company and financial data.



The current dashboard architecture accesses the SQLite database directly for these dashboard data functions; therefore, the HTTP availability check should not be interpreted as proof that every dashboard screen consumes its data through FastAPI.



\---



\## 5. SQLite Index Review



\### Objective



Review the production SQLite database for existing custom indexes and determine whether additional indexes are warranted based on the measured Day 43 workload.



Database:



`data/db/n100.db`



\### Result



The database contains:



\*\*NO\_CUSTOM\_INDEXES\*\*



No additional indexes were added during Day 43.



\### Rationale



The measured performance did not identify a database performance bottleneck requiring immediate index changes:



\- 10 concurrent screener requests completed in 0.3003 seconds.

\- Company Profile data-loading maximum was 0.0304 seconds.



Adding indexes without a demonstrated query-performance problem would unnecessarily modify the database schema.



Index optimization can be revisited if future profiling identifies slow queries as the dataset or workload grows.



\---



\## 6. Performance Bottlenecks



No material bottleneck was identified in the measured Day 43 workloads.



\### Observations



\- Concurrent screener API requests completed well within the 10-second target.

\- Company Profile database/data-loading operations completed well within the 3-second target.

\- FastAPI and Streamlit operated simultaneously without a port conflict.

\- SQLite contains no custom indexes, but current measured performance did not justify adding them.

\- Streamlit cache/runtime warnings appeared only because dashboard cache functions were exercised outside a normal Streamlit runtime during automated testing.

\- The FastAPI test suite produced a Starlette/AnyIO deprecation warning related to the test client, but this did not affect test success.



\---



\## 7. Day 43 Test Status



| Test Area | Result |

|---|---|

| 10 concurrent screener requests | \*\*PASS\*\* |

| Screener < 10 seconds | \*\*PASS\*\* |

| Company Profile data path for 5 tickers | \*\*PASS\*\* |

| Company Profile data path < 3 seconds | \*\*PASS\*\* |

| FastAPI health endpoint | \*\*PASS\*\* |

| Streamlit availability | \*\*PASS\*\* |

| FastAPI + Streamlit simultaneous operation | \*\*PASS\*\* |

| SQLite index review | \*\*COMPLETE\*\* |

| Performance bottleneck documentation | \*\*COMPLETE\*\* |



\---



\## 8. Conclusion



Day 43 performance and integration testing was completed against the current 100-company database.



The measured FastAPI concurrent screener workload and Company Profile data-loading workload both passed their specified performance targets.



FastAPI and Streamlit were also verified running simultaneously on ports 8000 and 8501 without a port conflict.



No SQLite indexes were added because the measured workloads did not demonstrate a performance requirement for additional indexes.



The main measurement limitation is that the automated Company Profile test measures the dashboard data-loading path rather than complete browser-render time.

