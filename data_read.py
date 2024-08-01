
# 1. 変数の初期設定等
from amplify import VariableGenerator
gen = VariableGenerator()
q = gen.array("Binary", 2146) # 二値変数
Cardi = 50 # データの読み込み数



# 2. TOPIX2146銘柄を取得
import csv
with open("topixweight_j.csv") as file:
    lst = list(csv.reader(file))

# データ以外の記述をリストから削除、0～2145までがデータ
lst.pop(0)
last_data = 2145
code_2146 = []
for i in range(18):
    lst.pop( last_data + 1 )

for i in range(len(lst)):
    code_2146.append(lst[i][2])
# print(code_2146) # 2146個の銘柄コード



# 3. 銘柄、購入数の決定
# 3. 1. Jquantsから株価データを取得
import requests
import json

mail_password={"mailaddress":"e.cos2612@outlook.jp", "password":"26Erika12122"}
r_ref = requests.post("https://api.jquants.com/v1/token/auth_user", data=json.dumps(mail_password))
RefreshToken = r_ref.json()["refreshToken"]
r_token = requests.post(f"https://api.jquants.com/v1/token/auth_refresh?refreshtoken={RefreshToken}")
idToken = r_token.json()["idToken"]
headers = {'Authorization': 'Bearer {}'.format(idToken)}

# 3. 2. time_pointを先に取得
time_point = []
from_ = "2022-05-21" # 取得できる期間変わるので定期的に更新しないと
to_ = "2023-04-21"
code_ = "7203"
url = "https://api.jquants.com/v1/prices/daily_quotes"
res = requests.get(f"{url}?code={code_}&from={from_}&to={to_}", headers=headers)
data = res.json()
close_values = [quote["Close"] for quote in data["daily_quotes"]]
for i in range(len(close_values)):
    time_point.append(data["daily_quotes"][i]["Date"])
    
from datetime import datetime
from collections import defaultdict
monthly_data = defaultdict(list)
for date_str in time_point: # 日付を扱いやすいように辞書型に変換
    date = datetime.strptime(date_str, '%Y-%m-%d')
    month_key = date.strftime('%Y-%m')
    monthly_data[month_key].append(date_str)

# 3. 3. 月初と月末の株価を2146銘柄分取得、csvファイルに保存
# 時間計測
import time
import os
folder_path = f"Cardinality_{Cardi}"
os.makedirs(folder_path, exist_ok=True)
print(f"フォルダ '{folder_path}' が作成されました。")
start_time = time.time()

count = 0
month_key_list = []
data_close_first = defaultdict(list) # 月初の全銘柄の株価を、月をkeyとして格納
data_close_last = defaultdict(list) # 月末の全銘柄の株価を、月をkeyとして格納
# data_close_first["2022-04"][0]で4月初の0番目の銘柄の株価取得

for key in monthly_data.keys():
    date_first = monthly_data[key][0]
    date_last = monthly_data[key][-1] 
    month_key_list.append(key)   
    print(key)
    print(count)
    # print(next(iter(monthly_data)))

# 月初、月末の株価取得
    for i in range(Cardi):
        res_first = requests.get(f"{url}?code={code_2146[i]}&date={date_first}", headers=headers)
        res_last = requests.get(f"{url}?code={code_2146[i]}&date={date_last}", headers=headers)
        data_first = res_first.json()
        data_last = res_last.json()
        
        if not data_first["daily_quotes"]: # Jquantsに銘柄コードがない時の例外処理
            if key == next(iter(monthly_data)):
                print(code_2146[i], "はありません、最初なので銘柄コードのみ削除します")
            else:
                print(code_2146[i], "はありません、2ヶ月目以降なのでデータも削除します")
                for key_past in monthly_data.keys(): #これまでのkeyのデータ削除
                    if(key == key_past):
                        break
                    else:
                        data_close_first[key_past].pop(i-1)
                        data_close_last[key_past].pop(i-1)
            code_2146.pop(i)
            i = i-1
            count = count + 1
            continue

        data_close_first[key].append(data_first["daily_quotes"][0]["Close"])
        data_close_last[key].append(data_last["daily_quotes"][0]["Close"])

# 取引高（Volume）の取得
real_cardi = Cardi - count
volume= []
volume_ave = []

for i in range(real_cardi):
    res_volume = requests.get(f"{url}?code={code_2146[i]}&from={from_}&to={to_}", headers=headers)
    data_volume = res_volume.json()
    volume = [quote["Volume"] for quote in data["daily_quotes"]]
    volume_sum = 0
    for j in range(len(volume)):
        volume_sum += volume[i]
    volume_ave.append(volume_sum / len(volume))
# print(volume_ave)


# csvファイルに株価、volumeの書き込み
with open (f"Cardinality_{Cardi}/volume_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(volume_ave)
        
    # print(key, "の株価 : ", data_close_first[key], data_close_last[key])
    
with open (f"Cardinality_{Cardi}/data_first_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    for i in range(real_cardi):
        data_csv = []
        for key in monthly_data.keys():
            data_csv.append(data_close_first[key][i])
        writer.writerow(data_csv)

with open (f"Cardinality_{Cardi}/data_last_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    for i in range(real_cardi):
        data_csv = []
        for key in monthly_data.keys():
            data_csv.append(data_close_last[key][i])
        writer.writerow(data_csv)


# 3. 4. TOPIXの株価取得
import pandas_datareader.data as web
from datetime import date
import pandas as pd
point_topix = []

source = 'stooq'
dt_s = date(2022, 5, 21)
dt_e = date(2023, 4, 21)
symbol = '^TPX'
df_topix = web.DataReader(symbol, source, dt_s, dt_e)
df_topix = df_topix.sort_values("Date").reset_index()
# print(df_topix.loc[df_topix['Date'] == '2022-04-18', 'Close'].values[0])

for i in range(len(df_topix)):
    point_topix.append(df_topix.at[i, "Close"])


# 月初・月末のDateの時のCloseを取得、csvファイルに保存
topix_first = []
topix_last = []

for key in monthly_data.keys():
    date_first = monthly_data[key][0]
    date_last = monthly_data[key][-1]
    topix_first.append(df_topix.loc[df_topix['Date'] == date_first, 'Close'].values[0])
    topix_last.append(df_topix.loc[df_topix['Date'] == date_last, 'Close'].values[0])

with open (f"Cardinality_{Cardi}/topix_first_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    writer.writerow(topix_first)

with open (f"Cardinality_{Cardi}/topix_last_{Cardi}.csv", "w", newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(month_key_list)
    writer.writerow(topix_last)
    


# 実行時間表示
end_time = time.time()
execution_time = end_time - start_time
print(f"実行時間: {execution_time}秒")