import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class Download:
    C_MAP = {
        'USDJPY': "21", 'EURJPY': "22", 'GBPJPY': "23",
        'AUDJPY': "24", 'NZDJPY': "25", 'CADJPY': "26",
        'CHFJPY': "27", 'ZARJPY': "29", 'EURUSD': "31",
        'GBPUSD': "32", 'EURCHF': "39", 'GBPCHF': "40",
        'USDCHF': "41"
    }
    C_MAP_PRE2015 = {
        'USDJPY': "01", 'EURJPY': "02", 'GBPJPY': "03",
        'AUDJPY': "04", 'NZDJPY': "05", 'CADJPY': "06",
        'CHFJPY': "07", 'ZARJPY': "09", 'EURUSD': "11"
    }

    @staticmethod
    def session(userid, password, download_dir):
        options = webdriver.ChromeOptions()
        prefs = {"download.default_directory": os.path.abspath(download_dir)}
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)
        login_url = "https://sec-sso.click-sec.com/loginweb/"
        driver.get(login_url)
        driver.find_element(By.NAME, "j_username").send_keys(userid)
        driver.find_element(By.NAME, "j_password").send_keys(password)
        driver.find_element(By.NAME, "LoginForm").click()
        return Download.Session(driver)

    class Session:
        def __init__(self, driver):
            self.driver = driver
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.logout()
        def download(self, year, month, pair, to="./"):
            os.makedirs(to, exist_ok=True)
            if year >= 2016:
                url = f"https://tb.click-sec.com/fx/historical/historicalDataDownload.do?y={year}&m={str(month).zfill(2)}&c={Download.C_MAP[pair]}&n={pair}"
            else:
                url = f"https://tb.click-sec.com/fx/historical/historicalDataDownload.do?y={year}&m={str(month).zfill(2)}&c={Download.C_MAP_PRE2015[pair]}&n={pair}"

            self.driver.get(url)
            time.sleep(5)  # ダウンロードが完了するのを待つ
        def logout(self):
            self.driver.get("https://sec-sso.click-sec.com/loginweb/sso-logout")
            self.driver.quit()

def save_settings(userid, password, pair, start_year, end_year, download_dir):
    with open(".settingsFX", "w") as file:
        file.write(f"{userid}\n")
        file.write(f"{password}\n")
        file.write(f"{pair}\n")
        file.write(f"{start_year}\n")
        file.write(f"{end_year}\n")
        file.write(f"{download_dir}\n")

def load_settings():
    if os.path.exists(".settingsFX"):
        with open(".settingsFX", "r") as file:
            lines = file.readlines()
            if len(lines) == 6:
                return [line.strip() for line in lines]
    return ["", "", "", "", "", ""]

def select_directory(entry):
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

def main():
    root = tk.Tk()
    root.title("FXヒストリカルデータダウンローダー")
    root.geometry("600x400")

    title_label = tk.Label(root, text="クリック証券 FXヒストリカルデータ・一括ダウンロード", font=("Helvetica", 14, "bold"))
    title_label.pack(pady=20)

    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    userid, password, pair, start_year, end_year, download_dir = load_settings()

    ttk.Label(frame, text="ユーザーID:").grid(row=0, column=0, sticky=tk.W, pady=10)
    userid_entry = ttk.Entry(frame, width=40)
    userid_entry.insert(0, userid)
    userid_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=10)

    ttk.Label(frame, text="パスワード:").grid(row=1, column=0, sticky=tk.W, pady=10)
    password_entry = ttk.Entry(frame, show='*', width=40)
    password_entry.insert(0, password)
    password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=10)

    ttk.Label(frame, text="為替ペア:").grid(row=2, column=0, sticky=tk.W, pady=10)
    pair_combobox = ttk.Combobox(frame, values=list(Download.C_MAP.keys()), width=38)
    pair_combobox.set(pair)
    pair_combobox.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=10)

    ttk.Label(frame, text="開始年:").grid(row=3, column=0, sticky=tk.W, pady=10)
    start_year_entry = ttk.Entry(frame, width=40)
    start_year_entry.insert(0, start_year)
    start_year_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=10)

    ttk.Label(frame, text="終了年:").grid(row=4, column=0, sticky=tk.W, pady=10)
    end_year_entry = ttk.Entry(frame, width=40)
    end_year_entry.insert(0, end_year)
    end_year_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=10)

    ttk.Label(frame, text="保存先:").grid(row=5, column=0, sticky=tk.W, pady=10)
    download_dir_entry = ttk.Entry(frame, width=40)
    download_dir_entry.insert(0, download_dir)
    download_dir_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=10)
    ttk.Button(frame, text="参照", command=lambda: select_directory(download_dir_entry)).grid(row=5, column=2, pady=10)

    def on_submit():
        userid = userid_entry.get()
        password = password_entry.get()
        pair = pair_combobox.get()
        start_year = start_year_entry.get()
        end_year = end_year_entry.get()
        download_dir = download_dir_entry.get()
        if not all([userid, password, pair, start_year, end_year, download_dir]):
            messagebox.showerror("エラー", "すべての項目を入力してください。")
            return
        try:
            start_year = int(start_year)
            end_year = int(end_year)
        except ValueError:
            messagebox.showerror("エラー", "開始年と終了年は数値で入力してください。")
            return
        save_settings(userid, password, pair, start_year, end_year, download_dir)
        with Download.session(userid, password, download_dir) as session:
            for year in range(start_year, end_year + 1):
                for month in range(1, 12 + 1):
                    session.download(year, month, pair, to=download_dir)
        messagebox.showinfo("完了", f"ダウンロードが完了しました。\n保存先: {download_dir}")
        root.quit()

    submit_button = ttk.Button(frame, text="ダウンロード開始", command=on_submit)
    submit_button.grid(row=6, column=0, columnspan=3, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
