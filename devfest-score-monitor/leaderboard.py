"""DevFest 26 Belagavi — Diamond Heist live terminal & HTTP dashboard."""

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from runner import DEFAULT_CHALLENGES_ROOT, DEFAULT_DATA_FILE, judge_code

MAX_SUBMISSION_BYTES = 256 * 1024
DEFAULT_PARTICIPANTS_FILE = Path(__file__).resolve().parent / "data" / "participants.json"


def load_participants(path: Path = DEFAULT_PARTICIPANTS_FILE) -> dict[str, dict]:
    """Load participant/team roster mapping {team_id: {'name': str, 'members': str}}."""
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def save_participants(mapping: dict[str, dict], path: Path = DEFAULT_PARTICIPANTS_FILE) -> None:
    """Save participant/team roster mapping to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=2), encoding="utf-8")


def load_submissions(data_file: Path) -> list[dict]:
    """Load submission records from JSON file."""
    if not data_file.is_file():
        return []
    try:
        data = json.loads(data_file.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def compute_standings(
    records: list[dict],
    challenge: str | None = None,
    participants: dict[str, dict] | None = None,
) -> list[dict]:
    """Aggregate latest status per team (preserving earliest completion) and rank them.

    Tie-breaker order:
      1. Most tests passed (core + extension, desc)
      2. Earliest completed_at timestamp (asc; incomplete teams last)
      3. Higher total_score (desc)
      4. Team name (asc)
    """
    roster = participants if participants is not None else load_participants()
    filtered = [r for r in records if challenge is None or r.get("challenge") == challenge]
    by_team: dict[str, dict] = {}

    for rec in filtered:
        team = rec["team"]
        prev = by_team.get(team)
        if prev is None:
            by_team[team] = dict(rec)
            continue

        earliest_completed = prev.get("completed_at")
        new_completed = rec.get("completed_at")
        merged = dict(rec)
        if earliest_completed and (not new_completed or earliest_completed < new_completed):
            merged["completed_at"] = earliest_completed
            merged["completed_all"] = True
        by_team[team] = merged

    rows = []
    for rec in by_team.values():
        core = rec.get("core", {})
        ext = rec.get("extension", {})
        tests_passed = core.get("passed", 0) + ext.get("passed", 0)
        tests_total = core.get("total", 0) + ext.get("total", 0)
        team_id = rec["team"]
        p_info = roster.get(team_id, {})
        rows.append({
            "team_id": team_id,
            "team": p_info.get("name") or team_id,
            "participants": p_info.get("members", ""),
            "challenge": rec.get("challenge", "diamond_heist"),
            "language": rec.get("language", "Python"),
            "core_passed": core.get("passed", 0),
            "core_total": core.get("total", 0),
            "ext_passed": ext.get("passed", 0),
            "ext_total": ext.get("total", 0),
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "cleanliness": rec.get("cleanliness", {}).get("score", 0.0),
            "speed_bonus": rec.get("speed_bonus", 0.0),
            "total_score": rec.get("total_score", 0.0),
            "completed_all": bool(rec.get("completed_all", False)),
            "completed_at": rec.get("completed_at"),
            "submitted_at": rec.get("submitted_at"),
            "compile_error": rec.get("compile_error"),
        })

    rows.sort(
        key=lambda r: (
            -r["tests_passed"],
            0 if r["completed_at"] else 1,
            r["completed_at"] or "~",
            -r["total_score"],
            r["team"].lower(),
        )
    )

    completed_rank = 0
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
        if row["completed_all"]:
            completed_rank += 1
            row["winner_badge"] = (
                "DIAMOND #1" if completed_rank == 1 else
                "DIAMOND #2" if completed_rank == 2 else
                "BREACHED"
            )
        else:
            row["winner_badge"] = ""
    return rows


def render_terminal_table(rows: list[dict], frozen: bool = False) -> str:
    """Format standings as a clean ASCII table for terminal output."""
    header_banner = "=== GDG DEVFEST '26 BELAGAVI — DIAMOND HEIST LEADERBOARD ==="
    if frozen:
        header_banner += " [BOARD FROZEN]"

    cols = (
        f"{'Rank':<5} {'Team':<18} {'Lang':<7} {'Core':<7} {'Escape':<7} "
        f"{'Clean':<7} {'Score':<7} {'Status':<13} {'Stolen At'}"
    )
    sep = "-" * 104
    lines = [header_banner, sep, cols, sep]

    if not rows:
        lines.append("No vault breach attempts recorded yet.")
    else:
        for r in rows:
            core_str = f"{r['core_passed']}/{r['core_total']}"
            ext_str = f"{r['ext_passed']}/{r['ext_total']}"
            status = r["winner_badge"] or "BREACHING"
            comp = r["completed_at"][:19].replace("T", " ") + "Z" if r["completed_at"] else "-"
            lines.append(
                f"{r['rank']:<5} {r['team']:<18} {r['language']:<7} {core_str:<7} {ext_str:<7} "
                f"{r['cleanliness']:<7.1f} {r['total_score']:<7.1f} {status:<13} {comp}"
            )
    lines.append(sep)
    return "\n".join(lines)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DevFest '26 Belagavi — The Diamond Heist</title>
  <style>
    :root {
      --g-blue: #4285F4;
      --g-red: #EA4335;
      --g-yellow: #FBBC04;
      --g-green: #34A853;
      --bg: #080d1a;
      --surface: #11182c;
      --surface-2: #17213a;
      --border: #263354;
      --text: #f1f5f9;
      --muted: #94a3b8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Segoe UI', system-ui, -apple-system, Roboto, sans-serif;
      background: radial-gradient(circle at top right, rgba(66, 133, 244, 0.14), transparent 45%),
                  radial-gradient(circle at top left, rgba(251, 188, 4, 0.08), transparent 40%),
                  var(--bg);
      color: var(--text);
    }
    .google-strip {
      height: 5px;
      display: grid;
      grid-template-columns: repeat(4, 1fr);
    }
    .google-strip span:nth-child(1) { background: var(--g-blue); }
    .google-strip span:nth-child(2) { background: var(--g-red); }
    .google-strip span:nth-child(3) { background: var(--g-yellow); }
    .google-strip span:nth-child(4) { background: var(--g-green); }

    .container { max-width: 1160px; margin: 0 auto; padding: 24px 20px 40px; }

    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 24px;
    }
    .brand-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(66, 133, 244, 0.14);
      border: 1px solid rgba(66, 133, 244, 0.45);
      color: #93c5fd;
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      padding: 5px 12px;
      border-radius: 999px;
      margin-bottom: 10px;
    }
    .dots { display: inline-flex; gap: 4px; }
    .dots i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
    h1 {
      margin: 0;
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }
    .subtitle { color: var(--muted); margin-top: 6px; font-size: 0.96rem; }

    .actions { display: flex; gap: 10px; align-items: center; }
    .live-pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      font-size: 0.85rem;
      font-weight: 600;
      color: #86efac;
      background: rgba(52, 168, 83, 0.14);
      border: 1px solid rgba(52, 168, 83, 0.4);
      padding: 8px 12px;
      border-radius: 9px;
    }
    .pulse {
      width: 8px; height: 8px; border-radius: 50%; background: var(--g-green);
      box-shadow: 0 0 8px var(--g-green);
    }
    .btn {
      background: var(--surface);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 9px 15px;
      border-radius: 9px;
      cursor: pointer;
      font-weight: 700;
      font-size: 0.88rem;
    }
    .btn:hover { border-color: var(--g-blue); }
    .btn.frozen {
      background: rgba(234, 67, 53, 0.2);
      border-color: var(--g-red);
      color: #fecaca;
    }

    .freeze-banner {
      background: rgba(234, 67, 53, 0.16);
      border: 1px solid var(--g-red);
      color: #fecaca;
      padding: 12px 16px;
      border-radius: 10px;
      margin-bottom: 18px;
      font-weight: 700;
      display: none;
    }

    .vault-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .diamond-card {
      background: linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      position: relative;
      overflow: hidden;
    }
    .diamond-card.stolen-1 {
      border-color: var(--g-yellow);
      box-shadow: 0 0 28px rgba(251, 188, 4, 0.16);
    }
    .diamond-card.stolen-2 {
      border-color: var(--g-blue);
      box-shadow: 0 0 28px rgba(66, 133, 244, 0.18);
    }
    .gem-box {
      width: 58px;
      height: 58px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .diamond-label {
      font-size: 0.76rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .stolen-1 .diamond-label { color: var(--g-yellow); }
    .stolen-2 .diamond-label { color: #60a5fa; }
    .diamond-team { font-size: 1.32rem; font-weight: 800; }
    .diamond-meta { color: var(--muted); font-size: 0.85rem; margin-top: 4px; }

    .table-wrap {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
    }
    table { width: 100%; border-collapse: collapse; }
    th, td {
      padding: 13px 15px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      font-size: 0.93rem;
    }
    th {
      background: #0c1324;
      color: var(--muted);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 700;
    }
    tr:last-child td { border-bottom: none; }
    tr.row-d1 { background: rgba(251, 188, 4, 0.07); }
    tr.row-d2 { background: rgba(66, 133, 244, 0.07); }

    .lang-pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 700;
      background: rgba(148, 163, 184, 0.14);
      color: #e2e8f0;
    }
    .lang-C { background: rgba(66, 133, 244, 0.18); color: #93c5fd; }
    .lang-Python { background: rgba(251, 188, 4, 0.16); color: #fde047; }
    .lang-Java { background: rgba(234, 67, 53, 0.18); color: #fca5a5; }

    .progress-wrap {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 170px;
    }
    .bar {
      flex: 1;
      height: 8px;
      background: #1e293b;
      border-radius: 999px;
      overflow: hidden;
    }
    .bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--g-blue), var(--g-green));
      border-radius: 999px;
      transition: width 0.3s ease;
    }
    .status-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.76rem;
      font-weight: 800;
      letter-spacing: 0.04em;
    }
    .st-d1 { background: rgba(251, 188, 4, 0.18); color: var(--g-yellow); border: 1px solid rgba(251, 188, 4, 0.45); }
    .st-d2 { background: rgba(66, 133, 244, 0.18); color: #93c5fd; border: 1px solid rgba(66, 133, 244, 0.45); }
    .st-ok { background: rgba(52, 168, 83, 0.18); color: #86efac; border: 1px solid rgba(52, 168, 83, 0.45); }
    .st-wip { background: rgba(148, 163, 184, 0.12); color: var(--muted); }
  </style>
</head>
<body>
  <div class="google-strip"><span></span><span></span><span></span><span></span></div>
  <div class="container">
    <div class="header">
      <div>
        <div class="brand-pill">
          <span class="dots">
            <i style="background:var(--g-blue)"></i>
            <i style="background:var(--g-red)"></i>
            <i style="background:var(--g-yellow)"></i>
            <i style="background:var(--g-green)"></i>
          </span>
          GDG DevFest '26 Belagavi
        </div>
        <h1>Round 3 Finale: The Diamond Heist</h1>
        <div class="subtitle">Two DevFest Diamonds are in the vault. First two teams to breach all 7 security checks win!</div>
      </div>
      <div class="actions">
        <div class="live-pill"><span class="pulse"></span> LIVE SYNC (C / Python / Java)</div>
        <button id="freezeBtn" class="btn" onclick="toggleFreeze()">Freeze Board</button>
      </div>
    </div>

    <div id="freezeBanner" class="freeze-banner">
      BOARD FROZEN — Standings are locked for the final minutes of the heist!
    </div>

    <div id="vaultGrid" class="vault-grid"></div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Team</th>
            <th>Lang</th>
            <th>Vault Breach</th>
            <th>Core / Escape</th>
            <th>Clean</th>
            <th>Score</th>
            <th>Status</th>
            <th>Stolen At (UTC)</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>

  <script>
    function esc(s) {
      return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }
    function gemSvg(color, claimed) {
      const opacity = claimed ? '1' : '0.35';
      return `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" style="opacity:${opacity}">
        <path d="M6 3H18L22 9L12 21L2 9L6 3Z" stroke="${color}" stroke-width="1.8" fill="${color}" fill-opacity="${claimed ? '0.22' : '0.06'}"/>
        <path d="M2 9H22M12 21L8.5 9L10.5 3M12 21L15.5 9L13.5 3" stroke="${color}" stroke-width="1.3"/>
      </svg>`;
    }
    async function refresh() {
      const res = await fetch('/api/leaderboard');
      const data = await res.json();
      const btn = document.getElementById('freezeBtn');
      const banner = document.getElementById('freezeBanner');

      if (data.frozen) {
        btn.textContent = 'Unfreeze Board';
        btn.classList.add('frozen');
        banner.style.display = 'block';
      } else {
        btn.textContent = 'Freeze Board';
        btn.classList.remove('frozen');
        banner.style.display = 'none';
      }

      const d1 = data.rows.find(r => r.winner_badge === 'DIAMOND #1');
      const d2 = data.rows.find(r => r.winner_badge === 'DIAMOND #2');
      const slots = [
        { num: 1, winner: d1, cls: 'stolen-1', color: '#FBBC04' },
        { num: 2, winner: d2, cls: 'stolen-2', color: '#4285F4' },
      ];
      document.getElementById('vaultGrid').innerHTML = slots.map(s => {
        if (!s.winner) {
          return `<div class="diamond-card">
            <div class="gem-box">${gemSvg(s.color, false)}</div>
            <div>
              <div class="diamond-label">DevFest Diamond #${s.num} — IN VAULT</div>
              <div class="diamond-team" style="color:var(--muted)">Locked &amp; Guarded</div>
              <div class="diamond-meta">Pass 4 Core + 3 Escape tests to claim</div>
            </div>
          </div>`;
        }
        return `<div class="diamond-card ${s.cls}">
          <div class="gem-box">${gemSvg(s.color, true)}</div>
          <div>
            <div class="diamond-label">DevFest Diamond #${s.num} — STOLEN!</div>
            <div class="diamond-team">${esc(s.winner.team)}</div>
            <div class="diamond-meta">Lang: ${esc(s.winner.language)} | Score: ${s.winner.total_score} | ${esc(s.winner.completed_at)}</div>
          </div>
        </div>`;
      }).join('');

      const tbody = document.getElementById('tbody');
      if (!data.rows.length) {
        tbody.innerHTML = '<tr><td colspan="9" style="color:var(--muted)">Waiting for teams to save (Ctrl+S) or submit...</td></tr>';
        return;
      }
      tbody.innerHTML = data.rows.map(r => {
        const pct = r.tests_total > 0 ? Math.round((r.tests_passed / r.tests_total) * 100) : 0;
        const rowCls = r.winner_badge === 'DIAMOND #1' ? 'row-d1' : (r.winner_badge === 'DIAMOND #2' ? 'row-d2' : '');
        const stCls = r.winner_badge === 'DIAMOND #1' ? 'st-d1' :
                      (r.winner_badge === 'DIAMOND #2' ? 'st-d2' :
                      (r.winner_badge === 'BREACHED' ? 'st-ok' : 'st-wip'));
        const stText = r.winner_badge || 'BREACHING';
        const langCls = 'lang-' + esc(r.language);
        return `<tr class="${rowCls}">
          <td><strong>#${r.rank}</strong></td>
          <td><strong>${esc(r.team)}</strong></td>
          <td><span class="lang-pill ${langCls}">${esc(r.language)}</span></td>
          <td>
            <div class="progress-wrap">
              <div class="bar"><div class="bar-fill" style="width:${pct}%"></div></div>
              <span style="font-weight:700;font-size:0.84rem">${r.tests_passed}/${r.tests_total}</span>
            </div>
          </td>
          <td>Core ${r.core_passed}/${r.core_total} · Esc ${r.ext_passed}/${r.ext_total}</td>
          <td>${r.cleanliness.toFixed(1)}</td>
          <td><strong>${r.total_score.toFixed(1)}</strong></td>
          <td><span class="status-badge ${stCls}">${esc(stText)}</span></td>
          <td style="color:var(--muted);font-size:0.84rem">${r.completed_at ? esc(r.completed_at) : '-'}</td>
        </tr>`;
      }).join('');
    }
    async function toggleFreeze() {
      await fetch('/api/toggle-freeze', { method: 'POST' });
      refresh();
    }
    refresh();
    setInterval(refresh, 2000);
  </script>
</body>
</html>
"""


class BoardState:
    """Thread-safe holder for live submissions, judging lock, and frozen snapshot."""

    def __init__(
        self,
        data_file: Path,
        challenges_root: Path = DEFAULT_CHALLENGES_ROOT,
        challenge: str | None = None,
        frozen: bool = False,
        timeout: int = 5,
    ):
        self.data_file = data_file
        self.challenges_root = challenges_root
        self.challenge = challenge
        self.frozen = frozen
        self.timeout = timeout
        self._lock = threading.Lock()
        self._frozen_rows: list[dict] | None = None
        if frozen:
            self._frozen_rows = compute_standings(load_submissions(data_file), challenge)

    def get_snapshot(self) -> dict:
        with self._lock:
            if self.frozen:
                if self._frozen_rows is None:
                    self._frozen_rows = compute_standings(load_submissions(self.data_file), self.challenge)
                return {"frozen": True, "rows": self._frozen_rows}
            rows = compute_standings(load_submissions(self.data_file), self.challenge)
            return {"frozen": False, "rows": rows}

    def toggle_freeze(self) -> bool:
        with self._lock:
            self.frozen = not self.frozen
            if self.frozen:
                self._frozen_rows = compute_standings(load_submissions(self.data_file), self.challenge)
            else:
                self._frozen_rows = None
            return self.frozen

    def submit_code(self, team: str, filename: str, code: str) -> dict:
        with self._lock:
            return judge_code(
                team=team,
                filename=filename,
                code_text=code,
                challenge=self.challenge or "diamond_heist",
                challenges_root=self.challenges_root,
                data_file=self.data_file,
                timeout=self.timeout,
            )


def make_handler(state: BoardState):
    class DashboardHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def _send_json(self, status: int, obj: dict):
            payload = json.dumps(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path.startswith("/api/leaderboard"):
                self._send_json(200, state.get_snapshot())
                return

            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path == "/api/toggle-freeze":
                frozen = state.toggle_freeze()
                self._send_json(200, {"frozen": frozen})
                return

            if self.path == "/api/submit":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self._send_json(400, {"error": "Invalid Content-Length"})
                    return
                if length <= 0 or length > MAX_SUBMISSION_BYTES:
                    self._send_json(400, {"error": "Payload empty or too large"})
                    return
                try:
                    data = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._send_json(400, {"error": "Invalid JSON body"})
                    return

                team = str(data.get("team", "")).strip()
                filename = str(data.get("filename", "")).strip()
                code = data.get("code", "")
                if not team or not filename or not isinstance(code, str):
                    self._send_json(400, {"error": "Fields 'team', 'filename', and 'code' are required"})
                    return

                try:
                    rec = state.submit_code(team, filename, code)
                    self._send_json(200, rec)
                except ValueError as exc:
                    self._send_json(400, {"error": str(exc)})
                except Exception as exc:
                    self._send_json(500, {"error": str(exc)})
                return

            self.send_error(404)

    return DashboardHandler


def main():
    parser = argparse.ArgumentParser(description="DevFest 26 Belagavi live leaderboard & auto-sync server.")
    parser.add_argument("--data-file", default=str(DEFAULT_DATA_FILE), help="Path to submissions.json")
    parser.add_argument("--challenges-root", default=str(DEFAULT_CHALLENGES_ROOT), help="Path to devfest-round3-challenges")
    parser.add_argument("--challenge", default=None, help="Optional challenge filter")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (use 0.0.0.0 for Wi-Fi/LAN events)")
    parser.add_argument("--port", type=int, default=8080, help="HTTP port (default: 8080)")
    parser.add_argument("--timeout", type=int, default=5, help="Test timeout in seconds")
    parser.add_argument("--freeze", action="store_true", help="Start with the leaderboard frozen")
    parser.add_argument("--once", action="store_true", help="Print terminal leaderboard once and exit")
    args = parser.parse_args()

    state = BoardState(
        data_file=Path(args.data_file),
        challenges_root=Path(args.challenges_root),
        challenge=args.challenge,
        frozen=args.freeze,
        timeout=args.timeout,
    )
    snap = state.get_snapshot()
    print(render_terminal_table(snap["rows"], frozen=snap["frozen"]))

    if args.once:
        return

    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    print(f"\n[leaderboard] DevFest 26 Belagavi Dashboard: http://{args.host}:{args.port} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[leaderboard] Stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
