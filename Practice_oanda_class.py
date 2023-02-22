### 情報取得のテスト

import threading  # 定時実行用
import time
import datetime
import sys
import os
# import requests
import pandas as pd
# 自作ファイルインポート
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import programs.main_functions as f  # とりあえずの関数集
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
from time import sleep
import pytz

# ★必須。Tokenの設定、クラスの実体化⇒これ以降、oa.関数名で呼び出し可能
print("Start")
oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
# oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, "live")

# # ★現在価格の取得
price_dic = oa.NowPrice_exe("USD_JPY")
print("【現在価格live】", price_dic['mid'], price_dic['ask'], price_dic['bid'], price_dic['spread'])



# print("test")
# オーダー番号から、オーダーの行く末を取得する
order_id = 88169  # pending
# order_id = ans['order_id']
order_detail = oa.OrderDetailsState_exe(order_id)  # 詳細の取得
print(order_detail)

test = oa.OrderCancel_exe(order_id)

print(type(test))
if type(test) is int:
    print("の")
else:
    print("OK")



# print(time_jp)

# オーダーブックの取得
# ans = oa.OrderBook_exe(price_dic['mid'])
# print(ans)

# オーダー全部キャンセル（必要な時あり）
# oa.OrderCancel_All_exe()

# オーダー一覧取得(TP/LCなし）
# orders = oa.OrdersWaitPending_exe()

#         print("80")

#
# # オーダー一覧取得（TP/LC含む）
# orders_all = oa.OrdersPending_exe()
# print(orders_all)

# print(oa.OpenTrades_exe())




# ★データの取得（複数一括）
# mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M5', "count": 100}, 1)
# mid_df.to_csv(tk.folder_path + 'TEST_DATA.csv', index=False, encoding="utf-8")
# f.draw_graph(mid_df)  # グラフ化
# print(mid_df)

# オーダー状況確認用
# pending_new_df = oa.OrdersWaitPending_exe()  # ペンディングオーダーの取得(利確注文等は含まない）
# print(pending_new_df)
# pending_new_df.to_csv(tk.folder_path + 'TEST_DATA.csv', index=False, encoding="utf-8")


# # ★データの取得（単品・Param確認用）
# mid_each_df = oa.InstrumentsCandles_exe("USD_JPY",
#                                         {"granularity": 'S5', "count": 10, "from": "2023-01-03T02:10:00.000000000Z"})
# print(" EACH CANDLE")
# print(mid_each_df)



# # ★注文を発行
# oa.OrderCreate_exe(10000, 1, price_dic['mid'], 0.05, 0.09, "STOP", 0.05, " ")



# print(orders)
# bef_order = pd.read_csv(tk.folder_path + 'orders.csv', sep=",", encoding="utf-8")
# print(bef_order)
# ans_dic_arr = []
# counter = 0
# if len(orders) != 0:
#     for index, item in bef_order.iterrows():
#         if len(orders[orders['id'].str.contains(str(item['id']))]) == 0:
#             temp_dic = {
#                 "id": item['id'],
#                 "price": item['price'],
#                 "units": item['units']
#             }
#             ans_dic_arr.append(temp_dic)
#
# print(len(ans_dic_arr))
# for i in range(len(ans_dic_arr)):
#     if ans_dic_arr[i]['units'] == -80:
