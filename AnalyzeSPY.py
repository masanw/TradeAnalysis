import pandas as pd
import glob
import os
import matplotlib.pyplot as plt

def process_spy_data():
    # 1. データの読み込み
    all_files = glob.glob("download_spy/spy_*.csv")
    
    # 全データを格納するDataFrame
    all_data = pd.DataFrame()
    yearly_results = []
    
    for file in all_files:
        # CSVファイルを読み込む
        df = pd.read_csv(file)
        
        # datetime型に変換
        df['date'] = pd.to_datetime(df['date'])
        
        # 日付でグループ化して最初と最後のデータを取得
        daily_data = df.groupby(df['date'].dt.date).agg({
            'open': 'first',
            'close': 'last'
        }).reset_index()
        
        # シフトを使って前日のcloseを取得
        daily_data['prev_close'] = daily_data['close'].shift(1)
        
        # Overnight ReturnとIntraday Returnの計算
        daily_data['overnight_return'] = (daily_data['open'] / daily_data['prev_close']) - 1
        daily_data['intraday_return'] = (daily_data['close'] / daily_data['open']) - 1
        
        # 日付をdatetime型に変換
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        
        # 全データに追加
        all_data = pd.concat([all_data, daily_data])
        
        # 年の平均を計算
        year = os.path.basename(file).split('_')[1][:4]
        yearly_avg = {
            'year': int(year),
            'avg_overnight_return': daily_data['overnight_return'].mean(),
            'avg_intraday_return': daily_data['intraday_return'].mean()
        }
        
        yearly_results.append(yearly_avg)
    
    # 年別結果をDataFrameに変換
    yearly_df = pd.DataFrame(yearly_results)
    yearly_df = yearly_df.sort_values('year')
    
    # 月別の集計
    all_data['month'] = all_data['date'].dt.month
    monthly_df = all_data.groupby('month').agg({
        'overnight_return': 'mean',
        'intraday_return': 'mean'
    }).reset_index()
    
    # グラフの作成
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # 年別グラフ（上）
    ax1.plot(yearly_df['year'], yearly_df['avg_overnight_return'] * 100, 
            label='Overnight Return (%)', marker='o')
    ax1.plot(yearly_df['year'], yearly_df['avg_intraday_return'] * 100, 
            label='Intraday Return (%)', marker='o')
    
    ax1.set_title('Average Daily Returns by Year')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Return (%)')
    ax1.legend()
    ax1.grid(True)
    ax1.set_xticks(yearly_df['year'])
    
    # 月別グラフ（下）
    ax2.plot(monthly_df['month'], monthly_df['overnight_return'] * 100, 
            label='Overnight Return (%)', marker='o')
    ax2.plot(monthly_df['month'], monthly_df['intraday_return'] * 100, 
            label='Intraday Return (%)', marker='o')
    
    ax2.set_title('Average Daily Returns by Month (All Years)')
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Return (%)')
    ax2.legend()
    ax2.grid(True)
    ax2.set_xticks(range(1, 13))
    
    plt.tight_layout()
    plt.show()
    
    return yearly_df, monthly_df

# プログラムの実行
yearly_results, monthly_results = process_spy_data()

print("\nYearly Results:")
print(yearly_results.to_string(index=False))

print("\nMonthly Results:")
print(monthly_results.to_string(index=False))