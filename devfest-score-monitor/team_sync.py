"""Auto-sync client (Ctrl+S) for DevFest 26 Belagavi Diamond Heist participants."""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def file_digest(path: Path) -> str:
    """Compute SHA-256 hex digest of the watched source file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def submit_file(server_url: str, team: str, file_path: Path) -> dict:
    """POST the source file to the judge server's /api/submit endpoint."""
    url = server_url.rstrip("/") + "/api/submit"
    payload = json.dumps({
        "team": team,
        "filename": file_path.name,
        "code": file_path.read_text(encoding="utf-8"),
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_feedback(rec: dict) -> str:
    """Format concise live test results for the participant's terminal."""
    core = rec["core"]
    ext = rec["extension"]
    lang = rec.get("language", "?")
    if rec.get("compile_error"):
        return f"[{lang}] COMPILE ERROR -> {rec['compile_error']}"

    badge = "DIAMOND STOLEN! Vault Breached!" if rec["completed_all"] else "BREACHING VAULT"
    lines = [
        f"[{lang}] {badge} | Core: {core['passed']}/{core['total']} | "
        f"Escape: {ext['passed']}/{ext['total']} | Score: {rec['total_score']}"
    ]
    for d in core.get("details", []) + ext.get("details", []):
        lines.append(f"   x {d['test']}: {d['error']}")
    return "\n".join(lines)


def watch_and_sync(team: str, file_path: Path, server_url: str, interval: float = 0.5, once: bool = False):
    """Watch `file_path` and auto-submit on every save (Ctrl+S)."""
    if not file_path.is_file():
        print(f"[team_sync] File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[team_sync] Team: {team} | Watching: {file_path}")
    print(f"[team_sync] Judge Server: {server_url}")
    print("[team_sync] Hit Ctrl+S in your IDE to test & update the live scoreboard!\n")

    last_hash = None
    while True:
        try:
            current_hash = file_digest(file_path)
            if current_hash != last_hash:
                last_hash = current_hash
                ts = time.strftime("%H:%M:%S")
                try:
                    rec = submit_file(server_url, team, file_path)
                    print(f"[{ts}] Synced! {format_feedback(rec)}\n")
                except urllib.error.HTTPError as exc:
                    body = exc.read().decode("utf-8", errors="replace")
                    print(f"[{ts}] Server rejected submission ({exc.code}): {body}\n")
                except urllib.error.URLError as exc:
                    print(f"[{ts}] Could not reach judge server ({exc.reason}). Retrying on next save...\n")
        except OSError as exc:
            print(f"[team_sync] Read error: {exc}")

        if once:
            break
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Auto-sync your starter file on Ctrl+S to the DevFest 26 Belagavi scoreboard.")
    parser.add_argument("--team", required=True, help="Your registered team name")
    parser.add_argument("--file", required=True, help="Path to your starter.c, starter.py, or Starter.java")
    parser.add_argument("--server", default="http://127.0.0.1:8080", help="Judge server URL (e.g., http://192.168.1.10:8080)")
    parser.add_argument("--interval", type=float, default=0.5, help="Poll interval in seconds (default: 0.5)")
    parser.add_argument("--once", action="store_true", help="Submit once and exit")
    args = parser.parse_args()

    try:
        watch_and_sync(
            team=args.team,
            file_path=Path(args.file),
            server_url=args.server,
            interval=args.interval,
            once=args.once,
        )
    except KeyboardInterrupt:
        print("\n[team_sync] Disconnected.")


if __name__ == "__main__":
    main()
