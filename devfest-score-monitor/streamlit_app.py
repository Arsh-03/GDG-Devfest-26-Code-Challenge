"""GDG DevFest '26 Belagavi — Diamond Heist Live Streamlit Dashboard."""

import html
import time
from pathlib import Path

import streamlit as st

from leaderboard import DEFAULT_DATA_FILE, compute_standings, load_submissions
from simulate_race import simulate

st.set_page_config(
    page_title="DevFest '26 Belagavi — The Diamond Heist",
    page_icon="💎",
    layout="wide",
)

CUSTOM_CSS = """
<style>
  .google-strip {
    height: 6px;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-radius: 999px;
    overflow: hidden;
    margin-bottom: 18px;
  }
  .google-strip span:nth-child(1) { background: #4285F4; }
  .google-strip span:nth-child(2) { background: #EA4335; }
  .google-strip span:nth-child(3) { background: #FBBC04; }
  .google-strip span:nth-child(4) { background: #34A853; }
  .brand-pill {
    display: inline-block;
    background: rgba(66, 133, 244, 0.16);
    border: 1px solid rgba(66, 133, 244, 0.5);
    color: #93c5fd;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 999px;
    margin-bottom: 8px;
  }
  .diamond-card {
    background: linear-gradient(135deg, #11182c 0%, #17213a 100%);
    border: 1px solid #263354;
    border-radius: 14px;
    padding: 18px 20px;
    color: #f1f5f9;
    margin-bottom: 12px;
  }
  .diamond-card.stolen-1 {
    border-color: #FBBC04;
    box-shadow: 0 0 24px rgba(251, 188, 4, 0.18);
  }
  .diamond-card.stolen-2 {
    border-color: #4285F4;
    box-shadow: 0 0 24px rgba(66, 133, 244, 0.20);
  }
  .d-label {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94a3b8;
  }
  .stolen-1 .d-label { color: #FBBC04; }
  .stolen-2 .d-label { color: #60a5fa; }
  .d-team { font-size: 1.45rem; font-weight: 800; margin-top: 4px; }
  .d-meta { font-size: 0.88rem; color: #94a3b8; margin-top: 4px; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="google-strip"><span></span><span></span><span></span><span></span></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="brand-pill">GDG DevFest \'26 Belagavi</div>', unsafe_allow_html=True)
st.title("Round 3 Finale: The Diamond Heist")
st.caption("Two DevFest Diamonds are locked in the vault. First two teams to pass all 7 checks (4 Core + 3 Escape) win!")

if "frozen" not in st.session_state:
    st.session_state.frozen = False
if "frozen_rows" not in st.session_state:
    st.session_state.frozen_rows = None

with st.sidebar:
    st.header("Judge Controls")
    data_path_str = st.text_input("Submissions JSON", value=str(DEFAULT_DATA_FILE))
    data_file = Path(data_path_str)

    freeze_toggle = st.toggle("Freeze Board", value=st.session_state.frozen)
    if freeze_toggle != st.session_state.frozen:
        st.session_state.frozen = freeze_toggle
        if freeze_toggle:
            st.session_state.frozen_rows = compute_standings(load_submissions(data_file))
        else:
            st.session_state.frozen_rows = None

    st.divider()
    if st.button("Simulate 5-Team Race", width="stretch"):
        simulate(data_file=data_file, reset=True)
        st.session_state.frozen_rows = None
        st.rerun()

    if st.button("Clear Submissions", type="secondary", width="stretch"):
        if data_file.is_file():
            data_file.unlink()
        st.session_state.frozen_rows = None
        st.rerun()


def render_diamond_card(num: int, winner: dict | None):
    if winner is None:
        return f"""
        <div class="diamond-card">
          <div class="d-label">💎 DevFest Diamond #{num} — IN VAULT</div>
          <div class="d-team" style="color:#94a3b8;">Locked &amp; Guarded</div>
          <div class="d-meta">Pass 4 Core + 3 Escape tests to claim</div>
        </div>
        """
    cls = "stolen-1" if num == 1 else "stolen-2"
    team = html.escape(winner["team"])
    lang = html.escape(winner["language"])
    comp = html.escape(winner["completed_at"] or "")
    return f"""
    <div class="diamond-card {cls}">
      <div class="d-label">💎 DevFest Diamond #{num} — STOLEN!</div>
      <div class="d-team">{team}</div>
      <div class="d-meta">Lang: {lang} · Score: {winner['total_score']:.1f} · {comp}</div>
    </div>
    """


@st.fragment(run_every=2)
def live_board():
    if st.session_state.frozen:
        st.error("BOARD FROZEN — Standings are locked for the final minutes of the heist!")
        rows = st.session_state.frozen_rows or []
    else:
        rows = compute_standings(load_submissions(data_file))

    d1 = next((r for r in rows if r["winner_badge"] == "DIAMOND #1"), None)
    d2 = next((r for r in rows if r["winner_badge"] == "DIAMOND #2"), None)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(render_diamond_card(1, d1), unsafe_allow_html=True)
    with c2:
        st.markdown(render_diamond_card(2, d2), unsafe_allow_html=True)

    if not rows:
        st.info("Waiting for teams to save (`Ctrl+S` via `sync.py`) or submit...")
        return

    table_rows = []
    for r in rows:
        pct = int(round((r["tests_passed"] / r["tests_total"]) * 100)) if r["tests_total"] > 0 else 0
        table_rows.append({
            "Rank": f"#{r['rank']}",
            "Team": r["team"],
            "Lang": r["language"],
            "Vault Breach %": pct,
            "Core": f"{r['core_passed']}/{r['core_total']}",
            "Escape": f"{r['ext_passed']}/{r['ext_total']}",
            "Clean": round(r["cleanliness"], 1),
            "Score": round(r["total_score"], 1),
            "Status": r["winner_badge"] or "BREACHING",
            "Stolen At (UTC)": r["completed_at"] or "-",
        })

    st.dataframe(
        table_rows,
        width="stretch",
        hide_index=True,
        column_config={
            "Vault Breach %": st.column_config.ProgressColumn(
                "Vault Breach",
                min_value=0,
                max_value=100,
                format="%d%%",
            ),
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Clean": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    st.caption(f"Last refreshed: {time.strftime('%H:%M:%S')} (auto-updates every 2s)")


live_board()
