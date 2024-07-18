
# 1. 変数の初期設定等
Cardi = 100 # カーディナリティ制約
import time
start_time = time.time()



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




# 4. 量子アニーリングで組み入れ銘柄決定
# 4. 1. 目的関数の生成
from amplify import VariableGenerator
gen = VariableGenerator()
q = gen.array("Binary", 2146) # 二値変数
object_f = 0
over_return = []


# 4. 2. CSVファイルからデータ読み込み
import numpy as np
real_cardi = -1 # 銘柄コード除外した分の個数

topix_first = []
with open(f"Cardinality_{Cardi}/topix_first_{Cardi}.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        topix_first.append(row)
topix_first_np = np.array(topix_first[1:], dtype=float)

topix_last = []
with open(f"Cardinality_{Cardi}/topix_last_{Cardi}.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        topix_last.append(row)
topix_last_np = np.array(topix_last[1:], dtype=float)

portfolio_first = []
with open(f"Cardinality_{Cardi}/data_first_{Cardi}.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        portfolio_first.append(row)
        real_cardi = real_cardi + 1
portfolio_first_np = np.array(portfolio_first[1:], dtype=float)

portfolio_last = []
with open(f"Cardinality_{Cardi}/data_last_{Cardi}.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        portfolio_last.append(row)
portfolio_last_np = np.array(portfolio_last[1:], dtype=float)



# 4. 2. 超過リターンの計算
import math
for i in range(12):
    # topix_return = (np.array(topix_last[1][i]) - np.array(topix_first[1][i])) / np.array(topix_first[1][i])
    topix_return = (topix_last_np[0][i] - topix_first_np[0][i]) / topix_first_np[0][i]
    portfolio_return = 0
    for j in range(real_cardi):
        # ここで二値変数q[i]をかける！
        # print("i :", i, ", j :",j)
        portfolio_return = portfolio_return + (portfolio_last_np[j][i] - portfolio_first_np[j][i]) * q[j] / portfolio_first_np[j][i]
    over_return.append(portfolio_return - topix_return)

over_return_ave = np.mean(over_return)
# print(over_return_ave)

mult = 0
for i in range(len(over_return)):
    mult = mult + (over_return[i] - over_return_ave) ** 2
f = mult

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
# print(result.best.objective)
print(f"{q} = {q.evaluate(result.best.values)}")
print("トラッキングエラー : ", math.sqrt(result.best.objective) * 100)


# 実行時間表示
end_time = time.time()
execution_time = end_time - start_time
print(f"実行時間: {execution_time}秒")