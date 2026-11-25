"""Simulate a 5-team multi-language DevFest 26 Belagavi Diamond Heist race."""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from leaderboard import compute_standings, load_submissions, render_terminal_table
from runner import DEFAULT_CHALLENGES_ROOT, DEFAULT_DATA_FILE, judge_code


def build_core_only_python(ref_source: str) -> str:
    """Replace ESCAPE handling with ERR NOT_IMPLEMENTED to simulate core-only fix."""
    return ref_source.replace(
        "print(handle_escape(start_zone, exit_zone, at_time, current_time, guard_zone, alert_level, disabled))",
        'print("ERR NOT_IMPLEMENTED")',
    )


def simulate(
    challenges_root: Path = DEFAULT_CHALLENGES_ROOT,
    data_file: Path = DEFAULT_DATA_FILE,
    reset: bool = True,
):
    """Create 5 mock team submissions across C and Python at staggered timestamps."""
    c_starter = (challenges_root / "c" / "starter.c").read_text(encoding="utf-8")
    c_ref = (challenges_root / "c" / "reference_solution.c").read_text(encoding="utf-8")
    py_ref = (challenges_root / "python" / "reference_solution.py").read_text(encoding="utf-8")

    if reset and data_file.is_file():
        data_file.unlink()

    base_time = datetime(2026, 11, 25, 14, 0, 0, tzinfo=timezone.utc)

    # 5 teams racing in C and Python
    mock_teams = [
        ("BelagaviCoders", "starter.py", base_time + timedelta(minutes=6), build_core_only_python(py_ref)),
        ("CyberPhantoms", "starter.c", base_time + timedelta(minutes=11), c_ref),
        ("VaultBreakers", "starter.py", base_time + timedelta(minutes=14), py_ref + "\n# debug note\n"),
        ("SegFaultSquad", "starter.c", base_time + timedelta(minutes=16), c_starter),
        ("KLETechHackers", "starter.c", base_time + timedelta(minutes=19), c_ref),
    ]

    for team, fname, ts, code in mock_teams:
        rec = judge_code(
            team=team,
            filename=fname,
            code_text=code,
            challenge="diamond_heist",
            challenges_root=challenges_root,
            data_file=data_file,
            completed_at_override=ts.isoformat(),
        )
        print(
            f"[simulate] {team:<16} [{rec['language']:<6}] | "
            f"Core {rec['core']['passed']}/{rec['core']['total']} | "
            f"Escape {rec['extension']['passed']}/{rec['extension']['total']} | "
            f"Score {rec['total_score']}"
        )

    print()
    rows = compute_standings(load_submissions(data_file))
    print(render_terminal_table(rows))


def main():
    parser = argparse.ArgumentParser(description="Simulate a 5-team DevFest 26 Belagavi Diamond Heist.")
    parser.add_argument("--challenges-root", default=str(DEFAULT_CHALLENGES_ROOT))
    parser.add_argument("--data-file", default=str(DEFAULT_DATA_FILE))
    parser.add_argument("--no-reset", action="store_true", help="Append instead of resetting submissions.json")
    args = parser.parse_args()

    simulate(
        challenges_root=Path(args.challenges_root),
        data_file=Path(args.data_file),
        reset=not args.no_reset,
    )


if __name__ == "__main__":
    main()
