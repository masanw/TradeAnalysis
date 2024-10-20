import pandas as pd
import zipfile
import os
from datetime import datetime
import pytz
import plotly.graph_objects as go

# 固定値の定義
PREFIX = 'SPOT_SILVER_'
FOLDER_PATH = 'download_file'
ENCODING = 'shift_jis'  # ファイルのエンコーディングを指定

def convert_to_ny_time(japan_time_str):
    # 日本時間のタイムスタンプを文字列に変換してからdatetimeオブジェクトに変換
    japan_time_str = str(japan_time_str)
    japan_time = datetime.strptime(japan_time_str, '%Y%m%d%H%M')

    # 日本時間のタイムゾーンを設定
    jst = pytz.timezone('Asia/Tokyo')
    japan_time = jst.localize(japan_time)

    # ニューヨーク時間のタイムゾーンを設定 
    ny_time = japan_time.astimezone(pytz.timezone('America/New_York'))
    
    return ny_time.strftime('%Y-%m-%d %H:%M:%S')

def load_trade_data(folder_path, prefix):
    # 全てのCSVファイルのデータを格納するリスト
    all_data = []

    for file_name in os.listdir(folder_path):
        if file_name.startswith(prefix) and file_name.endswith('.zip'):
            zip_path = os.path.join(folder_path, file_name)

            # ZIPファイルを開く
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # ZIPファイル内の各CSVファイルを処理
                for csv_file in zip_ref.namelist():
                    if csv_file.endswith('.csv'):
                        with zip_ref.open(csv_file) as file:
                            # CSVファイルをDataFrameとして読み込み
                            df = pd.read_csv(file, names=['datetime', 'bid_open', 'bid_high', 'bid_low', 'bid_close', 'ask_open', 'ask_high', 'ask_low', 'ask_close'], encoding=ENCODING, skiprows=1)
                            # 日本時間をニューヨーク時間に変換
                            df['datetime'] = df['datetime'].apply(convert_to_ny_time)
                            # DataFrameをリストに追加
                            all_data.append(df)

    # すべてのDataFrameを結合
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # 重複する時間がある行を削除（日本時間の遅い方を削除）
    combined_df = combined_df.sort_values(by='datetime').drop_duplicates(subset='datetime', keep='first').reset_index(drop=True)
    
    return combined_df

def calculate_time_frame(timestamp):
    # 時刻情報から時間フレームを計算
    hour = timestamp.hour
    minute = timestamp.minute
    return hour + (minute // 6) / 10

def resample_to_6min(df):
    # datetime列をdatetime型に変換
    df['datetime'] = pd.to_datetime(df['datetime'])
    # datetime列をインデックスに設定
    df.set_index('datetime', inplace=True)
    
    # 6分ごとにリサンプリングしてOHLCデータを生成
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
    
    # 時間枠を計算して追加
    df_6min['time_frame'] = df_6min.index.map(calculate_time_frame)

    return df_6min

# 変動幅を計算する関数
def calculate_volatility(df):
    df['volatility'] = df['bid_high'] - df['bid_low']
    return df

# 年、月、および時間枠ごとの集計量を計算する関数
def calculate_stats_by_time_frame(df):
    df['year'] = df.index.year
    df['month'] = df.index.month
    grouped = df.groupby(['year', 'month', 'time_frame'])['volatility']
    stats = grouped.agg(['mean', 'std']).reset_index()
    return stats

# すべての年を横断して月ごとの集計を計算する関数
def calculate_monthly_overall_stats(df):
    df['month'] = df.index.month
    grouped = df.groupby(['month', 'time_frame'])['volatility']
    monthly_stats = grouped.agg(['mean', 'std']).reset_index()
    return monthly_stats

# トレードデータを読み込む
trade_data_df = load_trade_data(FOLDER_PATH, PREFIX)

# 6分足データに変換
trade_data_6min_df = resample_to_6min(trade_data_df)

# 変動幅を計算
trade_data_6min_df = calculate_volatility(trade_data_6min_df)

# 年、月、および時間枠ごとの統計量を計算
stats = calculate_stats_by_time_frame(trade_data_6min_df)

# すべての年を横断した月ごとの統計量を計算
monthly_overall_stats = calculate_monthly_overall_stats(trade_data_6min_df)

# 平均値のグラフを作成
fig_mean = go.Figure()

for (year, month), group in stats.groupby(['year', 'month']):
    label = f'{year}-{month:02d}'
    fig_mean.add_trace(go.Scatter(
        x=group['time_frame'],
        y=group['mean'],
        mode='lines',
        name=label
    ))

fig_mean.update_layout(
    title='Average Volatility by Time Frame',
    xaxis_title='Time Frame',
    yaxis_title='Average Volatility',
    hovermode='x'
)

# 標準偏差のグラフを作成
fig_std = go.Figure()

for (year, month), group in stats.groupby(['year', 'month']):
    label = f'{year}-{month:02d}'
    fig_std.add_trace(go.Scatter(
        x=group['time_frame'],
        y=group['std'],
        mode='lines',
        name=label
    ))

fig_std.update_layout(
    title='Standard Deviation of Volatility by Time Frame',
    xaxis_title='Time Frame',
    yaxis_title='Standard Deviation of Volatility',
    hovermode='x'
)

# すべての年を横断した月ごとの平均値のグラフを作成
fig_mean_monthly = go.Figure()

for month, group in monthly_overall_stats.groupby('month'):
    label = f'Month {month:02d}'
    fig_mean_monthly.add_trace(go.Scatter(
        x=group['time_frame'],
        y=group['mean'],
        mode='lines',
        name=label
    ))

fig_mean_monthly.update_layout(
    title='Average Volatility by Time Frame Across All Years (Monthly)',
    xaxis_title='Time Frame',
    yaxis_title='Average Volatility',
    hovermode='x'
)

# すべての年を横断した月ごとの標準偏差のグラフを作成
fig_std_monthly = go.Figure()

for month, group in monthly_overall_stats.groupby('month'):
    label = f'Month {month:02d}'
    fig_std_monthly.add_trace(go.Scatter(
        x=group['time_frame'],
        y=group['std'],
        mode='lines',
        name=label
    ))

fig_std_monthly.update_layout(
    title='Standard Deviation of Volatility by Time Frame Across All Years (Monthly)',
    xaxis_title='Time Frame',
    yaxis_title='Standard Deviation of Volatility',
    hovermode='x'
)

# グラフを表示
fig_mean.show()
fig_std.show()
fig_mean_monthly.show()
fig_std_monthly.show()