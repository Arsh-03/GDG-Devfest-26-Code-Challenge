# GDG DevFest '26 Belagavi — Round 3 Score Monitor

Multi-language (`C`, `Python`, `Java`) judging pipeline, `Ctrl+S` auto-sync agent, and live **DevFest '26 Belagavi: The Diamond Heist** scoreboard.

## How Winning Works
- Two **DevFest Diamonds** are locked in the vault.
- The **first two teams** to pass all **4 Core + 3 Escape (`7/7`)** tests claim **DIAMOND #1** and **DIAMOND #2**!
- Score breakdown (100 pts):
  - **Core Bugs (40 pts)**: 4 tests (`10` pts each)
  - **Escape Route Extension (30 pts)**: 3 tests (`10` pts each)
  - **Code Cleanliness (20 pts)**: style/syntax checks (plus `--cleanliness-override`)
  - **Vault Breach Bonus (10 pts)**: awarded when `7/7` tests pass

---

## 1. Dry Run Simulation (`simulate_race.py`)
Runs 5 mock teams across `C` and `Python` and populates `data/submissions.json`:

```bash
cd devfest-score-monitor
python simulate_race.py
```

## 2. Start the DevFest '26 Belagavi Live Dashboard (`leaderboard.py` or Streamlit)
Starts the projector web UI (`http://localhost:8080`) AND listens for live `Ctrl+S` submissions (`POST /api/submit`):

```bash
cd devfest-score-monitor
python leaderboard.py --host 0.0.0.0 --port 8080
```
*(Use `--host 0.0.0.0` so participant laptops on event Wi-Fi can auto-sync to `http://<JUDGE-IP>:8080`. Add `--freeze` or click **Freeze Board** in the UI during the final minutes.)*

### Optional: Streamlit Projector UI (`streamlit_app.py`)
Keep `leaderboard.py --host 0.0.0.0 --port 8080` running in Terminal 1 to receive `sync.py` submissions, and launch the Streamlit dashboard in Terminal 2:
```bash
cd devfest-score-monitor
streamlit run streamlit_app.py
```

## 3. Participant `Ctrl+S` Auto-Sync (`team_sync.py`)
Share `team_sync.py` with students. They run it once in their terminal, then simply edit `starter.c` / `starter.py` / `Starter.java` in any IDE and press **`Ctrl+S`**:

```bash
python team_sync.py --team ByteBuilders --file path/to/starter.c --server http://<JUDGE-IP>:8080
```

## 4. Manual Judging (`runner.py`) & Folder Watching (`ci_watch.py`)
Judge a single file directly:
```bash
python runner.py --team ByteBuilders --file ../devfest-round3-challenges/c/reference_solution.c
```

Watch a shared submissions folder (`<root>/<team>/starter.c|py|Starter.java`):
```bash
python ci_watch.py --submissions-root ./submissions --interval 2
```

> **Note for Java teams:** Ensure a JDK (`javac` + `java`) is on `PATH` on the judge laptop (`gcc` is used for C, `python` for Python).
