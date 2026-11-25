"""DevFest 26 Belagavi - Diamond Heist Vault Console (Python Starter)."""

import sys


def main():
    """Run the vault security console reading commands from stdin."""
    disabled = [0, 0, 0]  # 0: Lobby, 1: Laser Hall, 2: Vent Shaft
    guard_zone = 0         # 4-zone loop: 0 -> 1 -> 2 -> 3 -> 0
    current_time = 0
    pass_expiry = -1
    alert_level = 0        # 0=CLEAR, 1=LOW, 2=HIGH, 3=CRITICAL
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
                sensor_id = 0
            disabled[sensor_id] = 1
            print(f"DISABLED {sensor_id}")
        elif cmd == "WAIT":
            steps = int(parts[1])
            if steps < 0:
                print("ERR INVALID_TIME")
            else:
                current_time += steps
                guard_zone = (guard_zone + steps) % 3
                print(f"GUARD {guard_zone} TIME {current_time}")
        elif cmd == "GRANT_PASS":
            pass_expiry = int(parts[1])
            print(f"PASS_SET {pass_expiry}")
        elif cmd == "TRIGGER":
            sensor_id = int(parts[1])
            at_time = int(parts[2])
            severity = int(parts[3])
            if pass_expiry != -1 and at_time <= pass_expiry:
                print("SUPPRESSED")
            elif 0 <= sensor_id < 3 and disabled[sensor_id] == 1:
                print("IGNORED")
            else:
                alert_level = severity
                last_event_time = at_time
                print(f"ALERT {alert_level}")
        elif cmd == "ESCAPE":
            print("ERR NOT_IMPLEMENTED")


if __name__ == "__main__":
    main()
