import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集


oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")

df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M5', "count": 100}, 1)
print(df)

df_r = df.sort_index(ascending=False)
print("並び替え後")
print(df_r)

# ans = f.range_direction_inspection((df_r))
# print(ans)

print("調査中")
top = []
for i in range(10):
    print(" 各調査")
    ans = f.range_direction_inspection(df_r)
    print(ans)
    df_r = df_r[ans['count']-1:]
    if ans['direction'] == -1:
        if ans['count'] <= 2:
            print("★短すぎるので認めない")
        else:
            print(ans['data'].iloc[0]["inner_high"])
            print(ans['data'].iloc[0]['time_jp'])
        print(" ")
    # print(df_r)