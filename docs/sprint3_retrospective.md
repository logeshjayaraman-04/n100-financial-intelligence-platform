\# SPRINT 3 RETROSPECTIVE



\## Sprint Information



Sprint: Sprint 3

Days: Day 15–21

Epics: Epic 03 — Screener + Epic 04 — Peer Engine

Target Story Points: 49 SP

Due Date: 08 Sep 2026



\---



\## Sprint Goal



The financial screener was implemented with preset filters and custom threshold support.



Peer percentile rankings were implemented for the defined peer groups and metrics.



Screener and peer comparison Excel reports were generated and validated.



Radar charts were generated for the company universe.



\---



\## Day 15 — Filter Engine Core



Implemented the screener engine in:



`src/screener/engine.py`



Supported filterable metrics include:



\- ROE

\- D/E

\- FCF

\- Revenue CAGR 5yr

\- PAT CAGR 5yr

\- OPM

\- P/E

\- P/B

\- Dividend Yield

\- ICR

\- Market Cap

\- Net Profit

\- EPS CAGR

\- Asset Turnover

\- Sales



The screener engine supports custom threshold filtering and returns results with the composite quality score.



\---



\## Day 16 — Preset Screeners



Implemented six preset screeners:



1\. Quality Compounder

2\. Value Pick

3\. Growth Accelerator

4\. Dividend Champion

5\. Debt-Free Blue Chip

6\. Turnaround Watch



Observed validation results:



\- Quality Compounder: 23 companies

\- Value Pick: 2 companies

\- Growth Accelerator: 19 companies

\- Dividend Champion: 30 companies

\- Debt-Free Blue Chip: 2 companies

\- Turnaround Watch: 36 companies



The preset engine executes successfully and produces business-readable results.



\---



\## Day 17 — Screener Export



Generated:



`output/screener\_output.xlsx`



The workbook contains exactly 6 sheets:



\- Quality Compounder

\- Value Pick

\- Growth Accelerator

\- Dividend Champion

\- Debt-Free Blue Chip

\- Turnaround Watch



The workbook was successfully generated and verified.



\---



\## Day 18 — Peer Percentile Rankings



Implemented peer percentile ranking functionality in:



`src/analytics/peer.py`



Validation results:



\- Peer groups: 11

\- Companies in peer groups: 56

\- Metrics: 10

\- Percentile rows: 540

\- Invalid percentile rows: 0



The following metrics were ranked:



\- ROE

\- ROCE

\- Net Profit Margin

\- D/E

\- FCF

\- PAT CAGR 5yr

\- Revenue CAGR 5yr

\- EPS CAGR 5yr

\- Interest Coverage

\- Asset Turnover



D/E ranking uses inverse ranking so lower D/E receives a higher percentile.



\---



\## Day 19 — Radar Charts



Generated radar charts for the company universe.



Output directory:



`reports/radar\_charts`



Validation:



\- Charts generated: 100

\- PNG files verified: 100



The charts include the requested financial metrics and peer/reference comparison.



\---



\## Day 20 — Peer Comparison Excel Report



Generated:



`output/peer\_comparison.xlsx`



The workbook was verified to contain exactly 11 sheets:



\- Automobiles

\- Consumer Finance

\- FMCG

\- IT Services

\- Life Insurance

\- Oil \& Gas

\- Pharmaceuticals

\- Power \& Utilities

\- Private Banks

\- Public Sector Banks

\- Steel



Sheet count verification:



11 sheets



The peer comparison workbook was successfully generated.



\---



\## Day 21 — Testing and Review



Full project test suite was executed.



Result:



`102 passed`



Failures:



`0`



Quality Compounder verification:



ROE > 15%

D/E < 1



Result:



38 companies



The result is within the required 5–50 company range.



\---



\## IT Services Peer Verification



IT Services ROE percentile ranking was manually verified.



Results:



\- TCS — ROE 50.94 — 100th percentile

\- INFY — ROE 29.79 — 80th percentile

\- HCLTECH — ROE 23.01 — 60th percentile

\- LTIM — ROE 22.90 — 40th percentile

\- TECHM — ROE 8.99 — 20th percentile



Validation:



The company with the highest ROE also has the highest ROE percentile.



Result:



PASS



\---



\## Sprint 3 Technical Outcome



The following deliverables were completed:



\- `src/screener/engine.py`

\- `src/screener/presets.py`

\- `src/analytics/peer.py`

\- `src/analytics/radar.py`

\- `src/analytics/peer\_comparison.py`

\- `output/screener\_output.xlsx`

\- `output/peer\_comparison.xlsx`

\- `reports/radar\_charts/`



\---



\## Testing Summary



Full automated test suite:



102 passed



Failures:



0



Peer percentile validation:



PASS



Quality Compounder validation:



PASS



IT Services peer ranking validation:



PASS



Screener Excel sheet count:



6



Peer comparison Excel sheet count:



11



Radar chart count:



100



\---



\## Formula and Implementation Decisions



\### Screener



The screener supports custom threshold filters and preset screening strategies.



Financials-sector companies are handled specially for D/E filtering because high leverage is structurally normal for financial institutions.



Debt-free companies are handled separately when evaluating interest coverage.



\### Peer Rankings



Peer percentile rankings are calculated within the assigned peer group.



D/E is ranked inversely because lower leverage is considered better for this metric.



Companies without a peer group are not treated as errors.



\### Radar Charts



Radar charts compare company financial characteristics against the relevant peer-group reference.



Companies without a peer group use the Nifty 100 universe as the reference.



\---



\## What Went Well



\- Screener engine successfully implemented.

\- Six preset strategies successfully implemented.

\- Screener Excel export generated successfully.

\- Peer percentile engine generated 540 percentile rows.

\- Eleven peer groups were processed.

\- One hundred radar charts were generated.

\- Peer comparison workbook contains exactly 11 sheets.

\- Full automated test suite passes with zero failures.

\- IT Services peer ranking was manually validated.



\---



\## Issues Encountered and Resolved



\### Missing Python Dependencies



The environment initially lacked:



`PyYAML`



and later:



`matplotlib`



The required dependencies were installed into the virtual environment.



\### PowerShell Command Quoting



Some inline Python/SQL commands failed because of PowerShell quotation handling.



The checks were subsequently moved into standalone Python scripts where necessary.



\### Python File Editing



A syntax error occurred while editing a Python file through Notepad.



The file was corrected and successfully compiled using:



`py\_compile`



\### Export Script Syntax



The initial screener export script contained syntax/indentation errors.



These were corrected and the final workbook was successfully generated.



\---



\## Sprint Result



Sprint 3 technical implementation and validation are complete.



All major software deliverables have been generated.



Automated tests pass with zero failures.



The remaining administrative requirement is Sprint Review sign-off by the team lead.



\---



\## Sprint Review Status



Technical implementation: COMPLETE



Testing: COMPLETE



Deliverables: COMPLETE



Documentation: COMPLETE



Team Lead Sign-off: PENDING



\---



\## Final Verification



Date: 08 Sep 2026



Sprint 3 technical status:



\*\*COMPLETE\*\*



Team Lead Review:



\*\*PENDING SIGN-OFF\*\*



Reviewer Name:



\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



Signature:



\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



Date:



\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

