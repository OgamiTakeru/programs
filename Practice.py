import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import numpy as np
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集

oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")  # クラスの定義

jp_time = datetime.datetime(2023, 5, 29, 19, 20, 00)
euro_time_datetime = jp_time - datetime.timedelta(hours=9)
euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
print(jp_time)
print(euro_time_datetime)
param = {"granularity": "M5", "count": 30, "to": euro_time_datetime_iso}
df = oa.InstrumentsCandles_exe("USD_JPY", param)
# df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)
df_r = df.sort_index(ascending=False)
print(df_r.head(5))


# Figure機能のテスト
inspection_condition = {
    "now_price": 100,  # 現在価格を渡す
    "data_r": df_r,  # 対象となるデータ
    "figure": {"ignore": 1, "latest_n": 2, "oldest_n": 30},
    "macd": {"short": 20, "long": 30},
    "save": False,  # データをCSVで保存するか（検証ではFalse推奨。Trueの場合は下の時刻は必須）
    "time_str": "",  # 記録用の現在時刻
}
ans = f.inspection_candle(inspection_condition)

f1 = ans['figure_result']
f2 = ans['figure_result2']

print(f1['latest_ans']['count'], f1['latest_ans']['data'])
print(f1['oldest_ans']['count'], f1['oldest_ans']['data'])
print(ans['figure_result']['union_ans'])
print(ans['figure_result']['memo'])
cur_gap = f1['oldest_ans']['gap']
print(f1['oldest_ans']['gap'])
print(ans['figure_result']['memo_all'])

print(f2['latest_ans']['count'], f2['latest_ans']['data'])
print(f2['oldest_ans']['count'], f2['oldest_ans']['data'])
print(ans['figure_result2']['union_ans'])
print(ans['figure_result2']['memo'])
bef_gap = f2['oldest_ans']['gap']
print(ans['figure_result2']['memo_all'])

print("kokokara")
if ans['figure_c_o']['c_o_ans'] == 1:
    print(" 発生！！")



# def peaks_collect(df_r):
#     """
#     リバースされたデータフレーム（直近が上）から、極値をN回分求める
#     基本的にトップとボトムが交互になる
#     :return:
#     """
#     peaks = []
#     for i in range(20):
#         # print(" 各調査")
#         ans = f.figure_inspection(df_r)
#         df_r = df_r[ans['count']-1:]
#         if ans['direction'] == 1:
#             # 上向きの場合
#             peak_latest = ans['data'].iloc[0]["inner_high"]
#             peak_oldest = ans['data'].iloc[-1]["inner_low"]
#
#         else:
#             # 下向きの場合
#             peak_latest = ans['data'].iloc[0]["inner_low"]
#             peak_oldest = ans['data'].iloc[-1]["inner_high"]
#
#         temp_all = {
#             'time_latest': ans['data'].iloc[0]['time_jp'],
#             'peak_latest': peak_latest,
#             'time_oldest': ans['data'].iloc[-1]['time_jp'],
#             'peak_oldest': peak_oldest,
#             'direction': ans['direction'],
#             'data': ans['data'],
#             'ans': ans,
#         }
#         peaks.append(temp_all)
#         print(ans['data'].iloc[0]['time_jp'], peak_latest, ans['direction'])
#     return peaks
#
#
# def filter_peaks(peaks, d, n):
#     """
#     引数１はTopBottom情報が混合のPeaks
#     :param d:direction　１かー１。１の場合はトップ、ー１の場合はボトムの抽出
#     :param n:直近何個分のピークを取るか
#     :return:
#     """
#     ans = []
#     max_counter = 0
#     for i in range(len(peaks)):
#         if max_counter >= n:
#             break
#
#         if peaks[i]['direction'] == d:
#             t = {
#                 'time_latest': peaks[i]['time_latest'],
#                 'peak_latest': peaks[i]['peak_latest'],
#                 'direction': peaks[i]['direction'],
#                 'data': peaks[i]['data'],
#                 'count': len(peaks[i]['data']) - 1
#             }
#             # print(peaks[i]['data'])
#             if i+1<len(peaks):
#                 if peaks[i+1]['direction'] == (d * -1):
#                     # 情報を追加する
#                     t['time_oldest'] = peaks[i+1]['time_oldest']
#                     t['peak_oldest'] = peaks[i+1]['peak_oldest']
#                     t['data'] = pd.concat([t['data'], peaks[i+1]['data']], axis=0, ignore_index=True)
#                     t['count'] = t['count'] + len(peaks[i+1]['data'])
#                     # tilt
#                     gap = t['peak_latest']-t['peak_oldest']
#                     t['gap'] = gap
#                     t['tilt'] = round(gap/t['count'], 3)
#             # 結果を格納する
#             ans.append(t)
#             max_counter = max_counter + 1
#     # 表示用
#     print("極値表示")
#     for i in range(len(ans)):
#         p = ans[i]
#         if "time_oldest" in p:
#             print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'], p['count'], p['tilt'],
#                   p['gap'])
#     return ans
#
#
# # 近似線の算出関数メイン
# def inspection_tilt(target_list):
#     """
#     引数は、最新が先頭にある、極値のみを抜いたデータ
#     関数の途中で、過去から先頭に並んでいる状況（通常の関数では、直近から先頭に並んでいる）
#     :return:
#     """
#     target_list_r = list(reversed(target_list))  # 過去を先頭に、並微カエル
#     y = []  # 価格
#     x = []  # 時刻系
#     x_span = 0  # 時系列は０スタート
#     for i in range(len(tops)):
#         p = target_list_r[i]
#         if "time_oldest" in p:
#             print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'], p['count'], p['tilt'],
#                   p['gap'])
#             y.append(p['peak_latest'])  # Y軸方向
#             x.append(x_span)  # X軸方向（時間ではなく、足の数）
#             x_span = x_span + p['count']  # 足の数を増やしていく
#
#     # 近似線の算出
#     x = np.array(x)  # npListに変換
#     y = np.array(y)
#     a, b = reg1dim(x, y)
#     plt.scatter(x, y, color="k")
#     plt.plot([0, x.max()], [b, a * x.max() + b])  # (0, b)地点から(xの最大値,ax + b)地点までの線
#     plt.show()
#     print("並び替え後(最新が最後）")
#     print(y)
#     print(x)
#     print(a, b)
#
# # 近似線の算出の計算
# def reg1dim(x, y):
#     n = len(x)
#     a = ((np.dot(x, y)- y.sum() * x.sum()/n)/
#         ((x ** 2).sum() - x.sum()**2 / n))
#     b = (y.sum() - a * x.sum())/n
#     return a, b
#
#
#
#
# oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
# # 現在価格の取得
# price_dic = oa.NowPrice_exe("USD_JPY")
# gl_now_price_mid = price_dic['mid']  # 念のために保存しておく（APIの回数減らすため）
#
# df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M5', "count": 100}, 1)
#
# # euro_time_datetime = datetime.datetime(2023, 5, 29, 6, 30, 00) - datetime.timedelta(hours=9)
# # euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
# # param = {"granularity": "M5", "count": 30, "to": euro_time_datetime_iso}
# # df = oa.InstrumentsCandles_exe("USD_JPY", param)
#
# df_r = df.sort_index(ascending=False)
#
# # 情報を取得
# peaks = peaks_collect(df_r)
# tops = filter_peaks(peaks, 1, 5)
# bottoms = filter_peaks(peaks, -1, 5)
#
# inspection_tilt(tops)
# inspection_tilt(bottoms)
#
