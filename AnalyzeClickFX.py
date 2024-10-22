import pandas as pd
import zipfile
import os
from datetime import datetime
import pytz
import plotly.graph_objects as go
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import plotly.io as pio

ENCODING = 'shift_jis'

def parse_timestamp(timestamp):
    """
    2つの異なるフォーマットのタイムスタンプを解析する
    フォーマット1: YYYY/MM/DD HH:MM:SS
    フォーマット2: YYYYMMDDHHMMSS
    """
    if not isinstance(timestamp, str):
        timestamp = str(timestamp)
        
    timestamp = timestamp.strip()
    
    try:
        if '/' in timestamp:
            # フォーマット1: YYYY/MM/DD HH:MM:SS
            return datetime.strptime(timestamp, '%Y/%m/%d %H:%M:%S')
        else:
            # フォーマット2: YYYYMMDDHHMMSS
            return datetime.strptime(timestamp, '%Y%m%d%H%M%S')
    except ValueError as e:
        print(f"Error parsing timestamp: {timestamp}")
        raise e

def convert_to_ny_time(timestamp):
    """
    タイムスタンプを日本時間からニューヨーク時間に変換
    """
    if not isinstance(timestamp, datetime):
        timestamp = parse_timestamp(timestamp)
        
    jst = pytz.timezone('Asia/Tokyo')
    japan_time = jst.localize(timestamp)
    ny_time = japan_time.astimezone(pytz.timezone('America/New_York'))
    return ny_time.strftime('%Y-%m-%d %H:%M:%S')

def get_user_input():
    root = tk.Tk()
    root.withdraw()

    currency_pairs = ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'EURUSD', 'GBPUSD']
    dialog = tk.Toplevel(root)
    dialog.title("通貨ペアの選択")
    dialog.geometry("300x200")
    
    selected_pair = tk.StringVar(dialog)
    selected_pair.set(currency_pairs[0])
    
    label = tk.Label(dialog, text="通貨ペアを選択してください:")
    label.pack(pady=10)
    
    dropdown = tk.OptionMenu(dialog, selected_pair, *currency_pairs)
    dropdown.pack(pady=10)
    
    prefix = [None]
    
    def on_select():
        prefix[0] = selected_pair.get()
        dialog.destroy()
        
    button = tk.Button(dialog, text="選択", command=on_select)
    button.pack(pady=10)
    
    dialog.wait_window()
    
    folder_path = filedialog.askdirectory(
        title="為替データが保存されているフォルダを選択してください",
        initialdir=os.getcwd()
    )
    
    if not folder_path or prefix[0] is None:
        messagebox.showerror("エラー", "フォルダまたは通貨ペアが選択されていません。")
        root.destroy()
        exit()
        
    root.destroy()
    return folder_path, prefix[0]

def load_trade_data(folder_path, prefix, start_year, end_year):
    all_data = []
    error_files = []
    
    for file_name in os.listdir(folder_path):
        if file_name.startswith(prefix) and file_name.endswith('.zip'):
            zip_path = os.path.join(folder_path, file_name)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for csv_file in zip_ref.namelist():
                        parts = csv_file.split('/')
                        if (len(parts) > 1 and parts[0].endswith('_EX') == False and csv_file.endswith('.csv')):
                            try:
                                with zip_ref.open(csv_file) as file:
                                    df = pd.read_csv(file, 
                                                   names=['datetime', 'bid_open', 'bid_high', 'bid_low', 'bid_close', 
                                                         'ask_open', 'ask_high', 'ask_low', 'ask_close'],
                                                   encoding=ENCODING, skiprows=1)
                                    
                                    df['datetime'] = df['datetime'].apply(convert_to_ny_time)
                                    df['datetime'] = pd.to_datetime(df['datetime'])
                                    
                                    df = df[(df['datetime'].dt.year >= start_year) & 
                                          (df['datetime'].dt.year <= end_year)]
                                    
                                    if not df.empty:
                                        all_data.append(df)
                            except Exception as e:
                                error_files.append(f"{csv_file}: {str(e)}")
            except Exception as e:
                error_files.append(f"{file_name}: {str(e)}")

    if error_files:
        error_message = "以下のファイルの処理中にエラーが発生しました：\n" + "\n".join(error_files)
        messagebox.showwarning("警告", error_message)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values(by='datetime').drop_duplicates(subset='datetime', keep='first').reset_index(drop=True)
    else:
        combined_df = pd.DataFrame()
    return combined_df

def get_year_range(min_year, max_year):
    root = tk.Tk()
    root.withdraw()

    dialog = tk.Toplevel(root)
    dialog.title("年範囲の選択")
    dialog.geometry("300x250")

    start_var = tk.IntVar(value=min_year)
    end_var = tk.IntVar(value=max_year)

    tk.Label(dialog, text="開始年:").pack(pady=5)
    start_spinbox = tk.Spinbox(dialog, from_=min_year, to=max_year, textvariable=start_var)
    start_spinbox.pack(pady=5)

    tk.Label(dialog, text="終了年:").pack(pady=5)
    end_spinbox = tk.Spinbox(dialog, from_=min_year, to=max_year, textvariable=end_var)
    end_spinbox.pack(pady=5)

    result = {"start": None, "end": None}

    def on_ok():
        result["start"] = start_var.get()
        result["end"] = end_var.get()
        dialog.destroy()

    tk.Button(dialog, text="OK", command=on_ok).pack(pady=20)

    dialog.wait_window()
    root.destroy()

    return result["start"], result["end"]

def resample_to_6min(df):
    df_6min = df.set_index('datetime').resample('6T').agg({
        'bid_open': 'first',
        'bid_high': 'max',
        'bid_low': 'min',
        'bid_close': 'last',
        'ask_open': 'first',
        'ask_high': 'max',
        'ask_low': 'min',
        'ask_close': 'last'
    }).reset_index()
    return df_6min.dropna()

def calculate_volatility(df):
    df['volatility'] = df['bid_high'] - df['bid_low']
    return df

def calculate_yearly_stats_by_time_frame(df):
    df['hour'] = df['datetime'].dt.hour
    df['year'] = df['datetime'].dt.year
    
    yearly_stats = df.groupby(['year', 'hour'])['volatility'].agg(['mean', 'std', 'count']).reset_index()
    return yearly_stats

def calculate_monthly_stats_by_time_frame(df):
    df['hour'] = df['datetime'].dt.hour
    df['month'] = df['datetime'].dt.month
    
    monthly_stats = df.groupby(['month', 'hour'])['volatility'].agg(['mean', 'std', 'count']).reset_index()
    return monthly_stats

def create_yearly_line_plots(stats, base_title, filename):
    # 平均値のグラフ
    fig_mean = go.Figure()
    buttons = []
    
    # 年ごとのデータをプロット
    years = sorted(stats['year'].unique())
    
    # すべての年のトレースを追加
    for year in years:
        year_data = stats[stats['year'] == year]
        
        # 平均値の折れ線
        fig_mean.add_trace(go.Scatter(
            x=year_data['hour'],
            y=year_data['mean'],
            mode='lines',
            name=f'Year {year}',
            visible=True
        ))

    # 全年のオン/オフボタン
    buttons.append(dict(
        label='Show All',
        method='update',
        args=[{'visible': [True] * len(years)}]
    ))
    
    buttons.append(dict(
        label='Hide All',
        method='update',
        args=[{'visible': [False] * len(years)}]
    ))
    
    # 個別の年のオン/オフボタン
    for i, year in enumerate(years):
        visible = [False] * len(years)
        visible[i] = True
        buttons.append(dict(
            label=f'Year {year}',
            method='update',
            args=[{'visible': visible}]
        ))

    # レイアウトの更新
    fig_mean.update_layout(
        title=f'{base_title} - Average Volatility by Year',
        xaxis_title='Hour (NY Time)',
        yaxis_title='Average Volatility',
        xaxis=dict(dtick=1),
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.1,
            'y': 1.15
        }],
        showlegend=True,
        width=1000,
        height=600
    )

    # 標準偏差のグラフ
    fig_std = go.Figure()
    
    # 年ごとのデータをプロット
    for year in years:
        year_data = stats[stats['year'] == year]
        
        fig_std.add_trace(go.Scatter(
            x=year_data['hour'],
            y=year_data['std'],
            mode='lines',
            name=f'Year {year}',
            visible=True
        ))

    fig_std.update_layout(
        title=f'{base_title} - Volatility Standard Deviation by Year',
        xaxis_title='Hour (NY Time)',
        yaxis_title='Volatility Standard Deviation',
        xaxis=dict(dtick=1),
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.1,
            'y': 1.15
        }],
        showlegend=True,
        width=1000,
        height=600
    )

    # グラフをHTMLファイルとして保存
    pio.write_html(fig_mean, f'{filename}_mean.html')
    pio.write_html(fig_std, f'{filename}_std.html')

def create_monthly_line_plots(stats, base_title, filename):
    # 平均値のグラフ
    fig_mean = go.Figure()
    
    # 月ごとのデータをプロット
    months = sorted(stats['month'].unique())
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for month in months:
        month_data = stats[stats['month'] == month]
        
        fig_mean.add_trace(go.Scatter(
            x=month_data['hour'],
            y=month_data['mean'],
            mode='lines',
            name=f'{month_names[month-1]}',
            visible=True
        ))

    # レイアウトの更新
    fig_mean.update_layout(
        title=f'{base_title} - Average Volatility by Month',
        xaxis_title='Hour (NY Time)',
        yaxis_title='Average Volatility',
        xaxis=dict(dtick=1),
        showlegend=True,
        width=1000,
        height=600
    )

    # 標準偏差のグラフ
    fig_std = go.Figure()
    
    for month in months:
        month_data = stats[stats['month'] == month]
        
        fig_std.add_trace(go.Scatter(
            x=month_data['hour'],
            y=month_data['std'],
            mode='lines',
            name=f'{month_names[month-1]}',
            visible=True
        ))

    fig_std.update_layout(
        title=f'{base_title} - Volatility Standard Deviation by Month',
        xaxis_title='Hour (NY Time)',
        yaxis_title='Volatility Standard Deviation',
        xaxis=dict(dtick=1),
        showlegend=True,
        width=1000,
        height=600
    )

    # グラフをHTMLファイルとして保存
    pio.write_html(fig_mean, f'{filename}_mean.html')
    pio.write_html(fig_std, f'{filename}_std.html')

def main():
    # ユーザー入力の取得
    folder_path, prefix = get_user_input()
    
    # 利用可能な年の範囲を取得
    all_years = set()
    for file_name in os.listdir(folder_path):
        if file_name.startswith(prefix) and file_name.endswith('.zip'):
            with zipfile.ZipFile(os.path.join(folder_path, file_name), 'r') as zip_ref:
                for csv_file in zip_ref.namelist():
                    parts = csv_file.split('/')
                    if (len(parts) > 1 and parts[0].endswith('_EX') == False and csv_file.endswith('.csv')):
                        year = int(csv_file.split('_')[1][:4])
                        all_years.add(year)

    if not all_years:
        messagebox.showerror("エラー", f"通貨ペア {prefix} のデータが見つかりません。")
        return

    # 年範囲の選択
    min_year, max_year = min(all_years), max(all_years)
    start_year, end_year = get_year_range(min_year, max_year)
    
    #
    trade_data_df = load_trade_data(folder_path, prefix, start_year, end_year)

    if trade_data_df.empty:
        print(f"No data available for the specified range {start_year}-{end_year}.")
    else:
        trade_data_6min_df = resample_to_6min(trade_data_df)
        trade_data_6min_df = calculate_volatility(trade_data_6min_df)
        
        # 年ごとの集計
        yearly_stats = calculate_yearly_stats_by_time_frame(trade_data_6min_df)
        
        # 月ごとの集計（全ての年を含む）
        monthly_stats = calculate_monthly_stats_by_time_frame(trade_data_6min_df)

    create_yearly_line_plots(yearly_stats, 'Average Volatility by Time Frame (Yearly)', 'AverageVolatility_Yearly')

    create_monthly_line_plots(monthly_stats, 'Average Volatility by Time Frame (Monthly)', 'AverageVolatility_Monthly')

if __name__ == '__main__':
    main()
    