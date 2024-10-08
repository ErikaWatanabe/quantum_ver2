# データ取得とアニーリングが一緒の初代版

# 1. 変数の初期設定等
from amplify import VariableGenerator
gen = VariableGenerator()
q = gen.array("Binary", 2146) # 二値変数
Cardi = 100 # カーディナリティ制約



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
from_ = "2022-04-21" # 取得できる期間変わるので定期的に更新しないと
to_ = "2023-03-21"
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

# 3. 3. 月初と月末の株価を2146銘柄分取得
# 時間計測
import time
start_time = time.time()

data = 0
data_close_first = defaultdict(list) # 月初の全銘柄の株価を、月をkeyとして格納
data_close_last = defaultdict(list) # 月末の全銘柄の株価を、月をkeyとして格納
# data_close_first["2022-04"][0]で4月初の0番目の銘柄の株価取得

for key in monthly_data.keys():
    date_first = monthly_data[key][0]
    date_last = monthly_data[key][-1]    

    for i in range(Cardi):
    # for i in range(len(code_2146)):
        res_first = requests.get(f"{url}?code={code_2146[i]}&date={date_first}", headers=headers)
        res_last = requests.get(f"{url}?code={code_2146[i]}&date={date_last}", headers=headers)
        data_first = res_first.json()
        data_last = res_last.json()
        data_close_first[key].append(data_first["daily_quotes"][0]["Close"])
        data_close_last[key].append(data_last["daily_quotes"][0]["Close"])
        # 銘柄コードはcode_2146[i]
    # print(key, "の株価 : ", data_close_first[key], data_close_last[key])



# 3. 4. TOPIXの株価取得
import pandas_datareader.data as web
from datetime import date
import pandas as pd
point_topix = []

source = 'stooq'
dt_s = date(2022, 4, 21)
dt_e = date(2023, 3, 21)
symbol = '^TPX'
df_topix = web.DataReader(symbol, source, dt_s, dt_e)
df_topix = df_topix.sort_values("Date").reset_index()
# print(df_topix.loc[df_topix['Date'] == '2022-04-18', 'Close'].values[0])

for i in range(len(df_topix)):
    point_topix.append(df_topix.at[i, "Close"])

topix_first = defaultdict(list)
topix_last = defaultdict(list)
# 月初・月末のDateの時のCloseを取得
for key in monthly_data.keys():
    date_first = monthly_data[key][0]
    date_last = monthly_data[key][-1]
    topix_first[key].append(df_topix.loc[df_topix['Date'] == date_first, 'Close'].values[0])
    topix_last[key].append(df_topix.loc[df_topix['Date'] == date_last, 'Close'].values[0])
    # print(key, "の月初値", topix_first[key])
    # print(key, "の月末値", topix_last[key])




# 4. 量子アニーリングで組み入れ銘柄決定
# 4. 1. 目的関数の生成
object_f = 0
over_return = []

# 4. 2. 超過リターンの計算
import numpy as np
import math
for key in monthly_data.keys():
    topix_return = (np.array(topix_last[key]) - np.array(topix_first[key])) / np.array(topix_first[key])
    portpholio_return = 0
    for i in range(Cardi):
        # ここで二値変数q[i]をかける！
        portpholio_return = portpholio_return + (data_close_last[key][i] - data_close_first[key][i]) * q[i] / data_close_first[key][i]
    over_return.append(portpholio_return - topix_return)

over_return_ave = np.mean(over_return)
# print(over_return_ave)

mult = 0
for i in range(len(over_return)):
    mult = mult + (over_return[i] - over_return_ave) ** 2
f = mult[0]
print(f)

# object_f = math.sqrt(mult / (Cardi - 1))
# print(object_f)

# 目的関数にルート入れるとバグる、分散の最小化でもいいのかしら



from amplify import FixstarsClient
client = FixstarsClient()
client.token = "AE/VfQDHqAtq9NOTUnJyxWiDTSGa7avMJQe" 
client.parameters.timeout = 1000
from amplify import solve
result = solve(f, client)

print(result.best.values)
print(result.best.objective)
print(f"{q} = {q.evaluate(result.best.values)}")
print("トラッキングエラー : ", math.sqrt(result.best.objective) * 100)


# 実行時間表示
end_time = time.time()
execution_time = end_time - start_time
print(f"実行時間: {execution_time}秒")