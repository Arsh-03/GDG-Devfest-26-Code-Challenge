#include <stdio.h>
#include <string.h>

static void handle_escape(int start_zone, int exit_zone, int at_time,
                          int current_time, int guard_zone, int alert_level,
                          const int disabled[3]) {
    if (at_time < current_time) {
        printf("ERR INVALID_TIME\n");
        return;
    }
    if (alert_level == 3) {
        printf("LOCKED\n");
        return;
    }
    if (start_zone < 0 || start_zone >= 4 || exit_zone < 0 || exit_zone >= 4) {
        printf("NO_PATH\n");
        return;
    }

    int blocked[4] = {0, 0, 0, 0};
    for (int z = 0; z < 3; z++) {
        if (disabled[z] == 0) {
            blocked[z] = 1;
        }
    }
    int guard_at = (guard_zone + (at_time - current_time)) % 4;
    blocked[guard_at] = 1;

    if (blocked[start_zone] || blocked[exit_zone]) {
        printf("NO_PATH\n");
        return;
    }
    if (start_zone == exit_zone) {
        printf("PATH %d\n", start_zone);
        return;
    }

    int adj[4][4] = {
        {0, 1, 1, 0},
        {1, 0, 0, 1},
        {1, 0, 0, 1},
        {0, 1, 1, 0}
    };
    int visited[4] = {0, 0, 0, 0};
    int parent[4] = {-1, -1, -1, -1};
    int queue[4];
    int head = 0, tail = 0;

    visited[start_zone] = 1;
    queue[tail++] = start_zone;

    int found = 0;
    while (head < tail) {
        int curr = queue[head++];
        if (curr == exit_zone) {
            found = 1;
            break;
        }
        for (int nxt = 0; nxt < 4; nxt++) {
            if (adj[curr][nxt] && !blocked[nxt] && !visited[nxt]) {
                visited[nxt] = 1;
                parent[nxt] = curr;
                queue[tail++] = nxt;
            }
        }
    }

    if (!found) {
        printf("NO_PATH\n");
        return;
    }

    int path[4];
    int len = 0;
    for (int v = exit_zone; v != -1; v = parent[v]) {
        path[len++] = v;
    }
    printf("PATH");
    for (int i = len - 1; i >= 0; i--) {
        printf(" %d", path[i]);
    }
    printf("\n");
}

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
                printf("ERR INVALID_SENSOR\n");
            } else {
                disabled[sensor_id] = 1;
                printf("DISABLED %d\n", sensor_id);
            }
        } else if (strcmp(cmd, "WAIT") == 0) {
            int steps;
            if (scanf("%d", &steps) != 1) break;
            if (steps < 0) {
                printf("ERR INVALID_TIME\n");
            } else {
                current_time += steps;
                guard_zone = (guard_zone + steps) % 4;
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
            if (pass_expiry != -1 && at_time < pass_expiry) {
                printf("SUPPRESSED\n");
            } else if (sensor_id >= 0 && sensor_id < 3 && disabled[sensor_id] == 1) {
                printf("IGNORED\n");
            } else {
                if (at_time == last_event_time) {
                    if (severity > alert_level) {
                        alert_level = severity;
                    }
                } else {
                    alert_level = severity;
                    last_event_time = at_time;
                }
                printf("ALERT %d\n", alert_level);
            }
        } else if (strcmp(cmd, "ESCAPE") == 0) {
            int start_zone, exit_zone, at_time;
            if (scanf("%d %d %d", &start_zone, &exit_zone, &at_time) != 3) break;
            handle_escape(start_zone, exit_zone, at_time, current_time, guard_zone, alert_level, disabled);
        }
    }
    return 0;
}
