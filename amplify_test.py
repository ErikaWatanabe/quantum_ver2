from amplify import (
    Solver,
    FixstarsClient,
    decode_solution,
    sum_poly,
    Poly,
    VariableGenerator,
    equal_to
)

# 変数の定義
gen = VariableGenerator()
x1, x2, x3 = gen.array("x", 3, "BINARY")

# 目的関数の定義
objective = 2*x1**2 + x2**2 + 3*x3**2 - 2*x1*x2 - 4*x1*x3

# 制約条件の定義
constraint = equal_to(x1 + x2 + x3, 2)

# 制約条件にペナルティを付けてモデルを作成
penalty = 5.0
model = objective + penalty * constraint

# FixstarsClientの設定
client = FixstarsClient()
client.token = "YOUR_TOKEN_HERE"  # あなたのトークンに置き換えてください
client.parameters.timeout = 5000  # タイムアウトを5秒に設定

# ソルバーの実行
solver = Solver(client)
result = solver.solve(model)

# 結果の表示
if len(result) == 0:
    print("No solution found")
else:
    values = result[0].values
    decoded_values = decode_solution(values, (x1, x2, x3))
    print("Solution found:")
    print(f"x1 = {decoded_values[x1]}")
    print(f"x2 = {decoded_values[x2]}")
    print(f"x3 = {decoded_values[x3]}")
    print(f"Objective value: {result[0].energy}")