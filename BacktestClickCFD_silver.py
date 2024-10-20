import os
import zipfile
import pandas as pd
from backtesting import Backtest, Strategy
from backtesting.lib import SignalStrategy
import itertools
from datetime import datetime
from tkinter import Tk, Label, Button, StringVar
from tkinter.ttk import Combobox

# 定数の定義
DATA_FOLDER = 'download_file'
FILE_PREFIX = 'SPOT_SILVER'
ENCODING = 'shift_jis'

def get_available_years(data_folder):
    years = set()
    for filename in os.listdir(data_folder):
        if filename.startswith(FILE_PREFIX) and filename.endswith('.zip'):
            year = filename.split('_')[2][:4]
            years.add(year)
    return sorted(years)

def get_user_input(years):
    root = Tk()
    root.title("Select Year Range")

    start_year_var = StringVar()
    end_year_var = StringVar()

    Label(root, text="Start Year:").grid(row=0, column=0, padx=5, pady=5)
    start_year_combo = Combobox(root, textvariable=start_year_var)
    start_year_combo['values'] = years
    start_year_combo.grid(row=0, column=1, padx=5, pady=5)

    Label(root, text="End Year:").grid(row=1, column=0, padx=5, pady=5)
    end_year_combo = Combobox(root, textvariable=end_year_var)
    end_year_combo['values'] = years
    end_year_combo.grid(row=1, column=1, padx=5, pady=5)

    def submit():
        selected_years = (int(start_year_var.get()), int(end_year_var.get()))
        root.destroy()
        main(selected_years)

    Button(root, text="Submit", command=submit).grid(row=2, column=0, columnspan=2, pady=10)
    root.mainloop()

def load_data(start_year, end_year, data_folder=DATA_FOLDER):
    all_data = []

    for year in range(start_year, end_year + 1):
        year_str = str(year)
        zip_files = [f for f in os.listdir(data_folder) if f.startswith(FILE_PREFIX) and f.endswith('.zip') and year_str in f]

        for zip_file in zip_files:
            with zipfile.ZipFile(os.path.join(data_folder, zip_file)) as z:
                for csv_file in z.namelist():
                    with z.open(csv_file) as f:
                        df = pd.read_csv(f, encoding=ENCODING)
                        df.columns = ["Datetime", "BID_Open", "BID_High", "BID_Low", "BID_Close",
                                      "ASK_Open", "ASK_High", "ASK_Low", "ASK_Close"]
                        df['Datetime'] = pd.to_datetime(df['Datetime'], format='%Y%m%d%H%M')
                        all_data.append(df)

    all_data = pd.concat(all_data)
    all_data.set_index('Datetime', inplace=True)
    all_data = all_data.rename(columns={
        'BID_Open': 'Open',
        'BID_High': 'High',
        'BID_Low': 'Low',
        'BID_Close': 'Close'
    })

    return all_data

class MyStrategy(Strategy):
    entry_time = 1630
    take_profit = 0.005
    stop_loss = 0.05
    close_time = 30

    def init(self):
        pass

    def next(self):
        # エントリー
        if len(self.data) > 0 and self.data.index[-1].hour * 100 + self.data.index[-1].minute == self.entry_time:
            entry_price = self.data.Close[-1]
            sl_price = entry_price - self.stop_loss
            tp_price = entry_price + self.take_profit
            
            if sl_price < entry_price < tp_price:
                self.buy(size=1, sl=sl_price, tp=tp_price)

        # ポジションクローズ
        if len(self.data) > 0 and self.data.index[-1].hour == 0 and self.data.index[-1].minute == self.close_time:
            self.position.close()

def optimize_strategy(data, entry_time_range, tp_values, sl_values, close_times):
    best_stats = None
    best_params = None
    results = []

    param_combinations = itertools.product(entry_time_range, tp_values, sl_values, close_times)

    for entry_time, tp, sl, close_time in param_combinations:
        MyStrategy.entry_time = entry_time
        MyStrategy.take_profit = tp
        MyStrategy.stop_loss = sl
        MyStrategy.close_time = close_time

        bt = Backtest(data, MyStrategy, cash=10000, commission=0.000)
        stats = bt.run()

        results.append((entry_time, tp, sl, close_time, stats['Return [%]']))

        if best_stats is None or stats['Return [%]'] > best_stats['Return [%]']:
            best_stats = stats
            best_params = (entry_time, tp, sl, close_time)

    return best_stats, best_params, results

def main(year_range):
    start_year, end_year = year_range
    data = load_data(start_year, end_year)

    # パラメータレンジの定義
    entry_time_range = range(1615, 1701, 2)
    take_profit_values = [0.003, 0.004, 0.005]
    stop_loss_values = [0.05, 0.08, 0.1]
    close_times = [10, 15, 30]

    with open('backtest_results.txt', 'w') as file:
        for year in range(start_year, end_year + 1):
            year_data = data[data.index.year == year]

            if not year_data.empty:
                print(f"\n--- Running Backtest for {year} ---", file=file)
                best_stats, best_params, all_results = optimize_strategy(year_data, entry_time_range, take_profit_values, stop_loss_values, close_times)
                
                print(f"Best result for {year}:", file=file)
                print(f"Entry Time: {best_params[0]}, Take Profit: {best_params[1]}, Stop Loss: {best_params[2]}, Close Time: {best_params[3]}", file=file)
                print(f"Return [%]: {best_stats['Return [%]']}\n", file=file)

                # 全結果を出力
                for result in all_results:
                    print(f"Entry: {result[0]}, TP: {result[1]}, SL: {result[2]}, Close: {result[3]} -> Return [%]: {result[4]}", file=file)

if __name__ == '__main__':
    available_years = get_available_years(DATA_FOLDER)
    get_user_input(available_years)