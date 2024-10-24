import pandas as pd
import glob
import os
import matplotlib.pyplot as plt

def process_spy_data():
    # 1. データの読み込み
    all_files = glob.glob("download_spy/spy_*.csv")
    
    # 結果を格納するリスト
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
        print(daily_data)
        
        # シフトを使って前日のcloseを取得
        daily_data['prev_close'] = daily_data['close'].shift(1)
        
        # Overnight ReturnとIntraday Returnの計算
        daily_data['overnight_return'] = (daily_data['open'] / daily_data['prev_close']) - 1
        daily_data['intraday_return'] = (daily_data['close'] / daily_data['open']) - 1
        
        # 年の平均を計算
        year = os.path.basename(file).split('_')[1][:4]
        yearly_avg = {
            'year': int(year),
            'avg_overnight_return': daily_data['overnight_return'].mean(),
            'avg_intraday_return': daily_data['intraday_return'].mean()
        }
        
        yearly_results.append(yearly_avg)
    
    # 結果をDataFrameに変換
    results_df = pd.DataFrame(yearly_results)
    results_df = results_df.sort_values('year')
    
    # 3. グラフの作成
    plt.figure(figsize=(10, 6))
    
    plt.plot(results_df['year'], results_df['avg_overnight_return'] * 100, 
             label='Overnight Return (%)', marker='o')
    plt.plot(results_df['year'], results_df['avg_intraday_return'] * 100, 
             label='Intraday Return (%)', marker='o')
    
    plt.title('Average Daily Returns by Year')
    plt.xlabel('Year')
    plt.ylabel('Return (%)')
    plt.legend()
    plt.grid(True)
    
    # X軸を年の整数値に設定
    plt.xticks(results_df['year'])
    
    plt.show()
    
    return results_df

# プログラムの実行
results = process_spy_data()
print("\nYearly Results:")
print(results.to_string(index=False))