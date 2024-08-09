# 制約条件をコスト関数に入れるもの、()^2の形で

# 1. 変数の初期設定等
Cardi = 500 # データの読み込み数
Cardi_want = 50 # カーディナリティ制約
Budget_want = 500000 # 予算制約
Volume_want = 100000 # 流動性制約
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

volume_ave = []
with open(f"Cardinality_{Cardi}/volume_{Cardi}.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        volume_ave.append(row)
volume_ave_np = np.array(volume_ave, dtype=float)

sector = []
with open(f"Cardinality_{Cardi}/sector_{Cardi}.csv", mode='r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        sector.append(row)
    # print(sector)


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

# 目的関数
mult = 0
for i in range(len(over_return)):
    mult = mult + (over_return[i] - over_return_ave) ** 2
f = mult

# 1. カーディナリティ制約
Cardi_sum = 0
for i in range(real_cardi):
        Cardi_sum += q[i]
f += 0.1 * (Cardi_want - Cardi_sum) ** 2

# 2. 予算の拡充度制約
Budget_sum = 0
for i in range(real_cardi):
        Budget_sum += portfolio_first_np[i][0] * q[i]

f += 0.001 * ((Budget_want - Budget_sum) * 1/10000) ** 2

# 3. 取引の流動性制約
count_volume = 0
true = True
false = False
for i in range(real_cardi):
    if(volume_ave_np[0][i] >= float(Volume_want)):
        count_volume += q[i] * true
    else:
        count_volume += q[i] * false
        # print("20万以下 : ", i)
f += 0.1 * (Cardi_want - count_volume) ** 2


# 4. 産業の構成割合制約
def add_to_dict(key, dict, value):
    if key in dict:
        dict[key] += value
    else:
        dict[key] = value

dict_sector_t = {}
dict_sector_p = {}
for i in range(real_cardi):
    add_to_dict(sector[0][i], dict_sector_t, 1)
    add_to_dict(sector[0][i], dict_sector_p, q[i])

for key in dict_sector_t.keys():
    f += 0.001*(( dict_sector_t[key] / real_cardi ) - ( dict_sector_p[key] / real_cardi )) ** 2






from amplify import FixstarsClient
client = FixstarsClient()
client.token = "AE/VfQDHqAtq9NOTUnJyxWiDTSGa7avMJQe" 
client.parameters.timeout = 1000
from amplify import solve
result = solve(f, client)

# print(result.best.values)
# print(result.best.objective)
# print(f"{q} = {q.evaluate(result.best.values)}")
filtered_result = {str(key).replace('Poly', '').strip('()'): value for key, value in result.best.values.items() if value == 1}
# print(filtered_result)
count_q_equals_one = sum(1 for key, value in result.best.values.items() if value == 1)
print(f"q[i] = 1 の数: {count_q_equals_one}")


Budget_sum = 0
selected_indices = []
volume_result = []

for key, value in result.best.values.items() :
    if value == 1:
        index = str(key).replace('q_', '')
        if not (index.isdigit()):
            index = index.replace('{', '').replace('}', '')
        index = int(index)
        selected_indices.append(index)
print(selected_indices)

# 産業分野の割合、予算合計、流動性の結果計算
dict_sector_p_res = {}
for select_i in selected_indices:
    Budget_sum += portfolio_first_np[select_i][0]
    volume_result.append(volume_ave_np[0][select_i] / 1000)
    add_to_dict(sector[0][select_i], dict_sector_p_res, 1)

import unicodedata
def width_adjusted_string(s, width):
    count = 0
    for char in s:
        if unicodedata.east_asian_width(char) in 'WF':  # 全角
            count += 2
        else:  # 半角
            count += 1
    return s + ' ' * (width - count)
for key in dict_sector_p_res.keys():
    adjusted_key = width_adjusted_string(str(key), 25)
    print(f"{adjusted_key} || TOPIX : {dict_sector_t[key] / real_cardi:.2f} | Portfolio : {dict_sector_p_res[key] / count_q_equals_one:.2f}")


print("Budget_sum:", Budget_sum)
# print("volume_result:", volume_result)
print("float(Volume_want):", float(Volume_want))
print("トラッキングエラー : ", math.sqrt(result.best.objective) * 100)


# 実行時間表示
end_time = time.time()
execution_time = end_time - start_time
print(f"実行時間: {execution_time}秒")

# sum_bu = 0
# for i in range(real_cardi):
#         sum_bu += portfolio_first_np[i][0] * q[i]

# print(sum_bu)