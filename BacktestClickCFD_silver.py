import os
import zipfile
import pandas as pd
from backtesting import Backtest, Strategy
from tkinter import Tk, Label, Button, StringVar, Entry, OptionMenu

# 定数の定義
DATA_FOLDER = 'download_file'
FILE_PREFIX = 'SPOT_SILVER'
ENCODING = 'shift_jis'
BACKTEST_PARAMS_FILE = 'backtest_params.txt'
OPTIMIZE_PARAMS_FILE = 'optimize_params.txt'
YEAR_RANGE_FILE = 'year_range.txt'  # New constant for year range file

def get_available_years(data_folder):
    years = set()
    for filename in os.listdir(data_folder):
        if filename.startswith(FILE_PREFIX) and filename.endswith('.zip'):
            year = filename.split('_')[2][:4]
            years.add(year)
    return sorted(years)

def load_params(filename, default_params):
    if not os.path.exists(filename):
        return default_params
    
    with open(filename, 'r') as file:
        lines = file.readlines()
        return {
            "entry_time": lines[0].strip(),
            "take_profit": lines[1].strip(),
            "stop_loss": lines[2].strip(),
            "close_time": lines[3].strip()
        }

def save_params(filename, params):
    with open(filename, 'w') as file:
        for key in ["entry_time", "take_profit", "stop_loss", "close_time"]:
            file.write(f"{params[key]}\n")

def load_year_range():
    if os.path.exists(YEAR_RANGE_FILE):
        with open(YEAR_RANGE_FILE, 'r') as file:
            lines = file.readlines()
            return lines[0].strip(), lines[1].strip()
    return None, None

def save_year_range(start_year, end_year):
    with open(YEAR_RANGE_FILE, 'w') as file:
        file.write(f"{start_year}\n{end_year}")

def get_user_input(years):
    root = Tk()
    root.title("Backtest or Optimize")

    start_year_var = StringVar()
    end_year_var = StringVar()
    mode_var = StringVar(value="Backtest")

    # Load previously saved year range
    saved_start_year, saved_end_year = load_year_range()
    if saved_start_year and saved_end_year:
        start_year_var.set(saved_start_year)
        end_year_var.set(saved_end_year)
    else:
        start_year_var.set(years[0])
        end_year_var.set(years[-1])

    # バックテスト用デフォルトパラメータの読み込み
    default_backtest_params = {"entry_time": "1630", "take_profit": "0.005", "stop_loss": "0.05", "close_time": "30"}
    backtest_params = load_params(BACKTEST_PARAMS_FILE, default_backtest_params)

    # 最適化用デフォルトパラメータの読み込み
    default_optimize_params = {"entry_time": "range(1615,1645,5)", "take_profit": "[0.004, 0.005, 0.006]", "stop_loss": "[0.04, 0.05, 0.06]", "close_time": "[0, 30, 60]"}
    optimize_params = load_params(OPTIMIZE_PARAMS_FILE, default_optimize_params)

    Label(root, text="Start Year:").grid(row=0, column=0)
    OptionMenu(root, start_year_var, *years).grid(row=0, column=1)

    Label(root, text="End Year:").grid(row=1, column=0)
    OptionMenu(root, end_year_var, *years).grid(row=1, column=1)

    Label(root, text="Mode:").grid(row=2, column=0)
    OptionMenu(root, mode_var, "Backtest", "Optimize").grid(row=2, column=1)

    Label(root, text="Backtest Entry Time (e.g., 1630):").grid(row=3, column=0)
    backtest_entry_time_entry = Entry(root)
    backtest_entry_time_entry.insert(0, backtest_params['entry_time'])
    backtest_entry_time_entry.grid(row=3, column=1)

    Label(root, text="Backtest Take Profit (e.g., 0.005):").grid(row=4, column=0)
    backtest_take_profit_entry = Entry(root)
    backtest_take_profit_entry.insert(0, backtest_params['take_profit'])
    backtest_take_profit_entry.grid(row=4, column=1)

    Label(root, text="Backtest Stop Loss (e.g., 0.05):").grid(row=5, column=0)
    backtest_stop_loss_entry = Entry(root)
    backtest_stop_loss_entry.insert(0, backtest_params['stop_loss'])
    backtest_stop_loss_entry.grid(row=5, column=1)

    Label(root, text="Backtest Close Time (e.g., 30):").grid(row=6, column=0)
    backtest_close_time_entry = Entry(root)
    backtest_close_time_entry.insert(0, backtest_params['close_time'])
    backtest_close_time_entry.grid(row=6, column=1)

    Label(root, text="Optimize Entry Time Range (e.g., range(1615,1645,5))").grid(row=7, column=0)
    optimize_entry_time_entry = Entry(root)
    optimize_entry_time_entry.insert(0, optimize_params['entry_time'])
    optimize_entry_time_entry.grid(row=7, column=1)

    Label(root, text="Optimize Take Profit Values (e.g., [0.004, 0.005, 0.006])").grid(row=8, column=0)
    optimize_take_profit_entry = Entry(root)
    optimize_take_profit_entry.insert(0, optimize_params['take_profit'])
    optimize_take_profit_entry.grid(row=8, column=1)

    Label(root, text="Optimize Stop Loss Values (e.g., [0.04, 0.05, 0.06])").grid(row=9, column=0)
    optimize_stop_loss_entry = Entry(root)
    optimize_stop_loss_entry.insert(0, optimize_params['stop_loss'])
    optimize_stop_loss_entry.grid(row=9, column=1)

    Label(root, text="Optimize Close Times (e.g., [0, 30, 60])").grid(row=10, column=0)
    optimize_close_time_entry = Entry(root)
    optimize_close_time_entry.insert(0, optimize_params['close_time'])
    optimize_close_time_entry.grid(row=10, column=1)

    def submit():
        selected_years = (int(start_year_var.get()), int(end_year_var.get()))
        
        # Save selected year range
        save_year_range(start_year_var.get(), end_year_var.get())
        
        # ユーザーが入力したバックテスト用パラメータを取得
        backtest_params = {
            "entry_time": backtest_entry_time_entry.get(),
            "take_profit": backtest_take_profit_entry.get(),
            "stop_loss": backtest_stop_loss_entry.get(),
            "close_time": backtest_close_time_entry.get()
        }
        save_params(BACKTEST_PARAMS_FILE, backtest_params)

        # ユーザーが入力した最適化用パラメータを取得
        optimize_params = {
            "entry_time": optimize_entry_time_entry.get(),
            "take_profit": optimize_take_profit_entry.get(),
            "stop_loss": optimize_stop_loss_entry.get(),
            "close_time": optimize_close_time_entry.get()
        }
        save_params(OPTIMIZE_PARAMS_FILE, optimize_params)

        root.destroy()
        main(selected_years, mode_var.get(), backtest_params, optimize_params)

    Button(root, text="Submit", command=submit).grid(row=11, column=0, columnspan=2, pady=5)
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
        if len(self.data) > 0 and self.data.index[-1].hour * 100 + self.data.index[-1].minute == self.entry_time:
            entry_price = self.data.Close[-1]
            sl_price = entry_price - self.stop_loss
            tp_price = entry_price + self.take_profit
            
            if sl_price < entry_price < tp_price:
                self.buy(size=1, sl=sl_price, tp=tp_price)

        close_hour = self.close_time // 100
        close_minute = self.close_time % 100
        if self.data.index[-1].hour == close_hour and self.data.index[-1].minute == close_minute:
            if self.orders:
                self.orders.cancel()
            if self.position:
                self.position.close()

def optimize_strategy(data, entry_time_range, tp_values, sl_values, close_times):
    bt = Backtest(data, MyStrategy, cash=100, margin=1, commission=0.000)
    try:
        stats = bt.optimize(
            entry_time=list(eval(entry_time_range)),
            take_profit=list(eval(tp_values)),
            stop_loss=list(eval(sl_values)),
            close_time=list(eval(close_times)),
            maximize='Win Rate [%]'
        )
        return stats
    except Exception as e:
        print(f"Optimization error: {e}")
        return None

def backtest_strategy(data, entry_time, take_profit, stop_loss, close_time):
    MyStrategy.entry_time = int(entry_time)
    MyStrategy.take_profit = float(take_profit)
    MyStrategy.stop_loss = float(stop_loss)
    MyStrategy.close_time = int(close_time)

    bt = Backtest(data, MyStrategy, cash=100, margin=1, commission=0.000)
    stats = bt.run()
    return stats

def main(year_range, mode, backtest_params, optimize_params):
    start_year, end_year = year_range
    data = load_data(start_year, end_year)

    if not os.path.exists('output'):
        os.makedirs('output')

    for year in range(start_year, end_year + 1):
        year_data = data[data.index.year == year]

        if not year_data.empty:
            if mode == "Backtest":
                print(f"--- Running Backtest for {year} ---")
                # バックテスト用パラメータは整数や小数に変換して利用
                stats = backtest_strategy(
                    year_data,
                    backtest_params['entry_time'],
                    backtest_params['take_profit'],
                    backtest_params['stop_loss'],
                    backtest_params['close_time']
                )
                
                with open(f'output/backtest_results_{year}.txt', 'w') as file:
                    print(f"Entry Time: {backtest_params['entry_time']}, Take Profit: {backtest_params['take_profit']}, "
                          f"Stop Loss: {backtest_params['stop_loss']}, Close Time: {backtest_params['close_time']}", file=file)
                    print(stats, file=file)
                    
                stats['_trades'].to_csv(f'output/trades_{year}.csv', index=False)

            elif mode == "Optimize":
                print(f"--- Running Optimization for {year} ---")
                best_stats = optimize_strategy(
                    year_data,
                    optimize_params['entry_time'],
                    optimize_params['take_profit'],
                    optimize_params['stop_loss'],
                    optimize_params['close_time']
                )

                if len(best_stats) > 0:
                    with open(f'output/optimization_results_{year}.txt', 'w') as file:
                        print(f"Best result for {year}:", file=file)
                        print(best_stats.to_string(), file=file)
                        print(best_stats['_strategy'], file=file)

if __name__ == '__main__':
    available_years = get_available_years(DATA_FOLDER)
    get_user_input(available_years)