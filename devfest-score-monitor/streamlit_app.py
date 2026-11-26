"""GDG DevFest '26 Belagavi — Diamond Heist Live Streamlit Dashboard."""

import html
import time
from pathlib import Path

import streamlit as st

from leaderboard import (
    DEFAULT_DATA_FILE,
    DEFAULT_PARTICIPANTS_FILE,
    compute_standings,
    load_participants,
    load_submissions,
    save_participants,
)
from runner import DEFAULT_CHALLENGES_ROOT, judge_code
from simulate_race import build_core_only_python, simulate

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

    st.divider()
    st.subheader("👥 Participant Mapping")
    roster = load_participants(DEFAULT_PARTICIPANTS_FILE)
    with st.form("map_participant_form", clear_on_submit=True):
        m_id = st.text_input("Team / Sync ID", placeholder="e.g. team_01 or CyberPhantoms")
        m_name = st.text_input("Display Team Name", placeholder="e.g. Cyber Phantoms")
        m_members = st.text_input("Participant Names", placeholder="e.g. Alice, Bob")
        if st.form_submit_button("Save Mapping", width="stretch"):
            if m_id.strip():
                roster[m_id.strip()] = {
                    "name": m_name.strip() or m_id.strip(),
                    "members": m_members.strip(),
                }
                save_participants(roster, DEFAULT_PARTICIPANTS_FILE)
                st.toast(f"Mapped '{m_id.strip()}'")
                st.rerun()

    if roster:
        with st.expander(f"Mapped Participants ({len(roster)})"):
            for tid, info in list(roster.items()):
                st.caption(f"**{tid}** → {info.get('name', tid)} ({info.get('members') or 'No members listed'})")
            if st.button("Clear All Mappings", width="stretch"):
                save_participants({}, DEFAULT_PARTICIPANTS_FILE)
                st.rerun()

    st.divider()
    st.subheader("🧪 Manual Test & Judge")
    team_options = list(roster.keys())
    selected_id = st.selectbox("Select Mapped Team (or type below)", options=[""] + team_options)
    manual_team = st.text_input("Team ID to Test", value=selected_id or "TestTeam_1")
    manual_member_names = st.text_input(
        "Participant Name(s) (auto-maps)",
        value=roster.get(manual_team.strip(), {}).get("members", ""),
        placeholder="e.g. Rahul, Priya",
    )
    test_mode = st.selectbox(
        "Test Mode",
        [
            "Preset: Reference Solution (7/7 Pass - 100 pts)",
            "Preset: Core Only (4/7 Pass - 60 pts)",
            "Preset: Buggy Starter (Fails)",
            "Upload Starter File (.py / .c / .java)",
            "Paste Code Manually",
            "Direct Score Override (Manual Points)",
        ],
    )
    manual_lang = st.selectbox("Language", ["Python", "C", "Java"])
    ext_map = {"Python": "starter.py", "C": "starter.c", "Java": "Starter.java"}
    lang_folder = {"Python": "python", "C": "c", "Java": "java"}[manual_lang]

    uploaded_file = None
    pasted_code = ""
    manual_core_pass = 4
    manual_ext_pass = 3
    manual_clean = 20.0

    if test_mode == "Upload Starter File (.py / .c / .java)":
        uploaded_file = st.file_uploader("Choose file", type=["py", "c", "java"])
    elif test_mode == "Paste Code Manually":
        default_src = (DEFAULT_CHALLENGES_ROOT / lang_folder / ext_map[manual_lang]).read_text(encoding="utf-8")
        pasted_code = st.text_area("Source Code", value=default_src, height=180)
    elif test_mode == "Direct Score Override (Manual Points)":
        manual_core_pass = st.slider("Core Tests Passed (out of 4)", 0, 4, 4)
        manual_ext_pass = st.slider("Escape Tests Passed (out of 3)", 0, 3, 2)
        manual_clean = st.slider("Cleanliness Score (0-20)", 0.0, 20.0, 18.0, 0.5)

    if st.button("Run Manual Test", type="primary", width="stretch"):
        tid = manual_team.strip()
        if not tid:
            st.error("Enter a Team ID.")
        else:
            if manual_member_names.strip():
                existing_name = roster.get(tid, {}).get("name", tid)
                roster[tid] = {"name": existing_name, "members": manual_member_names.strip()}
                save_participants(roster, DEFAULT_PARTICIPANTS_FILE)

            if test_mode == "Direct Score Override (Manual Points)":
                import json
                from datetime import datetime, timezone

                c_pts = round(40.0 * (manual_core_pass / 4), 2)
                e_pts = round(30.0 * (manual_ext_pass / 3), 2)
                done = manual_core_pass == 4 and manual_ext_pass == 3
                bonus = 10.0 if done else 0.0
                now_iso = datetime.now(timezone.utc).isoformat()
                rec = {
                    "team": tid,
                    "challenge": "diamond_heist",
                    "language": manual_lang,
                    "filename": ext_map[manual_lang],
                    "submitted_at": now_iso,
                    "completed_all": done,
                    "completed_at": now_iso if done else None,
                    "compile_error": None,
                    "core": {"passed": manual_core_pass, "total": 4, "failed": 4 - manual_core_pass, "errors": 0, "timed_out": False, "score": c_pts, "details": []},
                    "extension": {"passed": manual_ext_pass, "total": 3, "failed": 3 - manual_ext_pass, "errors": 0, "timed_out": False, "score": e_pts, "details": []},
                    "cleanliness": {"score": manual_clean, "override": True, "notes": ["Manual judge score entry"]},
                    "speed_bonus": bonus,
                    "total_score": round(c_pts + e_pts + manual_clean + bonus, 2),
                }
                existing = load_submissions(data_file)
                existing.append(rec)
                data_file.parent.mkdir(parents=True, exist_ok=True)
                data_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
                st.session_state.last_test_result = rec
                st.rerun()
            else:
                fname = ext_map[manual_lang]
                code_to_run = None
                ref_name = "reference_solution.py" if manual_lang == "Python" else ("reference_solution.c" if manual_lang == "C" else "ReferenceSolution.java")
                if test_mode.startswith("Preset: Reference"):
                    code_to_run = (DEFAULT_CHALLENGES_ROOT / lang_folder / ref_name).read_text(encoding="utf-8")
                    if manual_lang == "Java":
                        code_to_run = code_to_run.replace("class ReferenceSolution", "class Starter")
                elif test_mode.startswith("Preset: Core Only"):
                    py_ref = (DEFAULT_CHALLENGES_ROOT / "python" / "reference_solution.py").read_text(encoding="utf-8")
                    code_to_run = build_core_only_python(py_ref)
                    fname = "starter.py"
                elif test_mode.startswith("Preset: Buggy"):
                    code_to_run = (DEFAULT_CHALLENGES_ROOT / lang_folder / ext_map[manual_lang]).read_text(encoding="utf-8")
                elif test_mode.startswith("Upload"):
                    if uploaded_file is None:
                        st.error("Please upload a file first.")
                    else:
                        fname = uploaded_file.name
                        code_to_run = uploaded_file.getvalue().decode("utf-8")
                elif test_mode.startswith("Paste"):
                    code_to_run = pasted_code

                if code_to_run is not None:
                    rec = judge_code(
                        team=tid,
                        filename=fname,
                        code_text=code_to_run,
                        data_file=data_file,
                    )
                    st.session_state.last_test_result = rec
                    st.rerun()

    if "last_test_result" in st.session_state:
        res = st.session_state.last_test_result
        st.success(
            f"**{res['team']}** ({res['language']}) → **{res['total_score']} pts** "
            f"(Core {res['core']['passed']}/{res['core']['total']}, "
            f"Escape {res['extension']['passed']}/{res['extension']['total']})"
        )
        if res.get("compile_error"):
            st.error(res["compile_error"])


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
    members = html.escape(winner.get("participants", ""))
    member_html = f'<div class="d-meta" style="color:#cbd5e1;">👤 {members}</div>' if members else ""
    lang = html.escape(winner["language"])
    comp = html.escape(winner["completed_at"] or "")
    return f"""
    <div class="diamond-card {cls}">
      <div class="d-label">💎 DevFest Diamond #{num} — STOLEN!</div>
      <div class="d-team">{team}</div>
      {member_html}
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
            "Participants": r.get("participants") or "-",
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
