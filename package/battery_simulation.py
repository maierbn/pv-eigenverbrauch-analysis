import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

df = None

def create_summary_page(pdf, consumption_per_flat_per_year_kWh, installed_power_oso_kWp, 
                       installed_power_wnw_kWp, battery_capacity_kWh, 
                       battery_discharge_cutoff_limit, battery_charge_efficiency, 
                       battery_max_power_kW, avg_pv_used, avg_consumption, 
                       avg_grid_independence, avg_self_consumption_rate):
    """Create summary page with parameters and results"""
    from matplotlib.patches import Rectangle
    
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 size in inches
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Title
    fig.text(0.5, 0.95, 'PV-Batterie-Simulationsbericht', 
             ha='center', fontsize=18, fontweight='bold')
    fig.text(0.5, 0.92, f'Erstellt am: {datetime.now().strftime("%d.%m.%Y %H:%M:%S")}', 
             ha='center', fontsize=10, color='gray')
    
    y_pos = 0.88
    
    # Section: Annahmen
    fig.text(0.1, y_pos, 'Annahmen', fontsize=14, fontweight='bold')
    y_pos -= 0.03
    
    assumptions_text = """• Latitude/Longitude: 48.865, 9.314 (Burghaldenstr. 5, 71336 Waiblingen)
• Dachneigung zur Straße: 48°, Bearing: 285° (WNW), Azimuth für PVGIS: +105°
• Dachneigung zum Garten: 42°, Bearing: 105° (OSO), Azimuth für PVGIS: -75°"""
    
    fig.text(0.12, y_pos, assumptions_text, ha='left', va='top', fontsize=9, 
             verticalalignment='top')
    y_pos -= 0.10
    
    # Section: Eingabeparameter (as table)
    fig.text(0.1, y_pos, 'Eingabeparameter', fontsize=14, fontweight='bold')
    y_pos -= 0.00
    
    # Create parameter table
    param_data = [
        ['Verbrauch pro Wohnung pro Jahr', f'{consumption_per_flat_per_year_kWh:.0f} kWh'],
        ['Installierte Leistung OSO', f'{installed_power_oso_kWp:.1f} kWp'],
        ['Installierte Leistung WNW', f'{installed_power_wnw_kWp:.1f} kWp'],
        ['Batteriekapazität', f'{battery_capacity_kWh:.1f} kWh'],
        ['Batterie-Entladegrenze', f'{battery_discharge_cutoff_limit * 100:.0f}%'],
        ['Batterie-Ladewirkungsgrad', f'{battery_charge_efficiency * 100:.0f}%'],
        ['Maximale Batterieleistung', f'{battery_max_power_kW:.1f} kW']
    ]
    
    table = ax.table(cellText=param_data, 
                     colWidths=[0.5, 0.25],
                     cellLoc='left',
                     loc='upper left',
                     bbox=[0.1, y_pos-0.18, 0.8, 0.18])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    
    # Style the table
    for i in range(len(param_data)):
        table[(i, 0)].set_facecolor('#f0f0f0')
        table[(i, 1)].set_facecolor('white')
    
    y_pos -= 0.30
    
    # Section: Simulationsergebnisse (as table)
    fig.text(0.1, y_pos, 'Simulationsergebnisse', fontsize=14, fontweight='bold')
    y_pos -= 0.02
    
    results_data = [
        ['Durchschn. jährlich genutzte PV-Energie', f'{int(avg_pv_used)} kWh'],
        ['Durchschn. jährlicher Verbrauch', f'{int(avg_consumption)} kWh'],
        ['Durchschn. Netzunabhängigkeitsrate', f'{avg_grid_independence:.1f}%'],
        ['Durchschn. PV-Eigenverbrauchsrate', f'{avg_self_consumption_rate:.1f}%']
    ]
    
    table2 = ax.table(cellText=results_data, 
                      colWidths=[0.5, 0.25],
                      cellLoc='left',
                      loc='upper left',
                      bbox=[0.1, y_pos-0.11, 0.8, 0.11])
    table2.auto_set_font_size(False)
    table2.set_fontsize(9)
    table2.scale(1, 1.8)
    
    # Style the table
    for i in range(len(results_data)):
        table2[(i, 0)].set_facecolor('#e6f3ff')
        table2[(i, 1)].set_facecolor('white')
        table2[(i, 0)].set_text_props(weight='bold')
    
    y_pos -= 0.14
    
    # Section: Quellen
    fig.text(0.1, y_pos, 'Quellen', fontsize=14, fontweight='bold')
    y_pos -= 0.03
    
    sources_text = """• Stromverbrauch Haushalt - DeStatis
  https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Umwelt/
  UGR/private-haushalte/Tabellen/stromverbrauch-haushalte.html
  Gesamtstromverbrauch pro Jahr

• PVGis Hourly
  https://re.jrc.ec.europa.eu/pvg_tools/en/#api_5.3
  Berechnungstool für Sonneneinstrahlung

• Sample data - Open Power System Data
  https://data.open-power-system-data.org/household_data/
  Messdaten zu Stromverbrauch aus EU-gefördertem Projekt"""
    
    fig.text(0.12, y_pos, sources_text, ha='left', va='top', fontsize=8, 
             verticalalignment='top', family='monospace')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def plot_hourly_profiles(df, pdf=None):
    """Create hourly profile plots for PV, consumption, and battery"""
    # Calculate hourly averages by month
    df_hourly = df.copy()
    df_hourly['month'] = df_hourly.index.month
    df_hourly['hour'] = df_hourly.index.hour
    df_hourly['month_pair'] = ((df_hourly['month'] - 1) // 2) + 1

    hourly_by_month = df_hourly.groupby(['month_pair', 'hour']).agg({
        'PV_total_kW': 'mean',
        'consumption_kW': 'mean',
        'battery_charge_kWh': 'mean',
        'battery_discharge_kWh': 'mean'
    }).reset_index()

    month_pairs = ['Jan-Feb', 'Mär-Apr', 'Mai-Jun', 'Jul-Aug', 'Sep-Okt', 'Nov-Dez']
    colors = [
        '#3A4CC0',  # Jan-Feb: Deep blue (winter)
        '#6FA8DC',  # Mar-Apr: Light blue (spring)
        '#F4A582',  # May-Jun: Light orange (late spring/early summer)
        '#D7191C',  # Jul-Aug: Red (peak summer)
        '#FDAE61',  # Sep-Oct: Orange (fall)
        '#5E8CC0'   # Nov-Dec: Blue (late fall/winter)
    ]

    # Create subplots with A4-friendly size
    fig, axes = plt.subplots(3, 1, figsize=(8.27, 10))

    # Plot 1: PV Production
    for month_pair in range(1, 7):
        month_data = hourly_by_month[hourly_by_month['month_pair'] == month_pair]
        axes[0].plot(month_data['hour'], month_data['PV_total_kW'], 
                    label=month_pairs[month_pair-1], color=colors[month_pair-1], linewidth=2.5)
    axes[0].set_ylabel('Durchschn. PV-Erzeugung (kW)', fontsize=10)
    axes[0].set_title('Durchschnittliche PV-Erzeugung nach Tageszeit (2005-2023)', fontsize=11, fontweight='bold')
    axes[0].set_xticks(range(0, 24, 2))
    axes[0].legend(loc='upper right', ncol=3, fontsize=8)
    axes[0].grid(True, alpha=0.3)

    # Plot 2: Consumption
    for month_pair in range(1, 7):
        month_data = hourly_by_month[hourly_by_month['month_pair'] == month_pair]
        axes[1].plot(month_data['hour'], month_data['consumption_kW'], 
                    label=month_pairs[month_pair-1], color=colors[month_pair-1], linewidth=2.5)
    axes[1].set_ylabel('Durchschn. Verbrauch (kW)', fontsize=10)
    axes[1].set_title('Durchschnittlicher Verbrauch nach Tageszeit (2005-2023)', fontsize=11, fontweight='bold')
    axes[1].set_xticks(range(0, 24, 2))
    axes[1].legend(loc='upper right', ncol=3, fontsize=8)
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Battery Charge/Discharge
    for month_pair in range(1, 7):
        month_data = hourly_by_month[hourly_by_month['month_pair'] == month_pair]
        net_battery = month_data['battery_charge_kWh'] - month_data['battery_discharge_kWh']
        axes[2].plot(month_data['hour'], net_battery, 
                    label=month_pairs[month_pair-1], color=colors[month_pair-1], linewidth=2.5)
    axes[2].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[2].set_xlabel('Tageszeit (Stunde)', fontsize=10)
    axes[2].set_ylabel('Netto-Batteriefluss (kWh)\n(+Laden, -Entladen)', fontsize=10)
    axes[2].set_title('Durchschnittliches Batterieladen/-entladen nach Tageszeit (2005-2023)', fontsize=11, fontweight='bold')
    axes[2].set_xticks(range(0, 24, 2))
    axes[2].legend(loc='upper right', ncol=3, fontsize=8)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    if pdf:
        pdf.savefig(fig)
    plt.show()
    plt.close()


def plot_monthly_pv_usage(df, pdf=None):
    """Create monthly PV output vs unused PV plot"""
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
    months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
    x = np.arange(len(months))
    width = 0.35
    ax.bar(x - width/2, monthly_avg['PV_total_kW'], width, label='Gesamt-PV-Energieertrag', color='orange', alpha=0.8)
    ax.bar(x + width/2, monthly_avg['pv_unused_kWh'], width, label='Nicht genutzte PV-Energie', color='red', alpha=0.8)
    ax.set_xlabel('Monat')
    ax.set_ylabel('Energie (kWh)')
    ax.set_title('Monatlicher PV-Energieertrag vs. ungenutzte PV-Energie (Durchschnitt 2005-2023)')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if pdf:
        pdf.savefig(fig, bbox_inches='tight')
    plt.show()
    plt.close()


def plot_battery_status(df, battery_capacity_kWh, battery_discharge_cutoff_limit, pdf=None):
    """Create battery status plot showing full vs empty days"""
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
    months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
    x = np.arange(len(months))
    width = 0.35
    ax.bar(x - width/2, monthly_battery_status['battery_full'], width, label='Tage mit voller Batterie (>90%)', color='green', alpha=0.8)
    ax.bar(x + width/2, monthly_battery_status['battery_empty'], width, label='Tage mit leerer Batterie (<10%)', color='red', alpha=0.8)
    ax.set_xlabel('Monat')
    ax.set_ylabel('Anzahl Tage')
    ax.set_title('Batteriestatus: Volle vs. leere Tage nach Monat (2005-2023)')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if pdf:
        pdf.savefig(fig, bbox_inches='tight')
    plt.show()
    plt.close()


def generate_pdf_report(df, consumption_per_flat_per_year_kWh, installed_power_oso_kWp, 
                       installed_power_wnw_kWp, battery_capacity_kWh, 
                       battery_discharge_cutoff_limit, battery_charge_efficiency, 
                       battery_max_power_kW, avg_pv_used, avg_consumption, 
                       avg_grid_independence, avg_self_consumption_rate):
    """Generate complete PDF report with all plots and data"""
    pdf_filename = f"PV_Batterie_Simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    with PdfPages(pdf_filename) as pdf:
        # Page 1: Summary
        create_summary_page(pdf, consumption_per_flat_per_year_kWh, installed_power_oso_kWp, 
                          installed_power_wnw_kWp, battery_capacity_kWh, 
                          battery_discharge_cutoff_limit, battery_charge_efficiency, 
                          battery_max_power_kW, avg_pv_used, avg_consumption, 
                          avg_grid_independence, avg_self_consumption_rate)
        
        # Page 2: Hourly profiles
        plot_hourly_profiles(df, pdf)
        
        # Page 3: Monthly PV usage
        plot_monthly_pv_usage(df, pdf)
        
        # Page 4: Battery status
        plot_battery_status(df, battery_capacity_kWh, battery_discharge_cutoff_limit, pdf)
    
    return pdf_filename


def run_pv_battery_simulation(
    consumption_per_flat_per_year_kWh=3200,
    installed_power_oso_kWp=10,
    installed_power_wnw_kWp=10,
    battery_capacity_kWh=20,
    battery_discharge_cutoff_limit=0.1,
    battery_charge_efficiency=0.95,
    battery_max_power_kW=4.2,
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

    # Battery simulation with power limit
    soc = battery_capacity_kWh/2
    soc_list = []
    grid_list = []
    battery_charge_list = []
    battery_discharge_list = []

    for idx, row in df.iterrows():
        pv_surplus = row["PV_total_kW"] - row["consumption_kW"]
        if pv_surplus > 0:
            # Charging: limited by efficiency, capacity, and max power
            charge_possible = min(
                pv_surplus * battery_charge_efficiency, 
                battery_capacity_kWh - soc,
                battery_max_power_kW  # Power limit
            )
            soc += charge_possible
            grid = 0
            battery_charge = charge_possible
            battery_discharge = 0
        else:
            # Discharging: limited by available energy, cutoff limit, and max power
            discharge_possible = min(
                -pv_surplus, 
                soc - battery_capacity_kWh * battery_discharge_cutoff_limit,
                battery_max_power_kW  # Power limit
            )
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
    avg_consumption = annual_stats['consumption_kW'].mean()

    if not enable_plots:
        return avg_pv_used
    
    # Print input parameters
    print("=" * 60)
    print("EINGABEPARAMETER:")
    print("=" * 60)
    print(f"Verbrauch pro Wohnung pro Jahr: {consumption_per_flat_per_year_kWh:.0f} kWh")
    print(f"Installierte Leistung OSO: {installed_power_oso_kWp:.1f} kWp")
    print(f"Installierte Leistung WNW: {installed_power_wnw_kWp:.1f} kWp")
    print(f"Batteriekapazität: {battery_capacity_kWh:.1f} kWh")
    print(f"Batterie-Entladegrenze: {battery_discharge_cutoff_limit * 100:.0f}%")
    print(f"Batterie-Ladewirkungsgrad: {battery_charge_efficiency * 100:.0f}%")
    print(f"Maximale Batterieleistung: {battery_max_power_kW:.1f} kW")
    print("=" * 60)
    print()
    
    print("SIMULATIONSERGEBNISSE:")
    print("-" * 60)
    print(f"Durchschnittliche jährliche genutzte PV-Energie: {avg_pv_used:.2f} kWh")
    print(f"Verbrauch: {avg_consumption:.2f} kWh")
    print(f"Durchschnittliche Netzunabhängigkeitsrate: {avg_grid_independence:.1f}%")
    print(f"Durchschnittliche PV-Eigenverbrauchsrate: {avg_self_consumption_rate:.1f}%")
    print()
    
    # Generate PDF report
    pdf_filename = generate_pdf_report(
        df, consumption_per_flat_per_year_kWh, installed_power_oso_kWp, 
        installed_power_wnw_kWp, battery_capacity_kWh, 
        battery_discharge_cutoff_limit, battery_charge_efficiency, 
        battery_max_power_kW, avg_pv_used, avg_consumption, 
        avg_grid_independence, avg_self_consumption_rate
    )
    
    print(f"PDF-Bericht erfolgreich erstellt: {pdf_filename}")