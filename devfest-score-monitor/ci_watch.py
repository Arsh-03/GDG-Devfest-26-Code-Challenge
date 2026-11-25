"""Folder-watcher CI pipeline for DevFest 26 Belagavi Diamond Heist submissions."""

import argparse
import hashlib
import time
from pathlib import Path

from runner import (
    DEFAULT_CHALLENGES_ROOT,
    DEFAULT_DATA_FILE,
    find_submission_file,
    judge_submission,
)


def file_digest(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_submissions(submissions_root: Path) -> list[tuple[str, Path]]:
    """Find (team_name, starter_file_path) pairs under `<submissions_root>/<team>/`."""
    found = []
    if not submissions_root.is_dir():
        return found

    for entry in sorted(submissions_root.iterdir()):
        if not entry.is_dir():
            continue
        try:
            starter = find_submission_file(entry)
            found.append((entry.name, starter))
        except FileNotFoundError:
            continue
    return found


def watch_loop(
    submissions_root: Path,
    challenge: str = "diamond_heist",
    interval: float = 2.0,
    challenges_root: Path = DEFAULT_CHALLENGES_ROOT,
    data_file: Path = DEFAULT_DATA_FILE,
    timeout: int = 5,
    once: bool = False,
):
    """Poll `submissions_root` for new or modified C/Python/Java files and judge them."""
    seen: dict[str, str] = {}
    print(f"[ci_watch] Watching '{submissions_root}' every {interval}s (C / Python / Java)...")

    while True:
        for team, starter_path in discover_submissions(submissions_root):
            try:
                digest = file_digest(starter_path)
            except OSError:
                continue

            if seen.get(team) != digest:
                seen[team] = digest
                print(f"[ci_watch] Detected {starter_path.name} from '{team}' -> judging...")
                try:
                    rec = judge_submission(
                        team=team,
                        submission_path=starter_path,
                        challenge=challenge,
                        challenges_root=challenges_root,
                        data_file=data_file,
                        timeout=timeout,
                    )
                    core = rec["core"]
                    ext = rec["extension"]
                    status = "DIAMOND STOLEN!" if rec["completed_all"] else "BREACHING"
                    print(
                        f"[ci_watch] {team} [{rec['language']}]: {status} | "
                        f"Core {core['passed']}/{core['total']} | "
                        f"Escape {ext['passed']}/{ext['total']} | "
                        f"Score {rec['total_score']}"
                    )
                except Exception as exc:
                    print(f"[ci_watch] Error judging '{team}': {exc}")

        if once:
            break
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Watch team folders and run runner.py automatically.")
    parser.add_argument("--submissions-root", required=True, help="Root folder containing team subfolders")
    parser.add_argument("--challenge", default="diamond_heist", help="Challenge identifier (default: diamond_heist)")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds (default: 2)")
    parser.add_argument("--challenges-root", default=str(DEFAULT_CHALLENGES_ROOT), help="Path to devfest-round3-challenges")
    parser.add_argument("--data-file", default=str(DEFAULT_DATA_FILE), help="Path to submissions.json")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout per test case in seconds")
    parser.add_argument("--once", action="store_true", help="Scan once and exit")
    args = parser.parse_args()

    try:
        watch_loop(
            submissions_root=Path(args.submissions_root),
            challenge=args.challenge,
            interval=args.interval,
            challenges_root=Path(args.challenges_root),
            data_file=Path(args.data_file),
            timeout=args.timeout,
            once=args.once,
        )
    except KeyboardInterrupt:
        print("\n[ci_watch] Stopped.")


if __name__ == "__main__":
    main()
