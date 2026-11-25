#include <stdio.h>
#include <string.h>

/*
 * DevFest 26 Belagavi - Diamond Heist Vault Console (C Starter)
 *
 * Sensors: 0 = Lobby, 1 = Laser Hall, 2 = Vent Shaft (0 = active, 1 = disabled)
 * Guard patrol loop: 4 zones (0 -> 1 -> 2 -> 3 -> 0)
 * Alert levels: 0 = CLEAR, 1 = LOW, 2 = HIGH, 3 = CRITICAL
 */

int main(void) {
    int disabled[3] = {0, 0, 0};
    int guard_zone = 0;
    int current_time = 0;
    int pass_expiry = -1;
    int alert_level = 0;
    int last_event_time = -1;

    char cmd[32];
    while (scanf("%31s", cmd) == 1) {
        if (strcmp(cmd, "EXIT") == 0) {
            break;
        } else if (strcmp(cmd, "DISABLE") == 0) {
            int sensor_id, at_time;
            if (scanf("%d %d", &sensor_id, &at_time) != 2) break;
            if (sensor_id < 0 || sensor_id >= 3) {
                sensor_id = 0;
            }
            disabled[sensor_id] = 1;
            printf("DISABLED %d\n", sensor_id);
        } else if (strcmp(cmd, "WAIT") == 0) {
            int steps;
            if (scanf("%d", &steps) != 1) break;
            if (steps < 0) {
                printf("ERR INVALID_TIME\n");
            } else {
                current_time += steps;
                guard_zone = (guard_zone + steps) % 3;
                printf("GUARD %d TIME %d\n", guard_zone, current_time);
            }
        } else if (strcmp(cmd, "GRANT_PASS") == 0) {
            int expires_at;
            if (scanf("%d", &expires_at) != 1) break;
            pass_expiry = expires_at;
            printf("PASS_SET %d\n", pass_expiry);
        } else if (strcmp(cmd, "TRIGGER") == 0) {
            int sensor_id, at_time, severity;
            if (scanf("%d %d %d", &sensor_id, &at_time, &severity) != 3) break;
            if (pass_expiry != -1 && at_time <= pass_expiry) {
                printf("SUPPRESSED\n");
            } else if (sensor_id >= 0 && sensor_id < 3 && disabled[sensor_id] == 1) {
                printf("IGNORED\n");
            } else {
                alert_level = severity;
                last_event_time = at_time;
                printf("ALERT %d\n", alert_level);
            }
        } else if (strcmp(cmd, "ESCAPE") == 0) {
            int start_zone, exit_zone, at_time;
            if (scanf("%d %d %d", &start_zone, &exit_zone, &at_time) != 3) break;
            printf("ERR NOT_IMPLEMENTED\n");
        }
    }
    return 0;
}
