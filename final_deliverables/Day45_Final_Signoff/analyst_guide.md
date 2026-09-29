\# N100 Financial Intelligence Platform

\## Analyst Guide



\*\*Version:\*\* 1.0  

\*\*Sprint:\*\* Sprint 6  

\*\*Platform status:\*\* Day 43 performance and integration testing completed  

\*\*Current database universe:\*\* 100 companies



\---



\# 1. Purpose of This Guide



The N100 Financial Intelligence Platform is an analytical system for evaluating a broad company universe using historical financial statements, financial ratios, cash-flow indicators, peer comparisons, screening rules, valuation metrics, sector analysis, portfolio analytics, and generated reports.



This guide explains how an analyst can understand and use the platform without needing to inspect the implementation source code.



The platform has three primary interfaces:



1\. Interactive Streamlit dashboard

2\. FastAPI REST API

3\. SQLite-backed analytical data layer



The platform also contains ETL, analytics, reporting, NLP, screening, and quality-control components.



\---



\# 2. Current Data Universe



The current processed and database universe contains \*\*100 companies\*\*.



Several Sprint specifications refer to a 92-company target. The implementation currently preserves the actual 100-company universe rather than removing companies to force the specification count.



This distinction is important when interpreting counts displayed by the dashboard, API, tests, and analytical outputs.



The database also contains sector records for 92 sectors/sector mappings. The company universe and sector-row count therefore should not be assumed to be identical.



\---



\# 3. Platform Architecture



The platform can be understood as a layered pipeline.



\## 3.1 Source and Processed Data



The platform maintains raw and processed financial datasets.



The processed data includes information corresponding to:



\- Companies

\- Financial statements

\- Financial ratios

\- Market capitalisation

\- Stock prices

\- Peer groups

\- Sectors

\- Documents

\- Pros and cons

\- Analytical outputs



The processed data is loaded into the SQLite database.



\## 3.2 Database Layer



The main database is:



`data/db/n100.db`



The database provides the common data source for API and dashboard operations.



\## 3.3 Analytics Layer



The analytics layer calculates and interprets:



\- CAGR

\- Financial ratios

\- Cash-flow KPIs

\- Peer comparisons

\- Valuation

\- Clustering

\- Capital allocation

\- Portfolio statistics



\## 3.4 API Layer



FastAPI exposes the analytical data through REST endpoints.



The main application is:



`src/api/main.py`



\## 3.5 Dashboard Layer



Streamlit provides the interactive analyst interface.



The main application is:



`src/dashboard/app.py`



\---



\# 4. Data Flow



The high-level data flow is:



```text

Raw Data

&#x20;  |

&#x20;  v

ETL Normalisation

&#x20;  |

&#x20;  v

Data Validation

&#x20;  |

&#x20;  v

Processed Data

&#x20;  |

&#x20;  v

SQLite Database

&#x20;  |

&#x20;  +--------------------+

&#x20;  |                    |

&#x20;  v                    v

Analytics             API

&#x20;  |                    |

&#x20;  v                    v

Dashboard            External Clients

&#x20;  |

&#x20;  v

Analyst

