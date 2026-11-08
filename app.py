import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="IPL Analytics | Cricket Data Studio", page_icon="🏏", layout="wide", initial_sidebar_state="expanded")

# ----------------------------- Theme -----------------------------------------
st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(circle at 85% 0%, #14284a 0, #0b1425 38%, #08111f 100%); color: #edf3ff; }
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container { padding-top: 1.35rem; padding-bottom: 3rem; max-width: 1500px; }
section[data-testid="stSidebar"] { background: #0b1729; border-right: 1px solid #203653; }
section[data-testid="stSidebar"] * { color: #e8efff; }
.hero { padding: 26px 30px; border: 1px solid #29486f; border-radius: 22px; background: linear-gradient(115deg,rgba(16,37,68,.98),rgba(24,67,105,.88)); box-shadow: 0 18px 50px rgba(0,0,0,.22); margin-bottom: 18px; }
.hero-kicker { color:#8dc8ff; font-size: .78rem; letter-spacing: .16em; font-weight: 800; text-transform: uppercase; }
.hero h1 { color:#fff; margin:.25rem 0; font-size:2.25rem; }
.hero p { color:#c2d5ee; margin:0; }
.section-title { color:#f3f7ff; font-size:1.25rem; font-weight:750; margin: 1rem 0 .25rem; }
div[data-testid="stMetric"] { background:linear-gradient(145deg,#13243b,#102039); border:1px solid #29415f; padding:16px 18px; border-radius:16px; }
div[data-testid="stMetricLabel"] { color:#a9bfdc; }
div[data-testid="stMetricValue"] { color:#fff; }
div[data-testid="stMetricDelta"] { color:#73d6ad; }
div[data-testid="stPlotlyChart"] { background:#101e32; border:1px solid #203956; border-radius:16px; padding:8px; }
div[data-testid="stDataFrame"] { border:1px solid #203956; border-radius:12px; }
div.stButton > button, div.stDownloadButton > button { border-radius:10px; border:1px solid #3c6591; background:#17385d; color:#fff; }
div.stButton > button:hover, div.stDownloadButton > button:hover { border-color:#77baff; color:#fff; }
.small-note { color:#91a8c5; font-size:.82rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-kicker">Cricket data studio · IPL</div>
  <h1>🏏 IPL Analytics Dashboard</h1>
  <p>Explore seasons, compare franchises, discover player performances and export your analysis.</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------- Data ------------------------------------------
@st.cache_data(show_spinner=False)
def load_data(matches_source, deliveries_source):
    m = pd.read_csv(matches_source)
    d = pd.read_csv(deliveries_source)
    # Keep the franchise-name cleaning used in the uploaded notebook.
    replacements = {
        "Rising Pune Supergiants": "Rising Pune Supergiant",
        "Royal Challengers Bengaluru": "Royal Challengers Bangalore",
    }
    for col in ["team1", "team2", "toss_winner", "winner"]:
        if col in m:
            m[col] = m[col].astype("string").str.strip().replace(replacements)
    for col in ["batting_team", "bowling_team"]:
        if col in d:
            d[col] = d[col].astype("string").str.strip().replace(replacements)
    if "season" not in m and "date" in m:
        m["season"] = pd.to_datetime(m["date"], errors="coerce").dt.year
    return m, d

st.sidebar.markdown("## 🧭 Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Batting Lab", "Bowling Lab", "Team Comparison", "Match Explorer", "Reports & Export"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("## 📂 Project data")
match_file = st.sidebar.file_uploader("Upload matches.csv", type="csv", key="matches_upload")
delivery_file = st.sidebar.file_uploader("Upload deliveries.csv", type="csv", key="deliveries_upload")
local_matches, local_deliveries = Path("matches.csv"), Path("deliveries.csv")
if match_file is not None and delivery_file is not None:
    matches, deliveries = load_data(match_file, delivery_file)
elif local_matches.exists() and local_deliveries.exists():
    matches, deliveries = load_data(str(local_matches), str(local_deliveries))
else:
    st.info("Upload both CSV files in the sidebar to begin. The notebook contains the analysis code, but the CSV datasets were not included in the supplied project files.")
    st.markdown("**Required files**")
    st.code("matches.csv\ndeliveries.csv")
    st.stop()

required_m = {"team1", "team2", "winner"}
required_d = {"batter", "bowler", "batsman_runs", "total_runs"}
if not required_m.issubset(matches.columns) or not required_d.issubset(deliveries.columns):
    st.error("The CSV files are missing required IPL columns. Expected match columns: team1, team2, winner; delivery columns: batter, bowler, batsman_runs, total_runs.")
    st.stop()

match_id_col = "id" if "id" in matches.columns else ("match_id" if "match_id" in matches.columns else None)
delivery_match_col = "match_id" if "match_id" in deliveries.columns else None
if match_id_col and delivery_match_col:
    deliveries = deliveries[deliveries[delivery_match_col].isin(matches[match_id_col])].copy()

# ----------------------------- Global filters -------------------------------
st.sidebar.markdown("## 🎛️ Filters")
filtered_matches = matches.copy()
if "season" in matches:
    seasons = sorted(matches["season"].dropna().unique().tolist(), key=lambda x: str(x))
    chosen_seasons = st.sidebar.multiselect("Season", seasons, default=seasons)
    filtered_matches = filtered_matches[filtered_matches["season"].isin(chosen_seasons)]
else:
    chosen_seasons = []

teams_all = sorted(set(filtered_matches["team1"].dropna().astype(str)) | set(filtered_matches["team2"].dropna().astype(str)))
chosen_teams = st.sidebar.multiselect("Teams", teams_all, default=teams_all)
if chosen_teams:
    filtered_matches = filtered_matches[filtered_matches["team1"].isin(chosen_teams) | filtered_matches["team2"].isin(chosen_teams)]
elif teams_all:
    filtered_matches = filtered_matches.iloc[0:0]

if match_id_col and delivery_match_col:
    filtered_deliveries = deliveries[deliveries[delivery_match_col].isin(filtered_matches[match_id_col])].copy()
else:
    filtered_deliveries = deliveries.copy()

# Consistent Plotly look
PLOT = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#dce8f8"))
def chart(fig, height=390):
    fig.update_layout(**PLOT, height=height, margin=dict(l=24, r=20, t=62, b=35), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "responsive": True})

def team_summary(frame):
    played = pd.concat([frame["team1"], frame["team2"]]).value_counts()
    wins = frame["winner"].value_counts()
    out = pd.DataFrame({"Team": played.index, "Matches": played.values})
    out["Wins"] = out["Team"].map(wins).fillna(0).astype(int)
    out["Losses"] = (out["Matches"] - out["Wins"]).clip(lower=0)
    out["Win Rate (%)"] = (out["Wins"] / out["Matches"] * 100).round(1)
    return out.sort_values(["Win Rate (%)", "Wins"], ascending=False)

def wickets_count(frame):
    if "is_wicket" in frame:
        return int(pd.to_numeric(frame["is_wicket"], errors="coerce").fillna(0).sum())
    if "dismissal_kind" in frame:
        return int(frame["dismissal_kind"].notna().sum())
    return 0

def add_match_details(delivery_frame, match_frame):
    if not match_id_col or not delivery_match_col:
        return delivery_frame
    cols = [match_id_col] + [c for c in ["season", "city", "venue", "date", "team1", "team2", "winner"] if c in match_frame.columns and c != match_id_col]
    details = match_frame[cols].drop_duplicates(match_id_col).rename(columns={match_id_col: delivery_match_col})
    return delivery_frame.merge(details, on=delivery_match_col, how="left", suffixes=("", "_match"))

# KPI strip
played = len(filtered_matches)
decided = int(filtered_matches["winner"].notna().sum())
runs = int(pd.to_numeric(filtered_deliveries["total_runs"], errors="coerce").fillna(0).sum())
wkts = wickets_count(filtered_deliveries)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Matches", f"{played:,}")
k2.metric("Decided matches", f"{decided:,}", f"{(decided / played * 100):.1f}% decided" if played else None)
k3.metric("Runs scored", f"{runs:,}")
k4.metric("Wickets", f"{wkts:,}")

# ----------------------------- Pages -----------------------------------------
if page == "Overview":
    st.markdown('<div class="section-title">📊 Tournament overview</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    summary = team_summary(filtered_matches) if played else pd.DataFrame()
    with left:
        if not summary.empty:
            chart(px.bar(summary.sort_values("Win Rate (%)"), x="Win Rate (%)", y="Team", orientation="h", color="Win Rate (%)", hover_data=["Wins", "Matches"], title="Franchise win rate"))
        else:
            st.info("No matches in the selected filters.")
    with right:
        if "season" in filtered_matches and played:
            titles = filtered_matches.sort_values("season").groupby("season").tail(1)["winner"].value_counts().rename_axis("Team").reset_index(name="Titles")
            chart(px.bar(titles, x="Team", y="Titles", color="Team", title="Season titles in selected data"))
        elif "city" in filtered_matches and played:
            cities = filtered_matches["city"].fillna("Unknown").value_counts().head(10).rename_axis("City").reset_index(name="Matches")
            chart(px.pie(cities, names="City", values="Matches", hole=.48, title="Top match-hosting cities"))
    if "season" in filtered_matches and "season" in filtered_deliveries.columns if "season" in filtered_deliveries else False:
        pass
    if "season" in filtered_matches and match_id_col and delivery_match_col:
        season_runs = add_match_details(filtered_deliveries, filtered_matches)
        if "season" in season_runs:
            trend = season_runs.groupby("season", as_index=False)["total_runs"].sum()
            chart(px.line(trend, x="season", y="total_runs", markers=True, title="Runs by season"), height=330)
    c1, c2 = st.columns(2)
    with c1:
        if "dismissal_kind" in filtered_deliveries:
            dis = filtered_deliveries["dismissal_kind"].dropna().value_counts().rename_axis("Dismissal").reset_index(name="Count")
            chart(px.bar(dis, x="Dismissal", y="Count", color="Count", title="Dismissal breakdown"), height=340)
    with c2:
        if "toss_decision" in filtered_matches:
            toss = filtered_matches["toss_decision"].dropna().value_counts().rename_axis("Decision").reset_index(name="Matches")
            chart(px.pie(toss, names="Decision", values="Matches", hole=.48, title="Toss decisions"), height=340)
    if not summary.empty:
        st.markdown("#### Franchise leaderboard")
        st.dataframe(summary, use_container_width=True, hide_index=True)

elif page == "Batting Lab":
    st.markdown('<div class="section-title">🏏 Batting performance lab</div>', unsafe_allow_html=True)
    bat = filtered_deliveries.copy()
    bat["batsman_runs"] = pd.to_numeric(bat["batsman_runs"], errors="coerce").fillna(0)
    totals = bat.groupby("batter", as_index=False).agg(Runs=("batsman_runs", "sum"), Balls=("batsman_runs", "count"))
    totals["Strike Rate"] = (totals["Runs"] * 100 / totals["Balls"].replace(0, pd.NA)).round(2)
    if "batsman_runs" in bat:
        totals["Fours"] = bat.assign(_four=bat["batsman_runs"].eq(4)).groupby("batter")["_four"].sum().reindex(totals["batter"]).values
        totals["Sixes"] = bat.assign(_six=bat["batsman_runs"].eq(6)).groupby("batter")["_six"].sum().reindex(totals["batter"]).values
    if totals.empty:
        st.info("No batting data for the selected filters.")
    else:
        metric = st.selectbox("Rank players by", ["Runs", "Strike Rate", "Fours", "Sixes"], key="bat_rank")
        top = totals.nlargest(15, metric)
        chart(px.bar(top.sort_values(metric), x=metric, y="batter", orientation="h", color=metric, hover_data=["Runs", "Balls", "Strike Rate", "Fours", "Sixes"], title=f"Top 15 batters by {metric}"))
        player = st.selectbox("Open player profile", sorted(totals["batter"].dropna().unique()), key="bat_player")
        p = totals[totals["batter"] == player].iloc[0]
        p1,p2,p3,p4 = st.columns(4)
        p1.metric("Career runs (filtered)", f"{int(p['Runs']):,}")
        p2.metric("Balls faced", f"{int(p['Balls']):,}")
        p3.metric("Strike rate", f"{p['Strike Rate']:.2f}")
        p4.metric("Sixes", f"{int(p.get('Sixes', 0)):,}")
        if delivery_match_col:
            innings = bat[bat["batter"] == player].groupby(delivery_match_col, as_index=False).agg(Runs=("batsman_runs", "sum"), Balls=("batsman_runs", "count"))
            innings["Strike Rate"] = (innings["Runs"] * 100 / innings["Balls"].replace(0, pd.NA)).round(1)
            chart(px.scatter(innings, x="Runs", y="Strike Rate", size="Balls", hover_data=[delivery_match_col], title=f"{player} · innings runs vs strike rate"), height=350)
        st.dataframe(totals.sort_values("Runs", ascending=False), use_container_width=True, hide_index=True)

elif page == "Bowling Lab":
    st.markdown('<div class="section-title">🎯 Bowling performance lab</div>', unsafe_allow_html=True)
    bowl = filtered_deliveries.copy()
    if "dismissal_kind" in bowl:
        valid = bowl[bowl["dismissal_kind"].notna() & ~bowl["dismissal_kind"].astype(str).str.lower().isin(["run out", "retired hurt", "obstructing the field"])]
        wickets = valid.groupby("bowler").size().rename("Wickets")
    elif "is_wicket" in bowl:
        valid = bowl[pd.to_numeric(bowl["is_wicket"], errors="coerce").fillna(0).eq(1)]
        wickets = valid.groupby("bowler").size().rename("Wickets")
    else:
        valid = bowl.iloc[0:0]
        wickets = pd.Series(dtype=int)
    if wickets.empty:
        st.info("No wicket data available for the current filters.")
    else:
        bowling = wickets.reset_index().rename(columns={"index": "Bowler"})
        bowling["Bowler"] = bowling["bowler"] if "bowler" in bowling else bowling.iloc[:,0]
        rank = st.selectbox("Rank bowlers by", ["Wickets"], key="bowl_rank")
        top = bowling.nlargest(15, rank)
        chart(px.bar(top.sort_values(rank), x=rank, y="Bowler", orientation="h", color=rank, title="Top wicket takers (run-outs excluded)"))
        player = st.selectbox("Open bowler profile", sorted(wickets.index.dropna().unique()), key="bowl_player")
        player_balls = bowl[bowl["bowler"] == player]
        conceded = pd.to_numeric(player_balls["total_runs"], errors="coerce").fillna(0).sum()
        legal = len(player_balls)
        economy = conceded / (legal / 6) if legal else 0
        bp1,bp2,bp3 = st.columns(3)
        bp1.metric("Wickets", f"{int(wickets.get(player, 0)):,}")
        bp2.metric("Runs conceded", f"{int(conceded):,}")
        bp3.metric("Economy (approx.)", f"{economy:.2f}")
        if delivery_match_col:
            match_w = valid[valid["bowler"] == player].groupby(delivery_match_col).size().reset_index(name="Wickets")
            chart(px.bar(match_w.nlargest(10, "Wickets"), x=delivery_match_col, y="Wickets", title=f"{player} · best wicket hauls"), height=330)
        st.dataframe(bowling.sort_values("Wickets", ascending=False), use_container_width=True, hide_index=True)

elif page == "Team Comparison":
    st.markdown('<div class="section-title">⚔️ Head-to-head franchise comparison</div>', unsafe_allow_html=True)
    options = sorted(set(matches["team1"].dropna().astype(str)) | set(matches["team2"].dropna().astype(str)))
    if len(options) < 2:
        st.info("At least two teams are required.")
    else:
        ca, cb = st.columns(2)
        default_a = options[0]
        default_b = options[1]
        team_a = ca.selectbox("Team A", options, index=options.index(default_a))
        team_b = cb.selectbox("Team B", options, index=options.index(default_b))
        if team_a == team_b:
            st.warning("Choose two different teams to compare.")
        else:
            pair = filtered_matches[((filtered_matches["team1"] == team_a) & (filtered_matches["team2"] == team_b)) | ((filtered_matches["team1"] == team_b) & (filtered_matches["team2"] == team_a))]
            a_matches = filtered_matches[(filtered_matches["team1"] == team_a) | (filtered_matches["team2"] == team_a)]
            b_matches = filtered_matches[(filtered_matches["team1"] == team_b) | (filtered_matches["team2"] == team_b)]
            a_wins = int((a_matches["winner"] == team_a).sum())
            b_wins = int((b_matches["winner"] == team_b).sum())
            h2h_a = int((pair["winner"] == team_a).sum())
            h2h_b = int((pair["winner"] == team_b).sum())
            x,y,z = st.columns(3)
            x.metric(f"{team_a} · total wins", a_wins)
            y.metric(f"{team_b} · total wins", b_wins)
            z.metric("Head-to-head matches", len(pair))
            compare = pd.DataFrame({"Team":[team_a, team_b], "Wins":[a_wins,b_wins], "Matches played":[len(a_matches),len(b_matches)], "Head-to-head wins":[h2h_a,h2h_b]})
            chart(px.bar(compare.melt(id_vars="Team", var_name="Metric", value_name="Count"), x="Team", y="Count", color="Metric", barmode="group", title="Overall and head-to-head record"), height=390)
            if match_id_col and delivery_match_col:
                ids_a = set(a_matches[match_id_col])
                ids_b = set(b_matches[match_id_col])
                d_a = filtered_deliveries[filtered_deliveries[delivery_match_col].isin(ids_a)]
                d_b = filtered_deliveries[filtered_deliveries[delivery_match_col].isin(ids_b)]
                score = pd.DataFrame({"Team":[team_a,team_b], "Runs scored":[d_a.loc[d_a.get("batting_team", pd.Series(index=d_a.index,dtype=object)) == team_a, "total_runs"].sum() if "batting_team" in d_a else 0, d_b.loc[d_b.get("batting_team", pd.Series(index=d_b.index,dtype=object)) == team_b, "total_runs"].sum() if "batting_team" in d_b else 0]})
                chart(px.bar(score, x="Team", y="Runs scored", color="Team", title="Runs scored in selected matches"), height=300)
            st.markdown("#### Head-to-head match history")
            st.dataframe(pair.sort_values("date", ascending=False) if "date" in pair else pair, use_container_width=True, hide_index=True)

elif page == "Match Explorer":
    st.markdown('<div class="section-title">🔎 Match explorer</div>', unsafe_allow_html=True)
    search = st.text_input("Search team, winner, city or venue", placeholder="Start typing a team or venue...")
    view = filtered_matches.copy()
    searchable = [c for c in ["team1", "team2", "winner", "city", "venue"] if c in view]
    if search and searchable:
        mask = pd.Series(False, index=view.index)
        for col in searchable:
            mask |= view[col].astype("string").str.contains(search, case=False, na=False)
        view = view[mask]
    if "date" in view:
        view = view.sort_values("date", ascending=False)
    st.caption(f"{len(view):,} matches found")
    st.dataframe(view, use_container_width=True, hide_index=True)
    if not view.empty and match_id_col and delivery_match_col:
        labels = view.apply(lambda r: f"{r.get('date','') } | {r.get('team1','Team 1')} vs {r.get('team2','Team 2')} | {r.get('venue', r.get('city',''))}", axis=1)
        chosen_label = st.selectbox("Inspect a match", labels.tolist())
        chosen_id = view.loc[labels == chosen_label, match_id_col].iloc[0]
        detail = filtered_deliveries[filtered_deliveries[delivery_match_col] == chosen_id]
        st.markdown("#### Ball-by-ball scorecard data")
        st.dataframe(detail, use_container_width=True, hide_index=True)

elif page == "Reports & Export":
    st.markdown('<div class="section-title">📥 Reports & data export</div>', unsafe_allow_html=True)
    st.write("Download the filtered match and ball-by-ball data, or export a compact PDF summary.")
    team_table = team_summary(filtered_matches) if played else pd.DataFrame(columns=["Team","Matches","Wins","Losses","Win Rate (%)"])
    e1,e2 = st.columns(2)
    with e1:
        st.download_button("⬇️ Download filtered matches (CSV)", filtered_matches.to_csv(index=False).encode("utf-8"), "ipl_filtered_matches.csv", "text/csv", use_container_width=True)
    with e2:
        st.download_button("⬇️ Download filtered deliveries (CSV)", filtered_deliveries.to_csv(index=False).encode("utf-8"), "ipl_filtered_deliveries.csv", "text/csv", use_container_width=True)
    st.markdown("#### Team leaderboard")
    st.dataframe(team_table, use_container_width=True, hide_index=True)
    # A dependency-free PDF export using ReportLab, included in requirements.
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, title="IPL Analytics Summary")
        styles = getSampleStyleSheet()
        story = [Paragraph("IPL Analytics Dashboard — Summary Report", styles["Title"]), Spacer(1, 12),
                 Paragraph(f"Matches: {played:,} &nbsp;&nbsp; Decided: {decided:,} &nbsp;&nbsp; Runs: {runs:,} &nbsp;&nbsp; Wickets: {wkts:,}", styles["BodyText"]), Spacer(1, 14)]
        table_data = [list(team_table.columns)] + team_table.head(20).astype(str).values.tolist() if not team_table.empty else [["No team data"]]
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17385d")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.grey),("FONTSIZE",(0,0),(-1,-1),8),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#edf3f8")])]))
        story.append(table)
        doc.build(story)
        st.download_button("⬇️ Download PDF summary", pdf_buffer.getvalue(), "ipl_analytics_summary.pdf", "application/pdf", use_container_width=True)
    except ImportError:
        st.warning("Install reportlab to enable PDF export. CSV downloads are available.")

st.divider()
st.markdown('<p class="small-note">IPL Analytics · Built from the supplied IPL.ipynb analysis themes · Filtered results reflect the CSV data you upload.</p>', unsafe_allow_html=True)
