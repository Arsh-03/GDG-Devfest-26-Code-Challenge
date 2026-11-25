# DevFest 26 Belagavi — Round 3: The Diamond Heist

Two **DevFest Diamonds** are locked inside the vault. The **first two teams** to patch all 4 security flaws and implement the escape route (`7/7` tests passed) steal the two diamonds and win!

## Choose Your Language
Pick **one** folder and edit only its starter file:
- **C**: `c/starter.c`
- **Python**: `python/starter.py`
- **Java**: `java/Starter.java`

## Command Protocol (Reads from `stdin`, Writes to `stdout`)
- `DISABLE <sensor_id> <time>` -> Disables sensor `0`, `1`, or `2` (`DISABLED <id>` or `ERR INVALID_SENSOR`)
- `WAIT <steps>` -> Advances time and moves guard on 4-zone loop `0 -> 1 -> 2 -> 3 -> 0` (`GUARD <zone> TIME <time>`)
- `GRANT_PASS <expires_at>` -> Grants silent pass valid strictly while `time < expires_at` (`PASS_SET <expires_at>`)
- `TRIGGER <sensor_id> <time> <severity>` -> Evaluates pass, disabled sensor, or updates `alert_level` (`SUPPRESSED` / `IGNORED` / `ALERT <level>`)
- `ESCAPE <start_zone> <exit_zone> <at_time>` -> *(Extension)* See `extension_spec.md`
- `EXIT` -> Exits cleanly

## Live Auto-Sync (`Ctrl+S` to Judge!)
Open a terminal inside your chosen language folder (`c/`, `python/`, or `java/`), start `sync.py` once, and then edit your starter file in any IDE (VS Code, Code::Blocks, IntelliJ, etc.)—every **`Ctrl+S`** submits live:
```bash
# Example for C:
cd c
python sync.py --team YourTeamName --server http://<JUDGE-IP>:8080
```
*(In `python/` it watches `starter.py`; in `java/` it watches `Starter.java`.)*
