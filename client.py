import json
import requests
import time
import keyboard


def printMenu():
    print("---------------------------------------")
    print("1. Get price for area 3 Stockholm")
    print("2. Get household consumption")
    print("3. Start charging")
    print("4. Charge to 80% during optimal house consumption")
    print("5. Charge to 80% during optimal electricity price")
    print("6. Get battery percent")
    print("7. Discharge")
    print("8. Exit")
    print("---------------------------------------\nWhat would you like to do? ")


def getPricePerHour():
    url = "http://127.0.0.1:5000/priceperhour"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            print("Price/h starting from 00:00: ")
            output = ""
            hour = 0

            for price in data:
                output += f"{hour}:00 - {price} öre\n"
                hour = hour + 1

            return output.strip()

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")


def getBatteryPercent():
    urlBattery = "http://127.0.0.1:5000/charge"

    try:
        response = requests.get(urlBattery)

        if response.status_code == 200:
            data = response.json()
            return data

        else:
            print(f"Error getting data from server: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")

def turnOnCharger():
    urlBattery = "http://127.0.0.1:5000/charge"

    payload = { "charging": "on" }
    headers = { "Content-Type": "application/json" }

    try:
        response = requests.post(urlBattery, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return True

        else:
            print(f"Error getting data from server: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return False

def turnOffCharger():
    urlBattery = "http://127.0.0.1:5000/charge"

    payload = { "charging": "off" }
    headers = { "Content-Type": "application/json" }

    try:
        response = requests.post(urlBattery, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return True

        else:
            print(f"Error getting data from server: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return False

def getHouseConsumption():
    url = "http://127.0.0.1:5000/baseload"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")

def discharge():
    url = "http://127.0.0.1:5000/discharge"

    payload = { "discharging": "on"}
    headers = { "Content-Type": "application/json" }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            return True
        else:
            print(f"Error getting data from server: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return False

def getServerTime():
    url = "http://127.0.0.1:5000/info"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        simHour = data["sim_time_hour"]
        simMinute = data["sim_time_min"]
        return simHour, simMinute

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return None, None

def getBatteryCapacity():
    url = "http://127.0.0.1:5000/info"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        batteryCapacity = data["battery_capacity_kWh"]
        return batteryCapacity

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return None


def getOptimalHoursandLoad():
    houseConsumption = getHouseConsumption()
    chargerConsumption = 7.4
    optimalHours = []
    totalConsumption = []

    for i, consumption in enumerate(houseConsumption):
        if consumption + chargerConsumption <= 11:
            optimalHours.append(i)
            totalConsumption.append(consumption + chargerConsumption)
    return optimalHours, totalConsumption


def simulateChargingProcess():
    optimalHours, _ = getOptimalHoursandLoad()
    batteryCapacityLimit = 80

    while True:
        simHour, simMin = getServerTime()
        if simHour is None or simMin is None:
            print("Error in fetching simulation time")
            continue

        batteryPercent = getBatteryPercent()

        if batteryPercent >= batteryCapacityLimit:
            turnOffCharger()
            print(f"Battery reached {batteryCapacityLimit}%, stopping charging.")
            break

        if simHour in optimalHours:
            turnOnCharger()
            print(f"Current time: {simHour}:{simMin}, Charging ON, Battery: {round(batteryPercent)}%")
        else:
            turnOffCharger()
            print(f"Current time: {simHour}:{simMin}, Charging OFF, Battery: {round(batteryPercent)}%")

        time.sleep(0.1)


print("Welcome to the EVCharging")


isRunning = True

while isRunning:
    printMenu()
    userInput = input()

    try:
        option = int(userInput)

        if option == 1:
            print(getPricePerHour())
        elif option == 2:
            data = getHouseConsumption()
            print(f"Household consumption starting from 00:00")
            hour = 0
            output = ""
            for load in data:
                output += f"{hour}:00 - {load} kW\n"
                hour += 1
            print(output)

        elif option == 3:
            userOption = 0
            batteryPercent = getBatteryPercent()
            turnOnCharger()

            print("Press '1' to stop charging")

            stopCharging = False

            keyboard.add_hotkey('1', lambda:
                                globals().update(stopCharging=True))

            while batteryPercent < 80 and not stopCharging:
                if batteryPercent is None:
                    print("Failed to retrieve battery percentage, retrying...")
                    time.sleep(2)
                    batteryPercent = getBatteryPercent()
                    continue

                print(f"Battery charged: {round(batteryPercent)} %")
                time.sleep(1)
                batteryPercent = getBatteryPercent()

            if stopCharging:
                print(f"Stopping charging at {round(batteryPercent)} %")
            else:
                print("Battery charged to 80%")

            turnOffCharger()

        elif option == 4:
            simulateChargingProcess()

        elif option == 5:
            print("5. Charge to 80% during optimal electricity price")
        elif option == 6:
            print(f"Battery is {round(getBatteryPercent())} % charged")
        elif option == 7:
            discharge()
            if round(getBatteryPercent()) == 20:
                print("Battery discharged to 20%")
            else:
                print("Error discharging")
        elif option == 8:
            isRunning = False

        else:
            print("Invalid option, please choose number between 1 and 4.")

    except ValueError:
        print("Invalid input, please enter a number.")
