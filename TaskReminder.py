import time
import threading

alarms = []


def timer(alarm):
    while time.time() < alarm[1]:
        time.sleep(1)

    if alarm in alarms:
        print('\n🔔 ALARM! "' + alarm[0] + '" TIME IS UP!')
        alarms.remove(alarm)


while True:
    print("\n===== TASK REMINDER SYSTEM =====")
    print("1. Add")
    print("2. List All Alarms")
    print("3. Delete")
    print("4. Exit")

    choice = input("Choose: ")

    if choice == "1":
        name = input("Alarm Name: ")

        while True:
            try:
                time_input = input("Set Time (HH:MM:SS): ")
                hours, minutes, seconds = map(int, time_input.split(":"))

                if hours >= 0 and 0 <= minutes < 60 and 0 <= seconds < 60:
                    total = hours * 3600 + minutes * 60 + seconds

                    if total > 0:
                        break

                print("Invalid alarm.")

            except:
                print("Invalid alarm.")

        end = time.time() + total
        alarm = [name, end]
        alarms.append(alarm)

        print('You have set an "' + name + '" in', total, "seconds.")

        threading.Thread(
            target=timer,
            args=(alarm,),
            daemon=True
        ).start()

    elif choice == "2":
        print("\n===== ALL ALARMS =====")

        if len(alarms) == 0:
            print("No alarms.")
        else:
            for alarm in alarms:
                remaining = int(alarm[1] - time.time())

                if remaining > 0:
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60
                    seconds = remaining % 60

                    print("-", alarm[0],
                          f"({hours:02d}:{minutes:02d}:{seconds:02d})")

    elif choice == "3":
        print("\n===== DELETE ALARM =====")

        if len(alarms) == 0:
            print("No alarms.")
        else:
            for alarm in alarms:
                remaining = int(alarm[1] - time.time())

                if remaining > 0:
                    hours = remaining // 3600
                    minutes = (remaining % 3600) // 60
                    seconds = remaining % 60

                    print("-", alarm[0],
                          f"({hours:02d}:{minutes:02d}:{seconds:02d})")

            name = input("Enter alarm name to delete: ")

            for alarm in alarms:
                if alarm[0] == name:
                    alarms.remove(alarm)
                    print("Alarm deleted!")
                    break
            else:
                print("Alarm not found.")

    elif choice == "4":
        print("Exiting...")
        break

    else:
        print("Invalid choice.")



