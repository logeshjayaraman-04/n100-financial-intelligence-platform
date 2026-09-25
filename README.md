\# N100 Financial Intelligence Platform



A financial intelligence platform for analysing a 100-company Nifty 100-style universe using financial statements, ratios, cash flow metrics, peer analysis, screening, valuation, sector analysis, portfolio analytics, and generated reports.



> \*\*Data-universe note:\*\* The current processed/database universe contains 100 companies. Some Sprint specifications refer to 92 companies; the implementation preserves the actual 100-company universe.



\---



\## 1. Project Overview



The platform provides three main layers:



1\. \*\*Data and analytics layer\*\*

&#x20;  - ETL normalisation and validation

&#x20;  - Financial KPI calculations

&#x20;  - CAGR analysis

&#x20;  - Cash-flow analysis

&#x20;  - Peer comparison

&#x20;  - Valuation

&#x20;  - Clustering and portfolio analytics

&#x20;  - Screener logic

&#x20;  - NLP-derived pros/cons



2\. \*\*REST API\*\*

&#x20;  - FastAPI-based endpoints

&#x20;  - Company data

&#x20;  - Financial statements

&#x20;  - Ratios

&#x20;  - Screener

&#x20;  - Sectors

&#x20;  - Peer analysis

&#x20;  - Valuation

&#x20;  - Portfolio statistics

&#x20;  - Documents

&#x20;  - Health monitoring



3\. \*\*Interactive dashboard\*\*

&#x20;  - Streamlit application

&#x20;  - Company profiles

&#x20;  - Screener

&#x20;  - Peer comparison

&#x20;  - Trend analysis

&#x20;  - Sector analysis

&#x20;  - Capital allocation

&#x20;  - Annual reports



\---



\## 2. Repository Structure



```text

N100 FINANCIAL INTELLIGENCE PLATFORM/

│

├── data/

│   ├── db/

│   │   └── n100.db

│   ├── processed/

│   └── raw/

│

├── docs/

│   ├── N100\_API\_Postman\_Collection.json

│   ├── openapi.json

│   └── analyst\_guide.pdf

│

├── output/

│   └── perf\_notes.md

│

├── reports/

│

├── src/

│   ├── analytics/

│   ├── api/

│   ├── dashboard/

│   ├── etl/

│   ├── nlp/

│   ├── reports/

│   ├── screener/

│   ├── db\_loader.py

│   ├── financial\_engine.py

│   ├── intelligence\_report.py

│   ├── peer\_engine.py

│   └── stock\_engine.py

│

├── tests/

│   ├── api/

│   ├── dq/

│   ├── etl/

│   └── kpi/

│

├── requirements.txt

└── README.md

