import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchWindowException
import time

class Download:
    C_MAP = {
    '金スポット':'SPOT_GOLD',
    '銀スポット':'SPOT_SILVER',
    '日本225':'JP225',
    '日本TPX':'JPTOPIX',
    '米国30':'US30',
    '米国S500':'US500',
    '米国NQ100':'USTEC',
    '米国NQ100ミニ':'USTECMINI',
    '米国RS2000':'US2000',
    '上海A50':'CHNA50',
    '香港H':'HK',
    'イギリス100':'UK100',
    'ユーロ50':'EURO_50_Index',
    'ドイツ40':'GER40',
    'フランス40':'CAC40_Index_Futures',
    '米国VI':'vix',
    'WTI原油':'WTI',
    '北海ブレント':'Brent',
    '天然ガス':'Natural_Gas',
    'ガソリン':'RBOB_Gasoline_Futures',
    'ヒーティングオイル':'Heating_Oil_Futures',
    '銅先物':'Copper_Futures',
    '鉄鉱石':'Iron_Ore_Futures',
    'コーン':'CORN',
    '大豆':'SOY',
    '小麦':'Wheat_Futures',
    '砂糖':'Sugar_futures',
    'ココア':'Cocoa_futures',
    'コーヒー':'Coffee_C_R_Futures',
    'コットン':'Cotton',
    '牛肉':'Live_Cattle_Futures',
    '豚肉':'Lean_Hog_Futures'
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
            self.main_window = driver.current_window_handle
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.logout()
        
        def wait_for_user_navigation(self):
            wait = WebDriverWait(self, 15)  # 5秒間待機
            
            def find_cfd_window(self):
                try:

                    # ヒストリカルデータのアイコンがクリック可？
                    histBtn = self.driver.find_elements(By.ID, "id_historicalDataButton")
                    if histBtn:
                        for btn in histBtn:
                            if btn.is_enabled():
                                btn.click()
                                time.sleep(5)

                                for handle in self.driver.window_handles:
                                    if handle != self.main_window:
                                        self.driver.switch_to.window(handle)
                                        if "CFDレート 過去データ｜GMOクリック証券" in self.driver.title:
                                            return True
                                self.driver.switch_to.window(self.main_window)

                except NoSuchWindowException:
                    return False
                return False

            try:
                wait.until(find_cfd_window)
            except TimeoutException:
                messagebox.showerror("エラー", "CFDヒストリカルデータページが見つかりませんでした。")
                raise
        
        def downtest(self, year, par, to="./"):
            print("DEBUG>>> year=" + str(year) + " par=" + par)
            # 年のリストボックスを見つけて値を更新
            select_element = self.driver.find_element(By.NAME, 'y')
            select = Select(select_element)
            select.select_by_value(str(year))

            # 送信ボタンを見つけてクリック
            submit_button = self.driver.find_element(By.CSS_SELECTOR, 'form[name="f"]')
            submit_button.submit()

            # "金スポット"のテキストを持つ行を見つける
            x_str = "//tbody//td[@class='col01' and text()[contains(., '" + par + "')]]"
            print("DEBUG>>" + x_str)
            row = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, x_str))
            ).find_element(By.XPATH, "..")  # 行全体を取得

            # <a>タグを順番にクリックします
            links = row.find_elements(By.TAG_NAME, 'a')
            for link in links:
                print("DEBUG>>> clicking on " + link.text + " for " + par)
                link.click()
                time.sleep(5)  # 数秒待機
        
        def logout(self):
            try:
                self.driver.switch_to.window(self.main_window)
                self.driver.get("https://sec-sso.click-sec.com/loginweb/sso-logout")
            except Exception as e:
                print(f"ログアウト中にエラーが発生しました: {e}")
            finally:
                self.driver.quit()

def save_settings(userid, password, pair, start_year, end_year, download_dir):
    with open(".settingsCFD", "w") as file:
        file.write(f"{userid}\n")
        file.write(f"{password}\n")
        file.write(f"{pair}\n")
        file.write(f"{start_year}\n")
        file.write(f"{end_year}\n")
        file.write(f"{download_dir}\n")

def load_settings():
    if os.path.exists(".settingsCFD"):
        with open(".settingsCFD", "r") as file:
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
    root.title("CFDヒストリカルデータダウンローダー")
    root.geometry("600x400")

    title_label = tk.Label(root, text="クリック証券 CFDヒストリカルデータ・一括ダウンロード", font=("Helvetica", 14, "bold"))
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

    ttk.Label(frame, text="CFD商品:").grid(row=2, column=0, sticky=tk.W, pady=10)
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
        try:
            with Download.session(userid, password, download_dir) as session:
                # CFDページを開く (最上部のCFDアイコンのクリック)
                session.driver.find_element(By.ID, "cfdMenu").click()

                # "CFDが初めての方へ"ダイアログをユーザーが閉じるのを待つ
                session.wait_for_user_navigation()  

                for year in range(start_year, end_year + 1):
                    month = 10
                    session.downtest(year, pair, to=download_dir)
                    time.sleep(5)

            messagebox.showinfo("完了", f"ダウンロードが完了しました。\n保存先: {download_dir}")
        except Exception as e:
            messagebox.showerror("エラー", f"ダウンロード中にエラーが発生しました: {str(e)}")
        finally:
            root.quit()

    submit_button = ttk.Button(frame, text="ダウンロード開始", command=on_submit)
    submit_button.grid(row=6, column=0, columnspan=3, pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()