# Extension Spec: `ESCAPE <start_zone> <exit_zone> <at_time>` (Steal the Diamond)

Once you fix all 4 security bugs in `starter.c` / `starter.py` / `Starter.java`, implement the `ESCAPE` command to extract a **DevFest Diamond** from the vault!

## Vault Map (4 Zones)
```
  [0: Lobby] ---- [1: Laser Hall]
      |                  |
      |                  |
  [2: Vent Shaft] -- [3: Diamond Vault Exit]
```
- Adjacent connections (undirected):
  - `0` <-> `1`, `2`
  - `1` <-> `0`, `3`
  - `2` <-> `0`, `3`
  - `3` <-> `1`, `2`

## Rules for `ESCAPE <start_zone> <exit_zone> <at_time>`
1. **Past time check**: If `at_time < current_time`, print `ERR INVALID_TIME`.
2. **Critical lockdown**: If `alert_level == 3`, print `LOCKED`.
3. **Blocked zones at `at_time`**:
   - Any zone `z` in `{0, 1, 2}` whose laser sensor is still active (`disabled[z] == 0`) is **blocked**. (Zone `3` has no laser sensor.)
   - The guard's position at `at_time` is `(guard_zone + (at_time - current_time)) % 4`, which is also **blocked**.
4. **Shortest safe path (BFS)**:
   - Explore neighbors in ascending numeric order (`0, 1, 2, 3`).
   - If `start_zone` or `exit_zone` is out of `0..3`, blocked, or unreachable, print `NO_PATH`.
   - Otherwise print `PATH <z0> <z1> ...` (for example: `PATH 0 2 3`).
