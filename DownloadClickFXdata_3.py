from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import tkinter as tk
from tkinter import simpledialog, ttk


class Download:
    C_MAP = {
        'USDJPY': "21", 'EURJPY': "22", 'GBPJPY': "23",
        'AUDJPY': "24", 'NZDJPY': "25", 'CADJPY': "26",
        'CHFJPY': "27", 'ZARJPY': "29", 'EURUSD': "31",
        'GBPUSD': "32", 'EURCHF': "39", 'GBPCHF': "40",
        'USDCHF': "41"
    }

    @staticmethod
    def session(userid, password, proxy=None):
        options = webdriver.ChromeOptions()
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        driver = webdriver.Chrome(options=options)
        login_url = "https://sec-sso.click-sec.com/loginweb/"
        driver.get(login_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "j_username")))
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
            url = f"https://tb.click-sec.com/fx/historical/historicalDataDownload.do?y={year}&m={str(month).zfill(2)}&c={Download.C_MAP[pair]}&n={pair}"
            self.driver.get(url)
            time.sleep(5)  # ダウンロードが完了するのを待つ

        def logout(self):
            self.driver.get("https://sec-sso.click-sec.com/loginweb/sso-logout")
            self.driver.quit()

def save_settings(userid, password, pair, start_year, end_year):
    with open(".settings", "w") as file:
        file.write(f"{userid}\n")
        file.write(f"{password}\n")
        file.write(f"{pair}\n")
        file.write(f"{start_year}\n")
        file.write(f"{end_year}\n")

def load_settings():
    if os.path.exists(".settings"):
        with open(".settings", "r") as file:
            lines = file.readlines()
            if len(lines) == 5:
                return lines[0].strip(), lines[1].strip(), lines[2].strip(), lines[3].strip(), lines[4].strip()
    return "", "", "", "", ""

def main():
    root = tk.Tk()
    root.title("ダウンロード設定")
    userid, password, pair, start_year, end_year = load_settings()

    tk.Label(root, text="ユーザーID:").grid(row=0, column=0, padx=10, pady=5)
    userid_entry = tk.Entry(root)
    userid_entry.insert(0, userid)
    userid_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(root, text="パスワード:").grid(row=1, column=0, padx=10, pady=5)
    password_entry = tk.Entry(root, show='*')
    password_entry.insert(0, password)
    password_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(root, text="為替ペア:").grid(row=2, column=0, padx=10, pady=5)
    pair_combobox = ttk.Combobox(root, values=list(Download.C_MAP.keys()))
    pair_combobox.set(pair)
    pair_combobox.grid(row=2, column=1, padx=10, pady=5)

    tk.Label(root, text="開始年:").grid(row=3, column=0, padx=10, pady=5)
    start_year_entry = tk.Entry(root)
    start_year_entry.insert(0, start_year)
    start_year_entry.grid(row=3, column=1, padx=10, pady=5)

    tk.Label(root, text="終了年:").grid(row=4, column=0, padx=10, pady=5)
    end_year_entry = tk.Entry(root)
    end_year_entry.insert(0, end_year)
    end_year_entry.grid(row=4, column=1, padx=10, pady=5)

    def on_submit():
        userid = userid_entry.get()
        password = password_entry.get()
        pair = pair_combobox.get()
        start_year = int(start_year_entry.get())
        end_year = int(end_year_entry.get())
        save_settings(userid, password, pair, start_year, end_year)
        with Download.session(userid, password) as session:
            for year in range(start_year, end_year + 1):
                for month in range(1, 13):
                    session.download(year, month, pair)
        root.quit()

    submit_button = tk.Button(root, text="ダウンロード開始", command=on_submit)
    submit_button.grid(row=5, column=0, columnspan=2, pady=10)
    root.mainloop()

if __name__ == "__main__":
    main()
