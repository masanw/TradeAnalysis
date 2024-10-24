import pandas as pd
import glob
import os
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os



def process_spy_data():
    # 1. データの読み込み
    all_files = glob.glob("download_spy/spy_*.csv")
    
    # 全データを格納するDataFrame
    all_data = pd.DataFrame()
    yearly_results = []
    
    for file in all_files:
        # CSVファイルを読み込む
        df = pd.read_csv(file)
        df['date'] = pd.to_datetime(df['date'])
        
        daily_data = df.groupby(df['date'].dt.date).agg({
            'open': 'first',
            'close': 'last'
        }).reset_index()
        
        daily_data['prev_close'] = daily_data['close'].shift(1)
        daily_data['overnight_return'] = (daily_data['open'] / daily_data['prev_close']) - 1
        daily_data['intraday_return'] = (daily_data['close'] / daily_data['open']) - 1
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        
        all_data = pd.concat([all_data, daily_data])
        
        year = os.path.basename(file).split('_')[1][:4]
        yearly_avg = {
            'year': int(year),
            'avg_overnight_return': daily_data['overnight_return'].mean(),
            'avg_intraday_return': daily_data['intraday_return'].mean()
        }
        yearly_results.append(yearly_avg)
    
    # データの準備
    yearly_df = pd.DataFrame(yearly_results).sort_values('year')
    all_data['year'] = all_data['date'].dt.year
    all_data['month'] = all_data['date'].dt.month
    monthly_df = all_data.groupby('month').agg({
        'overnight_return': 'mean',
        'intraday_return': 'mean'
    }).reset_index()
    
    # ページ1: 年別と月別の集計グラフ
    plt.figure(figsize=(12, 10))
    
    # 年別グラフ（上）
    plt.subplot(2, 1, 1)
    plt.plot(yearly_df['year'], yearly_df['avg_overnight_return'] * 100, 
            label='Overnight Return (%)', marker='o')
    plt.plot(yearly_df['year'], yearly_df['avg_intraday_return'] * 100, 
            label='Intraday Return (%)', marker='o')
    plt.title('Average Daily Returns by Year', fontsize=12, pad=15)
    plt.xlabel('Year')
    plt.ylabel('Return (%)')
    plt.legend()
    plt.grid(True)
    plt.xticks(yearly_df['year'])
    
    # 月別グラフ（下）
    plt.subplot(2, 1, 2)
    plt.plot(monthly_df['month'], monthly_df['overnight_return'] * 100, 
            label='Overnight Return (%)', marker='o')
    plt.plot(monthly_df['month'], monthly_df['intraday_return'] * 100, 
            label='Intraday Return (%)', marker='o')
    plt.title('Average Daily Returns by Month (All Years)', fontsize=12, pad=15)
    plt.xlabel('Month')
    plt.ylabel('Return (%)')
    plt.legend()
    plt.grid(True)
    plt.xticks(range(1, 13))
    
    plt.tight_layout()
    # plt.show()
    plt.savefig(os.path.join(output_dir, 'yearly_monthly_summary.png'), dpi=300, bbox_inches='tight')

    # ページ2: 年ごとの月別グラフ
    years = sorted(list(set(all_data['year'])))
    n_years = len(years)
    
    fig = plt.figure(figsize=(15, n_years * 4))
    gs = GridSpec(n_years, 1, figure=fig)
    gs.update(hspace=0.05)  # グラフ間のスペースを調整
    
    for i, year in enumerate(years):
        ax = fig.add_subplot(gs[i, 0])
        
        year_data = all_data[all_data['year'] == year]
        monthly_avg = year_data.groupby('month').agg({
            'overnight_return': 'mean',
            'intraday_return': 'mean'
        }).reset_index()
        
        ax.plot(monthly_avg['month'], monthly_avg['overnight_return'] * 100, 
               label='Overnight Return (%)', marker='o', markersize=8, linewidth=2)
        ax.plot(monthly_avg['month'], monthly_avg['intraday_return'] * 100, 
               label='Intraday Return (%)', marker='o', markersize=8, linewidth=2)
        
        ax.set_title(f'{year} Monthly Returns', fontsize=14, pad=10)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Return (%)', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_xticks(range(1, 13))
        
        y_min = min(monthly_avg['overnight_return'].min(), monthly_avg['intraday_return'].min()) * 100
        y_max = max(monthly_avg['overnight_return'].max(), monthly_avg['intraday_return'].max()) * 100
        margin = (y_max - y_min) * 0.2
        ax.set_ylim(y_min - margin, y_max + margin)

    plt.savefig(os.path.join(output_dir, 'yearly_breakdown.png'), bbox_inches='tight')
    plt.close('all')

    # 保存したファイルを表示
    from PIL import Image
    img = Image.open(os.path.join(output_dir, 'yearly_breakdown.png'))
    img.show()

    return yearly_df, monthly_df

# スクリプトの先頭に追加
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# プログラムの実行
output_dir = 'output'
ensure_dir(output_dir)

yearly_results, monthly_results = process_spy_data()

print("\nYearly Results:")
print(yearly_results.to_string(index=False))

print("\nMonthly Results (All Years):")
print(monthly_results.to_string(index=False))