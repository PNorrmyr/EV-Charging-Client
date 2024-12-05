import json
import requests
import time
import keyboard
import matplotlib.pyplot as plt
import numpy as np

headers = { "Content-Type": "application/json" }


def print_menu():
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


def get_price_per_hour():
    url = "http://127.0.0.1:5000/priceperhour"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")


def get_battery_percent():
    url = "http://127.0.0.1:5000/charge"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return data

        else:
            print(f"Error getting data from server: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")


def turn_on_charger():
    url = "http://127.0.0.1:5000/charge"

    payload = {"charging": "on"}

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


def turn_off_charger():
    url = "http://127.0.0.1:5000/charge"

    payload = {"charging": "off"}

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


def fetch_charging_info():
    url = "http://127.0.0.1:5000/info"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return None


def get_house_consumption():
    url = "http://127.0.0.1:5000/baseload"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")


def discharge():
    url = "http://127.0.0.1:5000/discharge"

    payload = { "discharging": "on"}

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


def get_server_time():
    url = "http://127.0.0.1:5000/info"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        sim_hour = data["sim_time_hour"]
        sim_minute = data["sim_time_min"]
        return sim_hour, sim_minute

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return None, None


def get_battery_capacity():
    url = "http://127.0.0.1:5000/info"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        battery_capacity = data["battery_capacity_kWh"]
        return battery_capacity

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return None


def get_lowest_consumption_hours():
    consumption_hours = list(enumerate(get_house_consumption()))

    sorted_consumption = sorted(consumption_hours, key=lambda x: x[1])

    #Timmar med lägst förbrukning (de 6 lägsta)
    lowest_consumption_hours = [hour for hour, consumption in sorted_consumption[:6]]

    return lowest_consumption_hours


def get_lowest_price_hours(price_per_hour, num_hours=8):
    price_hours = list(enumerate(price_per_hour))
    sorted_prices = sorted(price_hours, key=lambda x: x[1])
    lowest_price_hours = [hour for hour, price in sorted_prices[:num_hours]]
    return lowest_price_hours


def get_optimal_hours_and_total_consumption():
    house_consumption = get_house_consumption()
    charger_consumption = 7.4
    optimal_hours = []
    total_consumption = []

    for i, consumption in enumerate(house_consumption):
        combined_consumption = consumption + charger_consumption
        total_consumption.append(combined_consumption)
        if combined_consumption <= 11:
            optimal_hours.append(i)
    return optimal_hours, total_consumption


def simulate_charging_lowest_consumption():
    optimal_hours, _ = get_optimal_hours_and_total_consumption()
    lowest_consumptions = get_lowest_consumption_hours()
    battery_capacity_limit = 80

    while True:
        sim_hour, sim_min = get_server_time()
        battery_percent = get_battery_percent()

        if sim_hour is None or sim_min is None:
            print("Error in fetching simulation time")
            continue

        if round(battery_percent) >= battery_capacity_limit:
            turn_off_charger()
            print(f"Battery reached {round(battery_capacity_limit)}%, stopping charging.")
            break

        if sim_hour not in optimal_hours and sim_hour not in lowest_consumptions:
            turn_off_charger()
            print(f"Current time: {sim_hour}:{sim_min}, Charging OFF, Battery: {round(battery_percent)}%")
        else:
            if battery_percent < battery_capacity_limit:
                turn_on_charger()
                print(f"Current time: {sim_hour}:{sim_min}, Charging ON, Battery: {round(battery_percent)}%")
                time.sleep(0.1)
            else:
                turn_off_charger()
                print(f"Battery reached {round(battery_capacity_limit)}%, stopping charging.")
                break
        time.sleep(1)


def simulate_charger_status(price_per_hour):
    optimal_hours, total_consumption = get_optimal_hours_and_total_consumption()
    battery_capacity_limit = 80
    battery_percent = get_battery_percent()

    lowest_price_hours = get_lowest_price_hours(price_per_hour)

    charger_on_hours = []

    for sim_hour in range(24):
        if sim_hour not in optimal_hours or sim_hour not in lowest_price_hours:
            continue
        if battery_percent < battery_capacity_limit:
            charger_on_hours.append(sim_hour)

    return charger_on_hours


def simulate_charging_lowest_price():
    optimal_hours, total_consumption = get_optimal_hours_and_total_consumption()
    battery_percent = get_battery_percent()
    price_per_hour = get_price_per_hour()

    if not price_per_hour:
        print("Failed to retrieve price data.")
        return

    battery_capacity_limit = 80

    lowest_price_hours = get_lowest_price_hours(price_per_hour)

    while True:
        sim_hour, sim_min = get_server_time()

        if sim_hour is None or sim_min is None:
            print("Error in fetching simulation time")
            time.sleep(1)
            continue

        if round(battery_percent) >= battery_capacity_limit:
            turn_off_charger()
            print(f"Battery reached {battery_capacity_limit}%, stopping charging.")
            break

        current_price = price_per_hour[sim_hour]
        print(
            f"Current time: {sim_hour}:{sim_min}, Battery: {round(battery_percent)}%, "
            f"Current price: {current_price} öre, Total consumption: {round(total_consumption[sim_hour], 2)}")

        if sim_hour not in optimal_hours or sim_hour not in lowest_price_hours:
            turn_off_charger()
            print("Charging OFF due to high electricity consumption or not being a low-price hour.")
        elif battery_percent < battery_capacity_limit:
            turn_on_charger()
            print("Charging ON")
            time.sleep(0.1)
            battery_percent = get_battery_percent()
        else:
            turn_off_charger()
            print("Charging OFF due to full battery.")
            break

        time.sleep(1)


def plot_simulation_lowest_consumption():
    hours = np.arange(24)
    optimal_hours, total_consumption = get_optimal_hours_and_total_consumption()
    lowest_consumption_hours = get_lowest_consumption_hours()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(hours, total_consumption,
             label='Total Consumption (kW)', color='orange', linestyle='--', marker='s')

    ax1.set_xlabel('Hour of Day')
    ax1.set_ylabel('Consumption (kW)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.axhline(y=11, color='red', linestyle='--', label='Consumption Limit (11 kW)')

    # Highlighting lowest consumption hours
    for hour in lowest_consumption_hours:
        ax1.axvline(x=hour,
                    color='purple', linestyle='--', alpha=0.5)
        ax1.fill_betweenx([0, max(total_consumption)], hour - 0.5,
                          hour + 0.5,
                          color='purple', alpha=0.3)

    fig.suptitle('Charging Management Over 24 Hours with Lowest Consumption Hours Highlighted')
    fig.legend(loc='upper right', bbox_to_anchor=(1, 0.85))

    plt.grid()
    plt.show()


def plot_combined_consumption_and_price():
    hours = np.arange(24)
    price_per_hour = get_price_per_hour()

    if not price_per_hour:
        print("Failed to retrieve price data.")
        return

    optimal_hours, total_consumption = get_optimal_hours_and_total_consumption()

    charger_on_hours = simulate_charger_status(price_per_hour)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    ax1.plot(hours, total_consumption, label='Total Consumption (kW)', color='orange', linestyle='--', marker='s')
    ax1.axhline(y=11, color='red', linestyle='--', label='Consumption Limit (11 kW)')

    ax1.set_xlabel('Hour of Day')
    ax1.set_ylabel('Consumption (kW)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    ax2 = ax1.twinx()
    ax2.plot(hours, price_per_hour, label='Energy Price (öre)', color='purple', marker='x')
    ax2.set_ylabel('Energy Price (öre)', color='purple')
    ax2.tick_params(axis='y', labelcolor='purple')

    # Highlight the charger on hours
    for hour in charger_on_hours:
        ax1.axvline(x=hour, color='purple', linestyle='--', alpha=0.5)
        ax1.fill_betweenx([0, max(total_consumption)], hour - 0.5,
                          hour + 0.5,
                          color='green', alpha=0.3)

    fig.suptitle('Household Consumption and Energy Prices with Charger Status')

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()

    fig.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

    plt.grid()
    plt.show()


print("Welcome to the EVCharging")

isRunning = True

while isRunning:
    print_menu()
    userInput = input()

    try:
        option = int(userInput)

        if option == 1:
            data = get_price_per_hour()
            print("Price/h starting from 00:00: ")
            output = ""
            hour = 0

            for price in data:
                output += f"{hour}:00 - {price} öre\n"
                hour = hour + 1

            print(output)
        elif option == 2:
            data = get_house_consumption()
            print(f"Household consumption starting from 00:00")
            hour = 0
            output = ""
            for load in data:
                output += f"{hour}:00 - {load} kW\n"
                hour += 1
            print(output)

        elif option == 3:
            battery_percent = get_battery_percent()
            turn_on_charger()

            print("Press '1' to stop charging")

            stop_charging = False

            keyboard.add_hotkey('1', lambda:
            globals().update(stop_charging=True))

            while battery_percent < 80 and not stop_charging:
                if battery_percent is None:
                    print("Failed to retrieve battery percentage, retrying...")
                    time.sleep(2)
                    battery_percent = get_battery_percent()
                    continue

                print(f"Battery charged: {round(battery_percent)} %")
                time.sleep(1)
                battery_percent = get_battery_percent()

            if stop_charging:
                print(f"Stopping charging at {round(battery_percent)} %")
            else:
                print("Battery charged to 80%")

            turn_off_charger()

        elif option == 4:
            simulate_charging_lowest_consumption()
            plot_simulation_lowest_consumption()

        elif option == 5:
            simulate_charging_lowest_price()
            plot_combined_consumption_and_price()
        elif option == 6:
            print(f"Battery is {round(get_battery_percent())} % charged")
        elif option == 7:
            discharge()
            if round(get_battery_percent()) == 20:
                print("Battery discharged to 20%")
            else:
                print("Error discharging")
        elif option == 8:
            isRunning = False

        else:
            print("Invalid option, please choose number between 1 and 8.")

    except ValueError:
        print("Invalid input, please enter a number.")
