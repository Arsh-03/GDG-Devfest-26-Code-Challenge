import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Queue;
import java.util.Scanner;

public class Starter {
    private static String handleEscape(
            int startZone, int exitZone, int atTime,
            int currentTime, int guardZone, int alertLevel, int[] disabled) {
        if (atTime < currentTime) {
            return "ERR INVALID_TIME";
        }
        if (alertLevel == 3) {
            return "LOCKED";
        }
        if (startZone < 0 || startZone >= 4 || exitZone < 0 || exitZone >= 4) {
            return "NO_PATH";
        }

        boolean[] blocked = new boolean[4];
        for (int z = 0; z < 3; z++) {
            if (disabled[z] == 0) {
                blocked[z] = true;
            }
        }
        int guardAt = (guardZone + (atTime - currentTime)) % 4;
        blocked[guardAt] = true;

        if (blocked[startZone] || blocked[exitZone]) {
            return "NO_PATH";
        }
        if (startZone == exitZone) {
            return "PATH " + startZone;
        }

        int[][] adj = {
            {0, 1, 1, 0},
            {1, 0, 0, 1},
            {1, 0, 0, 1},
            {0, 1, 1, 0}
        };
        boolean[] visited = new boolean[4];
        int[] parent = new int[4];
        Arrays.fill(parent, -1);
        Queue<Integer> queue = new ArrayDeque<>();
        visited[startZone] = true;
        queue.add(startZone);

        boolean found = false;
        while (!queue.isEmpty()) {
            int curr = queue.poll();
            if (curr == exitZone) {
                found = true;
                break;
            }
            for (int nxt = 0; nxt < 4; nxt++) {
                if (adj[curr][nxt] == 1 && !blocked[nxt] && !visited[nxt]) {
                    visited[nxt] = true;
                    parent[nxt] = curr;
                    queue.add(nxt);
                }
            }
        }

        if (!found) {
            return "NO_PATH";
        }
        int[] path = new int[4];
        int len = 0;
        for (int v = exitZone; v != -1; v = parent[v]) {
            path[len++] = v;
        }
        StringBuilder sb = new StringBuilder("PATH");
        for (int i = len - 1; i >= 0; i--) {
            sb.append(" ").append(path[i]);
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        int[] disabled = new int[]{0, 0, 0};
        int guardZone = 0;
        int currentTime = 0;
        int passExpiry = -1;
        int alertLevel = 0;
        int lastEventTime = -1;

        Scanner sc = new Scanner(System.in);
        while (sc.hasNext()) {
            String cmd = sc.next();
            if (cmd.equals("EXIT")) {
                break;
            } else if (cmd.equals("DISABLE")) {
                int sensorId = sc.nextInt();
                sc.nextInt();
                if (sensorId < 0 || sensorId >= 3) {
                    System.out.println("ERR INVALID_SENSOR");
                } else {
                    disabled[sensorId] = 1;
                    System.out.println("DISABLED " + sensorId);
                }
            } else if (cmd.equals("WAIT")) {
                int steps = sc.nextInt();
                if (steps < 0) {
                    System.out.println("ERR INVALID_TIME");
                } else {
                    currentTime += steps;
                    guardZone = (guardZone + steps) % 4;
                    System.out.println("GUARD " + guardZone + " TIME " + currentTime);
                }
            } else if (cmd.equals("GRANT_PASS")) {
                passExpiry = sc.nextInt();
                System.out.println("PASS_SET " + passExpiry);
            } else if (cmd.equals("TRIGGER")) {
                int sensorId = sc.nextInt();
                int atTime = sc.nextInt();
                int severity = sc.nextInt();
                if (passExpiry != -1 && atTime < passExpiry) {
                    System.out.println("SUPPRESSED");
                } else if (sensorId >= 0 && sensorId < 3 && disabled[sensorId] == 1) {
                    System.out.println("IGNORED");
                } else {
                    if (atTime == lastEventTime) {
                        if (severity > alertLevel) {
                            alertLevel = severity;
                        }
                    } else {
                        alertLevel = severity;
                        lastEventTime = atTime;
                    }
                    System.out.println("ALERT " + alertLevel);
                }
            } else if (cmd.equals("ESCAPE")) {
                int startZone = sc.nextInt();
                int exitZone = sc.nextInt();
                int atTime = sc.nextInt();
                System.out.println(handleEscape(startZone, exitZone, atTime, currentTime, guardZone, alertLevel, disabled));
            }
        }
        sc.close();
    }
}
