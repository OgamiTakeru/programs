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

# Tokenの設定、クラスの実体化
print("Start")
oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")

# 現在価格の取得
price_dic = oa.NowPrice_exe("USD_JPY")
print("【現在価格live】", price_dic['mid'], price_dic['ask'], price_dic['bid'], price_dic['spread'])

# データの取得
# mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M5', "count": 5000}, 4)
# # mid_df.to_csv(tk.folder_path + 'TEST_DATA.csv', index=False, encoding="utf-8")
# f.draw_graph(mid_df)  # グラフ化
# print(mid_df)

# #データ分析時に規定のデータフレームを切り取る
# inspection_range = 5
# for i in range(len(mid_df)):
#     d = mid_df[len(mid_df)-inspection_range-i : len(mid_df)-i]  # 模擬取得DF。適切な範囲を切り取る（取得時データと同様、下が最新データ)
#     # 最新データから順に拾っていく方式
#     if len(d) >= inspection_range:
#         index_graph = d.index.values[-1]  # ①直近時間のインデックスを取得（この状態だと、末尾のIndexとなる。逆順で解析後に使う事になる）
#         print(len(mid_df)-inspection_range-i, len(mid_df)-i)
#         print(mid_df[len(mid_df)-inspection_range-i : len(mid_df)-i])
#         # ②大体は順番を逆にする（上が新しいデータとしたい）
#         dr = d.sort_index(ascending=False).copy()

# 注文を発行
oa.OrderCreate_exe(10000, 1, price_dic['mid'], 0.05, 0.04, "STOP", 0.05, " ")
