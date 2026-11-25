"""Auto-sync client (Ctrl+S) for C participants — DevFest 26 Belagavi Diamond Heist."""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent / "starter.c"


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def submit_file(server_url: str, team: str, file_path: Path) -> dict:
    url = server_url.rstrip("/") + "/api/submit"
    payload = json.dumps({
        "team": team,
        "filename": file_path.name,
        "code": file_path.read_text(encoding="utf-8"),
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_feedback(rec: dict) -> str:
    core, ext = rec["core"], rec["extension"]
    lang = rec.get("language", "C")
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


def main():
    parser = argparse.ArgumentParser(description="Auto-sync starter.c on Ctrl+S to the DevFest 26 scoreboard.")
    parser.add_argument("--team", required=True, help="Your team name")
    parser.add_argument("--server", default="http://127.0.0.1:8080", help="Judge server URL (e.g., http://192.168.1.10:8080)")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="Path to starter.c")
    parser.add_argument("--interval", type=float, default=0.5, help="Poll interval in seconds")
    parser.add_argument("--once", action="store_true", help="Submit once and exit")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.is_file():
        print(f"[sync] File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[sync] Team: {args.team} | Watching: {file_path.name}")
    print(f"[sync] Server: {args.server} | Hit Ctrl+S in your IDE to test & update scoreboard!\n")

    last_hash = None
    try:
        while True:
            current_hash = file_digest(file_path)
            if current_hash != last_hash:
                last_hash = current_hash
                ts = time.strftime("%H:%M:%S")
                try:
                    rec = submit_file(args.server, args.team, file_path)
                    print(f"[{ts}] Synced! {format_feedback(rec)}\n")
                except urllib.error.HTTPError as exc:
                    print(f"[{ts}] Server error ({exc.code}): {exc.read().decode('utf-8', errors='replace')}\n")
                except urllib.error.URLError as exc:
                    print(f"[{ts}] Cannot reach judge server ({exc.reason}). Retrying on next save...\n")
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[sync] Disconnected.")


if __name__ == "__main__":
    main()
