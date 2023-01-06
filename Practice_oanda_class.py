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

# ★必須。Tokenの設定、クラスの実体化⇒これ以降、oa.関数名で呼び出し可能
print("Start")
oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")

# # ★現在価格の取得
price_dic = oa.NowPrice_exe("USD_JPY")
print("【現在価格live】", price_dic['mid'], price_dic['ask'], price_dic['bid'], price_dic['spread'])

# ★データの取得（複数一括）
mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M5', "count": 10}, 3)
# mid_df.to_csv(tk.folder_path + 'TEST_DATA.csv', index=False, encoding="utf-8")
# f.draw_graph(mid_df)  # グラフ化
# print(mid_df)

### データチェック用1 ⇒データフレーム各行を巡回し、「各行が最新で取得されるデータだったら(★d)」を検証出来る。
# inspection_range = 5
# now_time_from_df = f.str_to_time(mid_df.iloc[-1]['time'][:26])  # 今何時（英国時間）のデータが最新かを所持しておく（詳細検証データ取得時に利用）
# print(now_time_from_df)
# for i in range(len(mid_df)):
#     d = mid_df[len(mid_df)-inspection_range-i : len(mid_df)-i]  # ★模擬取得DF。適切な範囲を切り取る（取得時データと同様、下が最新データ)
#     # 最新データから順に拾っていく方式
#     if len(d) >= inspection_range:
#         index_graph = d.index.values[-1]  # ①直近時間のインデックスを取得（この状態だと、末尾のIndexとなる。逆順で解析後に使う事になる）
#         print(len(mid_df)-inspection_range-i, len(mid_df)-i)
#         # print(d)
#         # ②大体は順番を逆にする（上が新しいデータとしたい）
#         # ★ここからdに対して何を検証するかを記入！
#         dr = d.sort_index(ascending=False).copy()  # 逆順へ（最新が上）にしたほうがわかりやすい場合！
#         print(dr)
#
#         # 検証用の後続データの取得（dの直近が「8:00:00」の５分足の場合、8:05:00以降の５秒足を取得する
#         foot_minute = 5  # 元データとみなすdが何分足だったかを記録（将来的にはM5とかから５だけを抽出したい）
#         inepection_range = 180  # 100行×5S の検証を行う。
#         # 調査対象の最新行の時刻(time)をdatetimeに変換する（.fromisoformatが使えずやむなく関数を用意）
#         latest_row_time_dt = f.str_to_time(dr.iloc[0]['time'][:26])
#         detail_from_time_dt = latest_row_time_dt + datetime.timedelta(minutes=foot_minute)  # 足分を加算して、検証開始時刻の取得
#         detail_from_time_iso = str(detail_from_time_dt.isoformat()) + ".000000000Z"  # API形式の時刻へ（ISOで文字型。.0z付き）
#         # 検証範囲の取得（inspe_df)（検証開始時刻　＋　５秒×１０００）が、現時刻より前の場合（未来のデータは取得時エラーとなる為注意。）
#         if detail_from_time_dt + datetime.timedelta(seconds=5 * inepection_range) < now_time_from_df:
#             # 正常に取得できる場合
#             print(" 検証開始時刻:", detail_from_time_iso, " 検証必要時刻",
#                   detail_from_time_dt + datetime.timedelta(seconds=5 * inepection_range))
#             detail_df = oa.InstrumentsCandles_each_exe("USD_JPY",
#                                        {"granularity": 'S5', "count": inepection_range,
#                                         "from": detail_from_time_iso})  # ★検証範囲の取得する
#             print(detail_df.head(5))
#         else:
#             # detailが未来になってしまう場合
#             print(" 未来取得不可 検証開始時刻:", detail_from_time_dt, " 検証必要時刻",
#                   detail_from_time_dt + datetime.timedelta(seconds=5 * inepection_range))



# # ★データの取得（単品・Param確認用）
# mid_each_df = oa.InstrumentsCandles_exe("USD_JPY",
#                                         {"granularity": 'S5', "count": 10, "from": "2023-01-03T02:10:00.000000000Z"})
# print(" EACH CANDLE")
# print(mid_each_df)



# # ★注文を発行
oa.OrderCreate_exe(10000, 1, price_dic['mid'], 0.05, 0.09, "STOP", 0.05, " ")
