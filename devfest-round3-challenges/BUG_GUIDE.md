# Judge & Organizer Bug Guide — DevFest 26 Belagavi Diamond Heist (CONFIDENTIAL)

There are **4 planted bugs** (2 Easy, 1 Medium, 1 Tricky) identical across `c/starter.c`, `python/starter.py`, and `java/Starter.java`, plus **1 extension feature** (`ESCAPE`).

---

## Planted Bugs

1. **Bug 1 (Easy) — Invalid Sensor Clamping (`DISABLE`)**
   - *Symptom*: When `sensor_id < 0` or `sensor_id >= 3` (e.g., `DISABLE 9 1`), `starter` clamps `sensor_id = 0` and disables sensor `0` instead of rejecting it.
   - *Fix*: Print `ERR INVALID_SENSOR` and do not modify `disabled[]`.

2. **Bug 2 (Easy) — Wrong Guard Patrol Loop (`WAIT`)**
   - *Symptom*: Uses `% 3` instead of `% 4` (`guard_zone = (guard_zone + steps) % 3`), skipping Zone `3` (the Diamond Vault).
   - *Fix*: Use `% 4`.

3. **Bug 3 (Medium) — Off-by-One Pass Expiry (`TRIGGER`)**
   - *Symptom*: Uses `at_time <= pass_expiry` instead of `at_time < pass_expiry`, allowing an expired pass to suppress an alarm right at `at_time == pass_expiry`.
   - *Fix*: Change `<=` to `<`.

4. **Bug 4 (Tricky) — Simultaneous Alert Overwrite (`TRIGGER`)**
   - *Symptom*: Unconditionally assigns `alert_level = severity`, so a `LOW` (`1`) event in the same timestamp overwrites a `CRITICAL` (`3`) alert.
   - *Fix*: If `at_time == last_event_time`, only update `alert_level` when `severity > alert_level`.

---

## Extension (`ESCAPE <start_zone> <exit_zone> <at_time>`)
- See `extension_spec.md` and `tests/extension_cases.json`.
- First **2 teams** to pass all **4 Core + 3 Extension** tests (`7/7`) claim the **2 DevFest 26 Belagavi Diamonds**!
