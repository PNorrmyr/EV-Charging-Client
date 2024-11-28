import json

import requests
import time

isRunning = True


def printMenu():
    print("---------------------------------------")
    print("1. Get price for area 3 Stockholm")
    print("2. Get household consumption")
    print("3. Start charging")
    print("4. Get battery info and charge to 80%")
    print("5. Exit")
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

def getHouseConsumption():
    url = "http://127.0.0.1:5000/baseload"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        print(f"Household consumption starting from 00:00")
        hour = 0
        output = ""
        for load in data:
            output += f"{hour}:00 - {load} kW\n"
            hour += 1

        return output.strip()

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")


print("Welcome to the EVCharging")

while isRunning:
    printMenu()
    userInput = input()

    try:
        option = int(userInput)

        if option == 1:
            print(getPricePerHour())
        elif option == 2:
            print(getHouseConsumption())

        elif option == 3:
            batteryPercent = getBatteryPercent()
            turnOnCharger()
            batteryCharged = False

            while not batteryCharged:
                if batteryPercent is None:
                    print("Failed to retrieve battery percentage, retrying...")
                    time.sleep(2)
                    batteryPercent = getBatteryPercent()
                    continue

                if batteryPercent >= 80:
                    print("Battery charged to 80%.")
                    batteryCharged = True
                else:
                    print(f"Battery charged: {batteryPercent} %")
                    time.sleep(4)
                    batteryPercent = getBatteryPercent()

        elif option == 4:
            print("option 4")
        elif option == 5:
            isRunning = False

        else:
            print("Invalid option, please choose number between 1 and 4.")

    except ValueError:
        print("Invalid input, please enter a number.")
