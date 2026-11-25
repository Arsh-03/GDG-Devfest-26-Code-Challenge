"""DevFest 26 Belagavi - Diamond Heist Vault Console (Python Reference Solution)."""

from collections import deque
import sys


def handle_escape(start_zone, exit_zone, at_time, current_time, guard_zone, alert_level, disabled):
    """Compute shortest safe escape route avoiding active sensors and guard patrol."""
    if at_time < current_time:
        return "ERR INVALID_TIME"
    if alert_level == 3:
        return "LOCKED"
    if not (0 <= start_zone < 4 and 0 <= exit_zone < 4):
        return "NO_PATH"

    blocked = {z for z in range(3) if disabled[z] == 0}
    guard_at = (guard_zone + (at_time - current_time)) % 4
    blocked.add(guard_at)

    if start_zone in blocked or exit_zone in blocked:
        return "NO_PATH"
    if start_zone == exit_zone:
        return f"PATH {start_zone}"

    adj = {
        0: [1, 2],
        1: [0, 3],
        2: [0, 3],
        3: [1, 2],
    }
    queue = deque([[start_zone]])
    visited = {start_zone}
    while queue:
        path = queue.popleft()
        curr = path[-1]
        for nxt in adj[curr]:
            if nxt in blocked or nxt in visited:
                continue
            new_path = path + [nxt]
            if nxt == exit_zone:
                return "PATH " + " ".join(str(z) for z in new_path)
            visited.add(nxt)
            queue.append(new_path)
    return "NO_PATH"


def main():
    """Run the vault security console reading commands from stdin."""
    disabled = [0, 0, 0]
    guard_zone = 0
    current_time = 0
    pass_expiry = -1
    alert_level = 0
    last_event_time = -1

    for raw_line in sys.stdin:
        parts = raw_line.strip().split()
        if not parts:
            continue
        cmd = parts[0]

        if cmd == "EXIT":
            break
        elif cmd == "DISABLE":
            sensor_id = int(parts[1])
            if sensor_id < 0 or sensor_id >= 3:
                print("ERR INVALID_SENSOR")
            else:
                disabled[sensor_id] = 1
                print(f"DISABLED {sensor_id}")
        elif cmd == "WAIT":
            steps = int(parts[1])
            if steps < 0:
                print("ERR INVALID_TIME")
            else:
                current_time += steps
                guard_zone = (guard_zone + steps) % 4
                print(f"GUARD {guard_zone} TIME {current_time}")
        elif cmd == "GRANT_PASS":
            pass_expiry = int(parts[1])
            print(f"PASS_SET {pass_expiry}")
        elif cmd == "TRIGGER":
            sensor_id = int(parts[1])
            at_time = int(parts[2])
            severity = int(parts[3])
            if pass_expiry != -1 and at_time < pass_expiry:
                print("SUPPRESSED")
            elif 0 <= sensor_id < 3 and disabled[sensor_id] == 1:
                print("IGNORED")
            else:
                if at_time == last_event_time:
                    if severity > alert_level:
                        alert_level = severity
                else:
                    alert_level = severity
                    last_event_time = at_time
                print(f"ALERT {alert_level}")
        elif cmd == "ESCAPE":
            start_zone = int(parts[1])
            exit_zone = int(parts[2])
            at_time = int(parts[3])
            print(handle_escape(start_zone, exit_zone, at_time, current_time, guard_zone, alert_level, disabled))


if __name__ == "__main__":
    main()
