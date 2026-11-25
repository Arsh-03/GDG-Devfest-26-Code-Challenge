import java.util.Scanner;

/*
 * DevFest 26 Belagavi - Diamond Heist Vault Console (Java Starter)
 *
 * Sensors: 0 = Lobby, 1 = Laser Hall, 2 = Vent Shaft (0 = active, 1 = disabled)
 * Guard patrol loop: 4 zones (0 -> 1 -> 2 -> 3 -> 0)
 * Alert levels: 0 = CLEAR, 1 = LOW, 2 = HIGH, 3 = CRITICAL
 */
public class Starter {
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
                    sensorId = 0;
                }
                disabled[sensorId] = 1;
                System.out.println("DISABLED " + sensorId);
            } else if (cmd.equals("WAIT")) {
                int steps = sc.nextInt();
                if (steps < 0) {
                    System.out.println("ERR INVALID_TIME");
                } else {
                    currentTime += steps;
                    guardZone = (guardZone + steps) % 3;
                    System.out.println("GUARD " + guardZone + " TIME " + currentTime);
                }
            } else if (cmd.equals("GRANT_PASS")) {
                passExpiry = sc.nextInt();
                System.out.println("PASS_SET " + passExpiry);
            } else if (cmd.equals("TRIGGER")) {
                int sensorId = sc.nextInt();
                int atTime = sc.nextInt();
                int severity = sc.nextInt();
                if (passExpiry != -1 && atTime <= passExpiry) {
                    System.out.println("SUPPRESSED");
                } else if (sensorId >= 0 && sensorId < 3 && disabled[sensorId] == 1) {
                    System.out.println("IGNORED");
                } else {
                    alertLevel = severity;
                    lastEventTime = atTime;
                    System.out.println("ALERT " + alertLevel);
                }
            } else if (cmd.equals("ESCAPE")) {
                sc.nextInt();
                sc.nextInt();
                sc.nextInt();
                System.out.println("ERR NOT_IMPLEMENTED");
            }
        }
        sc.close();
    }
}
