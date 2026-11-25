"""Multi-language CLI test-runner & scorer for DevFest 26 Belagavi Diamond Heist."""

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CHALLENGES_ROOT = Path(__file__).resolve().parent.parent / "devfest-round3-challenges"
DEFAULT_DATA_FILE = Path(__file__).resolve().parent / "data" / "submissions.json"

SUPPORTED_FILENAMES = ("starter.py", "starter.c", "Starter.java")


def detect_language(filename: str) -> str:
    """Map starter filename or extension to canonical language label."""
    ext = Path(filename).suffix.lower()
    if ext == ".py":
        return "Python"
    if ext == ".c":
        return "C"
    if ext == ".java":
        return "Java"
    raise ValueError(f"Unsupported file type '{filename}'. Use .py, .c, or .java.")


def find_submission_file(submission_dir: Path) -> Path:
    """Locate starter.py, starter.c, or Starter.java inside `submission_dir`."""
    for name in SUPPORTED_FILENAMES:
        candidate = submission_dir / name
        if candidate.is_file():
            return candidate
    for ext in ("*.py", "*.c", "*.java"):
        matches = sorted(submission_dir.glob(ext))
        if matches:
            return matches[0]
    raise FileNotFoundError(
        f"No starter.py, starter.c, or Starter.java found in {submission_dir}"
    )


def compile_submission(work_dir: Path, source_path: Path, lang: str, timeout: int) -> tuple[list[str] | None, str | None]:
    """Compile C or Java if needed; return (run_cmd, error_message)."""
    if lang == "Python":
        return [sys.executable, source_path.name], None

    if lang == "C":
        gcc = shutil.which("gcc")
        if not gcc:
            return None, "gcc compiler not found on PATH."
        out_name = "vault_bin.exe" if os.name == "nt" else "./vault_bin"
        out_path = work_dir / ("vault_bin.exe" if os.name == "nt" else "vault_bin")
        try:
            proc = subprocess.run(
                [gcc, "-O2", source_path.name, "-o", out_path.name],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=max(timeout, 10),
            )
        except subprocess.TimeoutExpired:
            return None, "C compilation timed out."
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout).strip().splitlines()[:4]
            return None, "Compile error: " + " | ".join(err)
        return [str(out_path) if os.name == "nt" else out_name], None

    if lang == "Java":
        javac = shutil.which("javac")
        java = shutil.which("java")
        if not javac or not java:
            return None, "JDK (javac/java) not found on PATH."
        try:
            proc = subprocess.run(
                [javac, source_path.name],
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=max(timeout, 15),
            )
        except subprocess.TimeoutExpired:
            return None, "Java compilation timed out."
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout).strip().splitlines()[:4]
            return None, "Compile error: " + " | ".join(err)
        class_name = source_path.stem
        return [java, "-cp", ".", class_name], None

    return None, f"Unsupported language: {lang}"


def run_cases(work_dir: Path, run_cmd: list[str], cases: list[dict], timeout: int) -> dict:
    """Execute stdin/stdout test cases against the compiled/interpreted program."""
    total = len(cases)
    passed = 0
    failed = 0
    errors = 0
    timed_out = False
    details = []

    for case in cases:
        name = case["name"]
        stdin_data = case["input"]
        expected = [line.strip() for line in case["expected"]]
        try:
            proc = subprocess.run(
                run_cmd,
                cwd=str(work_dir),
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            timed_out = True
            errors += 1
            details.append({"test": name, "error": f"Timed out after {timeout}s"})
            continue

        if proc.returncode != 0:
            errors += 1
            err_line = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else f"Exit code {proc.returncode}"
            details.append({"test": name, "error": err_line})
            continue

        actual = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if actual == expected:
            passed += 1
        else:
            failed += 1
            details.append({
                "test": name,
                "error": f"Expected {expected}, got {actual}",
            })

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "timed_out": timed_out,
        "details": details,
    }


def evaluate_cleanliness(source_path: Path, lang: str) -> dict:
    """Compute a 0-20 code cleanliness score for Python, C, or Java."""
    try:
        source = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"score": 0.0, "notes": [f"Cannot read file: {exc}"]}

    notes = []
    score = 20.0

    if lang == "Python":
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return {"score": 0.0, "notes": [f"SyntaxError: {exc.msg} (line {exc.lineno})"]}
        debug_prints = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and any("debug" in ast.unparse(a).lower() for a in node.args)
        )
        if debug_prints > 0:
            penalty = min(6.0, debug_prints * 2.0)
            score -= penalty
            notes.append(f"Found {debug_prints} debug print() call(s) (-{penalty:.0f})")

        bare_excepts = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.ExceptHandler) and node.type is None
        )
        if bare_excepts > 0:
            penalty = min(4.0, bare_excepts * 2.0)
            score -= penalty
            notes.append(f"Found {bare_excepts} bare except clause(s) (-{penalty:.0f})")
    else:
        lower = source.lower()
        debug_hits = lower.count("debug")
        if debug_hits > 0:
            penalty = min(4.0, debug_hits * 2.0)
            score -= penalty
            notes.append(f"Found {debug_hits} debug marker(s) (-{penalty:.0f})")

    long_lines = sum(1 for line in source.splitlines() if len(line) > 120)
    if long_lines > 0:
        penalty = min(4.0, float(long_lines))
        score -= penalty
        notes.append(f"{long_lines} line(s) exceed 120 chars (-{penalty:.0f})")

    if not notes:
        notes.append(f"Clean {lang} code, well formatted.")
    return {"score": max(0.0, round(score, 2)), "notes": notes}


def judge_code(
    team: str,
    filename: str,
    code_text: str,
    challenge: str = "diamond_heist",
    challenges_root: Path = DEFAULT_CHALLENGES_ROOT,
    data_file: Path = DEFAULT_DATA_FILE,
    timeout: int = 5,
    cleanliness_override: float | None = None,
    completed_at_override: str | None = None,
) -> dict:
    """Judge a source string (`starter.py`, `starter.c`, or `Starter.java`) and log to submissions.json."""
    lang = detect_language(filename)
    tests_dir = challenges_root / "tests"
    core_file = tests_dir / "core_cases.json"
    ext_file = tests_dir / "extension_cases.json"
    if not core_file.is_file() or not ext_file.is_file():
        raise FileNotFoundError(f"Official test cases missing in {tests_dir}")

    core_cases = json.loads(core_file.read_text(encoding="utf-8"))
    ext_cases = json.loads(ext_file.read_text(encoding="utf-8"))

    target_name = "Starter.java" if lang == "Java" else Path(filename).name

    with tempfile.TemporaryDirectory(prefix=f"heist_{team}_") as tmp:
        work_dir = Path(tmp)
        src_path = work_dir / target_name
        src_path.write_text(code_text, encoding="utf-8")

        cleanliness = evaluate_cleanliness(src_path, lang)
        run_cmd, compile_err = compile_submission(work_dir, src_path, lang, timeout)

        if compile_err is not None or run_cmd is None:
            core_res = {
                "total": len(core_cases),
                "passed": 0,
                "failed": 0,
                "errors": len(core_cases),
                "timed_out": False,
                "details": [{"test": "compile", "error": compile_err}],
            }
            ext_res = {
                "total": len(ext_cases),
                "passed": 0,
                "failed": 0,
                "errors": len(ext_cases),
                "timed_out": False,
                "details": [{"test": "compile", "error": compile_err}],
            }
            clean_score = 0.0
        else:
            core_res = run_cases(work_dir, run_cmd, core_cases, timeout)
            ext_res = run_cases(work_dir, run_cmd, ext_cases, timeout)
            clean_score = (
                max(0.0, min(20.0, float(cleanliness_override)))
                if cleanliness_override is not None
                else cleanliness["score"]
            )

    core_total = core_res["total"]
    core_passed = core_res["passed"]
    ext_total = ext_res["total"]
    ext_passed = ext_res["passed"]

    core_pts = round(40.0 * (core_passed / core_total), 2) if core_total > 0 else 0.0
    ext_pts = round(30.0 * (ext_passed / ext_total), 2) if ext_total > 0 else 0.0

    completed_all = (
        core_total > 0
        and ext_total > 0
        and core_passed == core_total
        and ext_passed == ext_total
    )
    speed_bonus = 10.0 if completed_all else 0.0
    total_score = round(core_pts + ext_pts + clean_score + speed_bonus, 2)

    now_iso = datetime.now(timezone.utc).isoformat()
    completed_at = (completed_at_override or now_iso) if completed_all else None

    record = {
        "team": team,
        "challenge": challenge,
        "language": lang,
        "filename": target_name,
        "submitted_at": completed_at_override or now_iso,
        "completed_all": completed_all,
        "completed_at": completed_at,
        "compile_error": compile_err,
        "core": {
            "passed": core_passed,
            "total": core_total,
            "failed": core_res["failed"],
            "errors": core_res["errors"],
            "timed_out": core_res["timed_out"],
            "score": core_pts,
            "details": core_res["details"],
        },
        "extension": {
            "passed": ext_passed,
            "total": ext_total,
            "failed": ext_res["failed"],
            "errors": ext_res["errors"],
            "timed_out": ext_res["timed_out"],
            "score": ext_pts,
            "details": ext_res["details"],
        },
        "cleanliness": {
            "score": clean_score,
            "override": cleanliness_override is not None,
            "notes": cleanliness["notes"],
        },
        "speed_bonus": speed_bonus,
        "total_score": total_score,
    }

    data_file.parent.mkdir(parents=True, exist_ok=True)
    if data_file.is_file():
        try:
            existing = json.loads(data_file.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except json.JSONDecodeError:
            existing = []
    else:
        existing = []

    existing.append(record)
    data_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return record


def judge_submission(
    team: str,
    submission_path: Path,
    challenge: str = "diamond_heist",
    challenges_root: Path = DEFAULT_CHALLENGES_ROOT,
    data_file: Path = DEFAULT_DATA_FILE,
    timeout: int = 5,
    cleanliness_override: float | None = None,
    completed_at_override: str | None = None,
) -> dict:
    """Judge either a specific starter file or a directory containing one."""
    src_file = find_submission_file(submission_path) if submission_path.is_dir() else submission_path
    if not src_file.is_file():
        raise FileNotFoundError(f"Submission file not found: {src_file}")

    code_text = src_file.read_text(encoding="utf-8")
    return judge_code(
        team=team,
        filename=src_file.name,
        code_text=code_text,
        challenge=challenge,
        challenges_root=challenges_root,
        data_file=data_file,
        timeout=timeout,
        cleanliness_override=cleanliness_override,
        completed_at_override=completed_at_override,
    )


def main():
    parser = argparse.ArgumentParser(description="Run and score a DevFest 26 Belagavi Diamond Heist submission.")
    parser.add_argument("--team", required=True, help="Team name or ID")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to team's starter.c, starter.py, or Starter.java")
    group.add_argument("--submission-dir", help="Directory containing team's starter file")
    parser.add_argument("--challenge", default="diamond_heist", help="Challenge identifier (default: diamond_heist)")
    parser.add_argument("--challenges-root", default=str(DEFAULT_CHALLENGES_ROOT), help="Path to devfest-round3-challenges")
    parser.add_argument("--data-file", default=str(DEFAULT_DATA_FILE), help="Path to submissions.json")
    parser.add_argument("--timeout", type=int, default=5, help="Timeout in seconds per test case")
    parser.add_argument("--cleanliness-override", type=float, default=None, help="Judge override for cleanliness (0-20)")
    args = parser.parse_args()

    target = Path(args.file) if args.file else Path(args.submission_dir)
    record = judge_submission(
        team=args.team,
        submission_path=target,
        challenge=args.challenge,
        challenges_root=Path(args.challenges_root),
        data_file=Path(args.data_file),
        timeout=args.timeout,
        cleanliness_override=args.cleanliness_override,
    )
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
