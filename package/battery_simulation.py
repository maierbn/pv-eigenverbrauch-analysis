import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

df = None

def run_pv_battery_simulation(
    consumption_per_flat_per_year_kWh=3200,
    installed_power_oso_kWp=10,
    installed_power_wnw_kWp=10,
    battery_capacity_kWh=20,
    battery_discharge_cutoff_limit=0.1,
    battery_charge_efficiency=0.95,
    enable_plots=True
):
    global df

    if df is None:

        # Load PV data
        path_oso = "data/Timeseries_48.865_9.314_SA3_1kWp_crystSi_14_42deg_-75deg_2005_2023.json"
        path_wnw = "data/Timeseries_48.865_9.314_SA3_1kWp_crystSi_14_48deg_105deg_2005_2023.json"
        with open(path_oso, "r") as file:
            data_oso = json.load(file)
        with open(path_wnw, "r") as file:
            data_wnw = json.load(file)

        df_raw_oso = pd.DataFrame(data_oso['outputs']['hourly'])
        df_raw_oso["time"] = pd.to_datetime(
            df_raw_oso.time.str.slice(0,4)+"-"+df_raw_oso.time.str.slice(4,6)+"-"+df_raw_oso.time.str.slice(6,8)+" "+
            df_raw_oso.time.str.slice(9,11)+":"+df_raw_oso.time.str.slice(11,13), utc=True)
        df_pv_oso = df_raw_oso.set_index("time")
        df_pv_oso = df_pv_oso.tz_convert("Europe/Berlin")

        df_raw_wnw = pd.DataFrame(data_wnw['outputs']['hourly'])
        df_raw_wnw["time"] = pd.to_datetime(
            df_raw_wnw.time.str.slice(0,4)+"-"+df_raw_wnw.time.str.slice(4,6)+"-"+df_raw_wnw.time.str.slice(6,8)+" "+
            df_raw_wnw.time.str.slice(9,11)+":"+df_raw_wnw.time.str.slice(11,13), utc=True)
        df_pv_wnw = df_raw_wnw.set_index("time")
        df_pv_wnw = df_pv_wnw.tz_convert("Europe/Berlin")

        # Load consumption data
        df_raw = pd.read_csv('data/household_data_15min_singleindex_filtered.csv')
        df_full = df_raw[['cet_cest_timestamp', 'DE_KN_residential2_grid_import']].copy()
        df_full['cet_cest_timestamp'] = pd.to_datetime(df_full['cet_cest_timestamp'], utc=True)
        df_full.set_index('cet_cest_timestamp', inplace=True)
        df_cons = df_full['DE_KN_residential2_grid_import'].diff().resample('h').sum()
        df_filtered = df_cons[(df_cons.index >= pd.to_datetime("2016-01-01", utc=True)) & (df_cons.index <= pd.to_datetime("2016-12-31 23:59:59", utc=True))]
        consumption_year_total = df_filtered.sum()
        df_consumption = pd.DataFrame(df_filtered)
        df_consumption.index = pd.to_datetime(df_consumption.index)
        df_consumption.index.name = "time"
        df_consumption.rename(columns={"DE_KN_residential2_grid_import": "consumption_kW_normed"}, inplace=True)
        df_consumption["consumption_kW_normed"] /= consumption_year_total
        df_consumption["month"] = df_consumption.index.month
        df_consumption["day"] = df_consumption.index.day
        df_consumption["hour"] = df_consumption.index.hour

        # Merge PV and consumption data
        df = pd.merge(df_pv_oso["P"], df_pv_wnw["P"], on="time", suffixes=('_oso', '_wnw'))
        df["year"] = df.index.year
        df["month"] = df.index.month
        df["day"] = df.index.day
        df["hour"] = df.index.hour

        dfs = []
        for year in range(2005, 2024):
            df_merged = pd.merge(df[df.year==year], df_consumption, on=["month", "day", "hour"], how="inner")
            df_merged["year"] = year
            dfs.append(df_merged)
        df = pd.concat(dfs)
        df["time"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
        df.set_index("time", inplace=True)

    # Scale consumption
    df["consumption_kW"] = \
        df["consumption_kW_normed"] + np.roll(df["consumption_kW_normed"], 1) + np.roll(df["consumption_kW_normed"], 2) \
        + np.roll(df["consumption_kW_normed"], 7) + np.roll(df["consumption_kW_normed"], -6)
    
    df["consumption_kW"] *= consumption_per_flat_per_year_kWh
    df["PV_total_kW"] = installed_power_oso_kWp*df["P_oso"]*1e-3 + installed_power_wnw_kWp*df["P_wnw"]*1e-3

    # Battery simulation
    soc = battery_capacity_kWh/2
    soc_list = []
    grid_list = []
    battery_charge_list = []
    battery_discharge_list = []

    for idx, row in df.iterrows():
        pv_surplus = row["PV_total_kW"] - row["consumption_kW"]
        if pv_surplus > 0:
            charge_possible = min(pv_surplus * battery_charge_efficiency, battery_capacity_kWh - soc)
            soc += charge_possible
            grid = 0
            battery_charge = charge_possible
            battery_discharge = 0
        else:
            discharge_possible = min(-pv_surplus, soc - battery_capacity_kWh * battery_discharge_cutoff_limit)
            soc -= discharge_possible
            grid = -pv_surplus - discharge_possible if discharge_possible < -pv_surplus else 0
            battery_charge = 0
            battery_discharge = discharge_possible
        soc_list.append(soc)
        grid_list.append(grid)
        battery_charge_list.append(battery_charge)
        battery_discharge_list.append(battery_discharge)

    df["battery_soc_kWh"] = soc_list
    df["from_grid_kW"] = grid_list
    df["battery_charge_kWh"] = battery_charge_list
    df["battery_discharge_kWh"] = battery_discharge_list

    # Annual stats
    annual_stats = df.copy().groupby('year').agg({
        'PV_total_kW': 'sum',
        'consumption_kW': 'sum',
        'from_grid_kW': 'sum',
        'battery_charge_kWh': 'sum',
        'battery_discharge_kWh': 'sum'
    }).reset_index()
    annual_stats['pv_used_kWh'] = annual_stats['consumption_kW'] - annual_stats['from_grid_kW']
    annual_stats['pv_self_consumption_rate'] = annual_stats['pv_used_kWh'] / annual_stats['PV_total_kW'] * 100
    annual_stats['grid_independence_rate'] = (1 - annual_stats['from_grid_kW'] / annual_stats['consumption_kW']) * 100

    avg_pv_used = annual_stats['pv_used_kWh'].mean()
    avg_self_consumption_rate = annual_stats['pv_self_consumption_rate'].mean()
    avg_grid_independence = annual_stats['grid_independence_rate'].mean()

    if not enable_plots:
        return avg_pv_used
    
    print(f"Average annual PV power used: {avg_pv_used:.2f} kWh")
    print(f"Consumption: {annual_stats['consumption_kW'].mean():.2f} kWh")
    print(f"Average grid independence rate: {avg_grid_independence:.1f}%")
    print(f"Average PV self-consumption rate: {avg_self_consumption_rate:.1f}%")

    # Monthly PV output vs unused PV
    monthly_data = df.copy().groupby(['year', 'month']).agg({
        'PV_total_kW': 'sum',
        'consumption_kW': 'sum',
        'from_grid_kW': 'sum'
    }).reset_index()
    monthly_data['pv_used_kWh'] = monthly_data['consumption_kW'] - monthly_data['from_grid_kW']
    monthly_data['pv_unused_kWh'] = monthly_data['PV_total_kW'] - monthly_data['pv_used_kWh']
    monthly_avg = monthly_data.groupby('month').agg({
        'PV_total_kW': 'mean',
        'pv_unused_kWh': 'mean'
    }).reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    x = np.arange(len(months))
    width = 0.35
    ax.bar(x - width/2, monthly_avg['PV_total_kW'], width, label='Total PV Energy Output', color='orange', alpha=0.8)
    ax.bar(x + width/2, monthly_avg['pv_unused_kWh'], width, label='PV Energy Not Used', color='red', alpha=0.8)
    ax.set_xlabel('Month')
    ax.set_ylabel('Energy (kWh)')
    ax.set_title('Monthly PV Energy Output vs Unused PV Energy (Average 2005-2023)')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

    # Battery status plot
    df_copy = df.copy()
    df_copy["year"] = df_copy.index.year
    df_copy["month"] = df_copy.index.month
    df_copy["day"] = df_copy.index.day
    daily_battery = df_copy.groupby([df_copy.year, df_copy.month, df_copy.day]).agg({
        'battery_soc_kWh': ['min', 'max']
    }).reset_index()
    daily_battery.columns = ['year', 'month', 'day', 'soc_min', 'soc_max']
    battery_full_threshold = battery_capacity_kWh * 0.9
    battery_empty_threshold = battery_capacity_kWh * battery_discharge_cutoff_limit
    daily_battery['battery_full'] = daily_battery['soc_max'] >= battery_full_threshold
    daily_battery['battery_empty'] = daily_battery['soc_min'] <= battery_empty_threshold
    monthly_battery_status = daily_battery.groupby('month').agg({
        'battery_full': 'sum',
        'battery_empty': 'sum'
    }).reset_index()
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(months))
    width = 0.35
    ax.bar(x - width/2, monthly_battery_status['battery_full'], width, label='Days with Battery Full (>90%)', color='green', alpha=0.8)
    ax.bar(x + width/2, monthly_battery_status['battery_empty'], width, label='Days with Battery Empty (<10%)', color='red', alpha=0.8)
    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Days')
    ax.set_title('Battery Status: Days Full vs Empty by Month (2005-2023)')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()