import os
from datetime import datetime
import zipfile
import pandas as pd
from backtesting import Backtest, Strategy
from tkinter import Tk, Label, Button, StringVar, Entry, OptionMenu, Radiobutton
import json
import pytz

# 定数の定義
DATA_FOLDER = 'download_file'
ENCODING = 'shift_jis'
MARGIN = 0.06
CASH = 100
SIZE = 1

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

def get_available_years(data_folder):
    years = set()
    for filename in os.listdir(data_folder):
        if filename.endswith('.zip'):
            year = filename.split('_')[1][:4]  # "EURJPY_202301.zip"から年を抽出
            years.add(year)
    return sorted(years)

def get_available_currency_pairs(data_folder):
    pairs = set()
    for filename in os.listdir(data_folder):
        if filename.endswith('.zip'):
            pair = filename.split('_')[0]
            pairs.add(pair)
    return sorted(pairs)

def get_params_file(currency_pair):
    return f'all_params_{currency_pair}.json'

def load_params(currency_pair):
    params_file = get_params_file(currency_pair)
    if not os.path.exists(params_file):
        return {
            "year_range": {"start_year": None, "end_year": None},
            "backtest": {"entry_time": "1600", "take_profit": "0.005", "stop_loss": "0.05", "close_time": "30"},
            "optimize": {"entry_time": "range(1615,1645,5)", "take_profit": "[0.004, 0.005, 0.006]", "stop_loss": "[0.04, 0.05, 0.06]", "close_time": "[0, 30, 60]"},
            "process_mode": "yearly"
        }
    
    with open(params_file, 'r') as file:
        return json.load(file)

def save_params(params, currency_pair):
    params_file = get_params_file(currency_pair)
    with open(params_file, 'w') as file:
        json.dump(params, file, indent=4)

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

def get_user_input(years):
    root = Tk()
    root.title("Backtest or Optimize")
    root.geometry("600x500")

    # 通貨ペアの選択を追加
    currency_pairs = get_available_currency_pairs(DATA_FOLDER)
    currency_pair_var = StringVar(value=currency_pairs[0] if currency_pairs else "EURJPY")
    
    Label(root, text="Currency Pair:").grid(row=0, column=0)
    OptionMenu(root, currency_pair_var, *currency_pairs).grid(row=0, column=1)

    params = load_params(currency_pair_var.get())

    start_year_var = StringVar(value=params["year_range"]["start_year"] or years[0])
    end_year_var = StringVar(value=params["year_range"]["end_year"] or years[-1])
    mode_var = StringVar(value="Backtest")
    process_mode_var = StringVar(value=params.get("process_mode", "yearly"))

    Label(root, text="Start Year:").grid(row=1, column=0)
    OptionMenu(root, start_year_var, *years).grid(row=1, column=1)

    Label(root, text="End Year:").grid(row=2, column=0)
    OptionMenu(root, end_year_var, *years).grid(row=2, column=1)

    Label(root, text="Mode:").grid(row=3, column=0)
    OptionMenu(root, mode_var, "Backtest", "Optimize").grid(row=3, column=1)

    Label(root, text="Process Mode:").grid(row=4, column=0)
    Radiobutton(root, text="Yearly", variable=process_mode_var, value="yearly").grid(row=4, column=1)
    Radiobutton(root, text="All Data", variable=process_mode_var, value="all_data").grid(row=4, column=2)

    Label(root, text="Backtest Entry Time (e.g., 1630):").grid(row=5, column=0)
    backtest_entry_time_entry = Entry(root)
    backtest_entry_time_entry.insert(0, params["backtest"]["entry_time"])
    backtest_entry_time_entry.grid(row=5, column=1)

    Label(root, text="Backtest Take Profit (e.g., 0.005):").grid(row=6, column=0)
    backtest_take_profit_entry = Entry(root)
    backtest_take_profit_entry.insert(0, params["backtest"]["take_profit"])
    backtest_take_profit_entry.grid(row=6, column=1)

    Label(root, text="Backtest Stop Loss (e.g., 0.05):").grid(row=7, column=0)
    backtest_stop_loss_entry = Entry(root)
    backtest_stop_loss_entry.insert(0, params["backtest"]["stop_loss"])
    backtest_stop_loss_entry.grid(row=7, column=1)

    Label(root, text="Backtest Close Time (e.g., 30):").grid(row=8, column=0)
    backtest_close_time_entry = Entry(root)
    backtest_close_time_entry.insert(0, params["backtest"]["close_time"])
    backtest_close_time_entry.grid(row=8, column=1)

    Label(root, text="Optimize Entry Time Range (e.g., range(1615,1645,5))").grid(row=9, column=0)
    optimize_entry_time_entry = Entry(root)
    optimize_entry_time_entry.insert(0, params["optimize"]["entry_time"])
    optimize_entry_time_entry.grid(row=9, column=1)

    Label(root, text="Optimize Take Profit Values (e.g., [0.004, 0.005, 0.006])").grid(row=10, column=0)
    optimize_take_profit_entry = Entry(root)
    optimize_take_profit_entry.insert(0, params["optimize"]["take_profit"])
    optimize_take_profit_entry.grid(row=10, column=1)

    Label(root, text="Optimize Stop Loss Values (e.g., [0.04, 0.05, 0.06])").grid(row=11, column=0)
    optimize_stop_loss_entry = Entry(root)
    optimize_stop_loss_entry.insert(0, params["optimize"]["stop_loss"])
    optimize_stop_loss_entry.grid(row=11, column=1)

    Label(root, text="Optimize Close Times (e.g., [0, 30, 60])").grid(row=12, column=0)
    optimize_close_time_entry = Entry(root)
    optimize_close_time_entry.insert(0, params["optimize"]["close_time"])
    optimize_close_time_entry.grid(row=12, column=1)

    def submit():
        currency_pair = currency_pair_var.get()
        params = {
            "year_range": {
                "start_year": start_year_var.get(),
                "end_year": end_year_var.get()
            },
            "backtest": {
                "entry_time": backtest_entry_time_entry.get(),
                "take_profit": backtest_take_profit_entry.get(),
                "stop_loss": backtest_stop_loss_entry.get(),
                "close_time": backtest_close_time_entry.get()
            },
            "optimize": {
                "entry_time": optimize_entry_time_entry.get(),
                "take_profit": optimize_take_profit_entry.get(),
                "stop_loss": optimize_stop_loss_entry.get(),
                "close_time": optimize_close_time_entry.get()
            },
            "process_mode": process_mode_var.get()
        }
        save_params(params, currency_pair)
        
        root.destroy()
        main(currency_pair, 
             (int(params["year_range"]["start_year"]), int(params["year_range"]["end_year"])), 
             mode_var.get(), params["backtest"], params["optimize"], params["process_mode"])

    Button(root, text="Submit", command=submit).grid(row=13, column=0, columnspan=2, pady=5)
    root.mainloop()

def load_data(currency_pair, start_year, end_year, data_folder=DATA_FOLDER):
    all_data = []

    for year in range(start_year, end_year + 1):
        year_str = str(year)
        zip_files = [f for f in os.listdir(data_folder) if f.startswith(currency_pair) and f.endswith('.zip') and year_str in f]

        for zip_file in zip_files:
            with zipfile.ZipFile(os.path.join(data_folder, zip_file)) as z:
                for csv_file in z.namelist():
                    if not csv_file.endswith('.csv'):
                        continue
                    parts = csv_file.split('/')
                    if len(parts) > 1 and parts[0].endswith('_EX') == False:  # "EURJPY_202301.zip/202301/EURJPY_20230102.csv" の場合確認
                        with z.open(csv_file) as f:
                            df = pd.read_csv(f, usecols=[0,1,2,3,4],encoding=ENCODING)
                            df.columns = ["Datetime", "BID_Open", "BID_High", "BID_Low", "BID_Close"
                                        #   ,"ASK_Open", "ASK_High", "ASK_Low", "ASK_Close"
                                          ]
                            # df['Datetime'] = pd.to_datetime(df['Datetime'], format='%Y/%m/%d %H:%M:%S')  # 新しいフォーマットで変換
                            df['Datetime'] = df['Datetime'].apply(convert_to_ny_time)
                            df['Datetime'] = pd.to_datetime(df['Datetime'])
                           
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

def process_data(currency_pair, data, mode, backtest_params, optimize_params, period):
    if not data.empty:
        if mode == "Backtest":
            print(f"--- Running Backtest for {currency_pair} {period} ---")
            stats = backtest_strategy(
                data,
                backtest_params['entry_time'],
                backtest_params['take_profit'],
                backtest_params['stop_loss'],
                backtest_params['close_time']
            )
            
            with open(f'output/{currency_pair}_backtest_results_{period}.txt', 'w') as file:
                print(f"Entry Time: {backtest_params['entry_time']}, Take Profit: {backtest_params['take_profit']}, "
                      f"Stop Loss: {backtest_params['stop_loss']}, Close Time: {backtest_params['close_time']}", file=file)
                print(f'-----------------------------------------------------------------',file=file)
                print(stats, file=file)
                
            stats['_trades'].to_csv(f'output/{currency_pair}_trades_{period}.csv', index=False)

        elif mode == "Optimize":
            print(f"--- Running Optimization for {currency_pair} {period} ---")
            best_stats = optimize_strategy(
                data,
                optimize_params['entry_time'],
                optimize_params['take_profit'],
                optimize_params['stop_loss'],
                optimize_params['close_time']
            )

            if len(best_stats) > 0:
                with open(f'output/{currency_pair}_optimization_results_{period}.txt', 'w') as file:
                    print(f"Best result for {currency_pair} {period}:", file=file)
                    print(best_stats.to_string(), file=file)
                    print(best_stats['_strategy'], file=file)
                    print(f'Optimize parameters :',file=file)
                    print(f'-----------------------------------------------------------------',file=file)
                    print(optimize_params,file=file)

class MyStrategy(Strategy):
    entry_time = 1630
    take_profit = 0.005
    stop_loss = 0.05
    close_time = 30

    def init(self):
        pass

    def next(self):
        # 金曜日（週末）には取引を行わない
        if self.data.index[-1].weekday() == 4:  # 0 = 月曜日, 4 = 金曜日
            return
                
        if len(self.data) > 0 and self.data.index[-1].hour * 100 + self.data.index[-1].minute == self.entry_time:
            entry_price = self.data.Close[-1]
            sl_price = entry_price - self.stop_loss
            tp_price = entry_price + self.take_profit
            
            if ( (sl_price < entry_price < tp_price) 
                and self.data.index[-1].weekday() != 2 ):   # 0 = 月曜日, 4 = 金曜日
                self.buy(size=SIZE, sl=sl_price, tp=tp_price)

        close_hour = self.close_time // 100
        close_minute = self.close_time % 100
        if self.data.index[-1].hour == close_hour:
            if (close_minute - 3) < self.data.index[-1].minute < (close_minute + 3):
                if self.orders:
                    self.orders.cancel()
                if self.position:
                    self.position.close()

def optimize_strategy(data, entry_time_range, tp_values, sl_values, close_times):
    bt = Backtest(data, MyStrategy, cash=CASH, margin=MARGIN, commission=0.000)
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

    bt = Backtest(data, MyStrategy, cash=CASH, margin=MARGIN, commission=0.000)
    stats = bt.run()
    return stats

def main(currency_pair, year_range, mode, backtest_params, optimize_params, process_mode):
    start_year, end_year = year_range
    data = load_data(currency_pair, start_year, end_year)
    print(data)

    if not os.path.exists('output'):
        os.makedirs('output')

    if process_mode == "yearly":
        for year in range(start_year, end_year + 1):
            year_data = data[data.index.year == year]
            process_data(currency_pair, year_data, mode, backtest_params, optimize_params, year)
    else:  # all_data
        process_data(currency_pair, data, mode, backtest_params, optimize_params, f"{start_year}-{end_year}")

if __name__ == '__main__':
    available_years = get_available_years(DATA_FOLDER)
    get_user_input(available_years)