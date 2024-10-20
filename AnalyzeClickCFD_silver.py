import pandas as pd
import zipfile
import os
from datetime import datetime
import pytz
import plotly.graph_objects as go
import tkinter as tk
from tkinter import simpledialog, messagebox

# 固定値の定義
PREFIX = 'SPOT_SILVER_'
FOLDER_PATH = 'download_file'
ENCODING = 'shift_jis'  # ファイルのエンコーディングを指定

def convert_to_ny_time(japan_time_str):
    japan_time_str = str(japan_time_str)
    japan_time = datetime.strptime(japan_time_str, '%Y%m%d%H%M')
    jst = pytz.timezone('Asia/Tokyo')
    japan_time = jst.localize(japan_time)
    ny_time = japan_time.astimezone(pytz.timezone('America/New_York'))
    return ny_time.strftime('%Y-%m-%d %H:%M:%S')

def load_trade_data(folder_path, prefix, start_year, end_year):
    all_data = []
    for file_name in os.listdir(folder_path):
        if file_name.startswith(prefix) and file_name.endswith('.zip'):
            zip_path = os.path.join(folder_path, file_name)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for csv_file in zip_ref.namelist():
                    if csv_file.endswith('.csv'):
                        with zip_ref.open(csv_file) as file:
                            df = pd.read_csv(file, names=['datetime', 'bid_open', 'bid_high', 'bid_low', 'bid_close', 'ask_open', 'ask_high', 'ask_low', 'ask_close'], encoding=ENCODING, skiprows=1)
                            df['datetime'] = df['datetime'].apply(convert_to_ny_time)
                            df['datetime'] = pd.to_datetime(df['datetime'])
                            df = df[(df['datetime'].dt.year >= start_year) & (df['datetime'].dt.year <= end_year)]
                            if not df.empty:
                                all_data.append(df)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values(by='datetime').drop_duplicates(subset='datetime', keep='first').reset_index(drop=True)
    else:
        combined_df = pd.DataFrame()
    return combined_df

def calculate_time_frame(timestamp):
    hour = timestamp.hour
    minute = timestamp.minute
    return hour + (minute // 6) / 10

def resample_to_6min(df):
    if df.empty:
        return df
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    ohlc_dict = {
        'bid_open': 'first',
        'bid_high': 'max',
        'bid_low': 'min',
        'bid_close': 'last',
        'ask_open': 'first',
        'ask_high': 'max',
        'ask_low': 'min',
        'ask_close': 'last'
    }
    df_6min = df.resample('6T').apply(ohlc_dict).dropna(how='all')
    df_6min['time_frame'] = df_6min.index.map(calculate_time_frame)
    return df_6min

def calculate_volatility(df):
    if df.empty:
        return df
    df['volatility'] = df['bid_high'] - df['bid_low']
    return df

def calculate_yearly_stats_by_time_frame(df):
    if df.empty:
        return pd.DataFrame()
    df['year'] = df.index.year
    grouped = df.groupby(['year', 'time_frame'])['volatility']
    stats = grouped.agg(['mean', 'std']).reset_index()
    return stats

def calculate_monthly_stats_by_time_frame(df):
    if df.empty:
        return pd.DataFrame()
    df['month'] = df.index.month
    grouped = df.groupby(['month', 'time_frame'])['volatility']
    stats = grouped.agg(['mean', 'std']).reset_index()
    return stats

class YearRangeDialog(simpledialog.Dialog):
    def __init__(self, parent, min_year, max_year):
        self.min_year = min_year
        self.max_year = max_year
        self.start_year = None
        self.end_year = None
        super().__init__(parent, title="Select Year Range")

    def body(self, master):
        tk.Label(master, text="Start Year:").grid(row=0)
        tk.Label(master, text="End Year:").grid(row=1)

        self.start_var = tk.IntVar(value=self.min_year)
        self.end_var = tk.IntVar(value=self.max_year)
        
        self.start_entry = tk.Entry(master, textvariable=self.start_var)
        self.end_entry = tk.Entry(master, textvariable=self.end_var)

        self.start_entry.grid(row=0, column=1)
        self.end_entry.grid(row=1, column=1)
        return self.start_entry

    def validate(self):
        try:
            self.start_year = self.start_var.get()
            self.end_year = self.end_var.get()
            if self.start_year < self.min_year or self.start_year > self.max_year:
                raise ValueError("Invalid start year")
            if self.end_year < self.min_year or self.end_year > self.max_year:
                raise ValueError("Invalid end year")
            if self.start_year > self.end_year:
                raise ValueError("Start year must be less than or equal to end year")
            return True
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return False

    def apply(self):
        self.start_year = self.start_var.get()
        self.end_year = self.end_var.get()

def get_year_range(min_year, max_year):
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを表示しない
    dialog = YearRangeDialog(root, min_year, max_year)
    if dialog.start_year is None or dialog.end_year is None:
        raise ValueError("Year range not specified.")
    return dialog.start_year, dialog.end_year

all_years = set()
for file_name in os.listdir(FOLDER_PATH):
    if file_name.startswith(PREFIX) and file_name.endswith('.zip'):
        with zipfile.ZipFile(os.path.join(FOLDER_PATH, file_name), 'r') as zip_ref:
            for csv_file in zip_ref.namelist():
                if csv_file.endswith('.csv'):
                    year = int(csv_file.split('_')[2][:4])
                    all_years.add(year)

min_year, max_year = min(all_years), max(all_years)
start_year, end_year = get_year_range(min_year, max_year)

trade_data_df = load_trade_data(FOLDER_PATH, PREFIX, start_year, end_year)

if trade_data_df.empty:
    print(f"No data available for the specified range {start_year}-{end_year}.")
else:
    trade_data_6min_df = resample_to_6min(trade_data_df)
    trade_data_6min_df = calculate_volatility(trade_data_6min_df)
    
    # 年ごとの集計
    yearly_stats = calculate_yearly_stats_by_time_frame(trade_data_6min_df)
    
    # 月ごとの集計（全ての年を含む）
    monthly_stats = calculate_monthly_stats_by_time_frame(trade_data_6min_df)

    # 年別の平均値のグラフを作成
    fig_mean_yearly = go.Figure()
    buttons_yearly = []
    for year, group in yearly_stats.groupby('year'):
        fig_mean_yearly.add_trace(go.Scatter(
            x=group['time_frame'],
            y=group['mean'],
            mode='lines',
            name=f'Mean {year}',
            visible=True if year == start_year else False
        ))
        buttons_yearly.append(dict(
            method='update',
            label=str(year),
            args=[{'visible': [True if trace.name.endswith(str(year)) else False for trace in fig_mean_yearly.data]}]
        ))

    fig_mean_yearly.update_layout(
        title='Average Volatility by Time Frame (Yearly)',
        xaxis_title='Time Frame',
        yaxis_title='Average Volatility',
        xaxis=dict(dtick=1),  # X軸の目盛り間隔を指定
        updatemenus=[{
            'buttons': buttons_yearly,
            'direction': 'down',
            'showactive': True,
        }]
    )

    # 月ごとの平均値のグラフを作成
    fig_mean_monthly = go.Figure()
    for month, group in monthly_stats.groupby('month'):
        fig_mean_monthly.add_trace(go.Scatter(
            x=group['time_frame'],
            y=group['mean'],
            mode='lines',
            name=f'Month {month}'
        ))

    fig_mean_monthly.update_layout(
        title='Average Volatility by Time Frame (Monthly Across All Years)',
        xaxis_title='Time Frame',
        yaxis_title='Average Volatility',
        xaxis=dict(dtick=1)  # X軸の目盛り間隔を指定
    )

    # 年別の標準偏差のグラフを作成
    fig_std_yearly = go.Figure()
    for year, group in yearly_stats.groupby('year'):
        fig_std_yearly.add_trace(go.Scatter(
            x=group['time_frame'],
            y=group['std'],
            mode='lines',
            name=f'Std Dev {year}',
            visible=True if year == start_year else False
        ))

    fig_std_yearly.update_layout(
        title='Standard Deviation of Volatility by Time Frame (Yearly)',
        xaxis_title='Time Frame',
        yaxis_title='Standard Deviation of Volatility',
        xaxis=dict(dtick=1),  # X軸の目盛り間隔を指定
        updatemenus=[{
            'buttons': buttons_yearly,
            'direction': 'down',
            'showactive': True,
        }]
    )

    # 月ごとの標準偏差のグラフを作成
    fig_std_monthly = go.Figure()
    for month, group in monthly_stats.groupby('month'):
        fig_std_monthly.add_trace(go.Scatter(
            x=group['time_frame'],
            y=group['std'],
            mode='lines',
            name=f'Month {month}'
        ))

    fig_std_monthly.update_layout(
        title='Standard Deviation of Volatility by Time Frame (Monthly Across All Years)',
        xaxis_title='Time Frame',
        yaxis_title='Standard Deviation of Volatility',
        xaxis=dict(dtick=1)  # X軸の目盛り間隔を指定
    )

    # グラフを表示
    fig_mean_yearly.show()
    fig_std_yearly.show()
    fig_mean_monthly.show()
    fig_std_monthly.show()