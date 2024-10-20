import pandas as pd
import zipfile
import os
from datetime import datetime
import pytz
import matplotlib.pyplot as plt

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

    # 指定フォルダ内のすべてのZIPファイルを取得
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
    
    return df_6min

# 変動幅を計算する関数
def calculate_volatility(df):
    df['volatility'] = df['bid_high'] - df['bid_low']
    return df

# 年ごとの標準偏差と平均値を計算する関数
def calculate_yearly_stats(df):
    df['year'] = df.index.year
    yearly_stats = df.groupby('year')['volatility'].agg(['mean', 'std']).reset_index()
    return yearly_stats

# 月ごとの標準偏差と平均値を計算する関数
def calculate_monthly_stats(df):
    df['year_month'] = df.index.to_period('M')
    monthly_stats = df.groupby('year_month')['volatility'].agg(['mean', 'std']).reset_index()
    return monthly_stats

# トレードデータを読み込む
trade_data_df = load_trade_data(FOLDER_PATH, PREFIX)

# 6分足データに変換
trade_data_6min_df = resample_to_6min(trade_data_df)

# 変動幅を計算
trade_data_6min_df = calculate_volatility(trade_data_6min_df)

# 年ごとの統計量を計算
yearly_stats = calculate_yearly_stats(trade_data_6min_df)

# 月ごとの統計量を計算
monthly_stats = calculate_monthly_stats(trade_data_6min_df)

# 年ごとの折れ線グラフを作成
plt.figure(figsize=(14, 7))
plt.plot(yearly_stats['year'], yearly_stats['mean'], label='Mean Volatility')
plt.plot(yearly_stats['year'], yearly_stats['std'], label='Volatility Std Dev')
plt.title('Yearly Mean and Standard Deviation of Volatility')
plt.xlabel('Year')
plt.ylabel('Volatility')
plt.legend()
plt.grid(True)
plt.show()

# 月ごとの折れ線グラフを作成
plt.figure(figsize=(14, 7))
plt.plot(monthly_stats['year_month'].astype(str), monthly_stats['mean'], label='Mean Volatility')
plt.plot(monthly_stats['year_month'].astype(str), monthly_stats['std'], label='Volatility Std Dev')
plt.title('Monthly Mean and Standard Deviation of Volatility')
plt.xlabel('Year-Month')
plt.ylabel('Volatility')
plt.legend()
plt.xticks(rotation=90)
plt.grid(True)
plt.show()
