IPL ANALYTICS DASHBOARD — ENHANCED EDITION

FEATURES
- Premium dark cricket analytics theme and sidebar navigation
- Global season/team filters and KPI cards
- Overview charts: team win rate, season titles, runs by season, dismissals, toss decisions
- Batting Lab: player profiles, runs, strike rate, fours, sixes and innings chart
- Bowling Lab: wicket rankings, bowler profiles, economy estimate and wicket hauls
- Team Comparison: overall record, head-to-head wins, runs scored and match history
- Match Explorer: search and inspect match/ball-by-ball data
- Reports & Export: filtered CSV downloads and PDF summary

RUN
1. Extract IPL_Dashboard_Enhanced.zip.
2. Put matches.csv and deliveries.csv beside app.py, or upload both in the app sidebar.
3. Install: pip install -r requirements.txt
4. Start: streamlit run app.py

DATA
The supplied IPL.ipynb references matches.csv and deliveries.csv, but those datasets were not bundled with the notebook. The dashboard therefore asks you to provide both CSV files.
