import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集
import pandas as pd
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集


# MACDのテスト
oa = oanda_class.Oanda(tk.accountID, tk.access_token, tk.environment)
mid_df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)

print(mid_df)
print("NEST")

test_df = f.add_macd(mid_df)
print(test_df)

# def peaks_collect2(df_r):
#     """
#     リバースされたデータフレーム（直近が上）から、極値をN回分求める
#     基本的にトップとボトムが交互になる
#     :return:
#     """
#     peaks = []
#     for i in range(20):
#         # print(" 各調査")
#         ans = f.range_direction_inspection(df_r)
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
# def peaks_collect(df_r):
#     """
#     リバースされたデータフレーム（直近が上）から、極値をN回分求める
#     基本的にトップとボトムが交互になる
#     :return:
#     """
#     peaks = []
#     for i in range(20):
#         # print(" 各調査")
#         ans = f.range_direction_inspection(df_r)
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
# def filter_peaks(peaks, d):
#     """
#     引数１はTopBottom情報が混合のPeaks
#     引数2は１かー１。１の場合はトップ、ー１の場合はボトムの抽出
#     :param d:
#     :return:
#     """
#     ans = []
#     for i in range(len(peaks)):
#         if peaks[i]['direction'] == d:
#             t = {
#                 'time_latest': peaks[i]['time_latest'],
#                 'peak_latest': peaks[i]['peak_latest'],
#                 'direction': peaks[i]['direction'],
#                 'data': peaks[i]['data'],
#                 'count': len(peaks[i]['data'])
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
#     return ans
#
#
# oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")
# # 現在価格の取得
# price_dic = oa.NowPrice_exe("USD_JPY")
# gl_now_price_mid = price_dic['mid']  # 念のために保存しておく（APIの回数減らすため）
#
# df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": 'M5', "count": 100}, 1)
# print(df)
#
# df_r = df.sort_index(ascending=False)
# df_r = df
#
# peaks = peaks_collect(df_r)
# tops = filter_peaks(peaks, 1)
# bottoms = filter_peaks(peaks, -1)
#
# print("Tops")
# for i in range(len(tops)):
#     p = tops[i]
#     if "time_oldest" in p:
#         print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'],p['count'],p['tilt'],p['gap'])
#         # print(tops[i])
#
# print("bottoms")
# for i in range(len(bottoms)):
#     p = bottoms[i]
#     if "time_oldest" in p:
#         print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'],p['count'],p['tilt'],p['gap'])
#         # print(tops[i])

# 直近４個づつで、特徴のある形状を探す
# (1)平行上り







# def inspection_candle(ins_condition):
#     """
#     オーダーを発行するかどうかの判断。オーダーを発行する場合、オーダーの情報も返却する
#     ins_condition:探索条件を辞書形式（ignore:無視する直近足数,latest_n:直近とみなす足数)
#     返却値：辞書形式で以下を返却
#     inspection_ans: オーダー発行有無（０は発行無し。０以外は発行あり）
#     datas: 更に辞書形式が入っている
#             ans: ０がオーダーなし
#             orders: オーダーが一括された辞書形式
#             info: 戻り率等、共有の情報
#             memo: メモ
#     """
#     # 直近データの解析
#     ignore = ins_condition['ignore']  # ignore=1の場合、タイミング次第では自分を入れずに探索する（正）
#     dr_latest_n = ins_condition['latest_n']  # 2
#     dr_oldest_n = 10
#     latest_df = df_r[ignore: dr_latest_n + ignore]  # 直近のn個を取得
#     oldest_df = df_r[dr_latest_n + ignore - 1: dr_latest_n + dr_oldest_n + ignore - 1]  # 前半と１行をラップさせる。
#     # print("  [ins_can]", latest_df.iloc[0]["time_jp"], latest_df.iloc[-1]["time_jp"])
#     # Latestの期間を検証する
#     latest_ans = f.range_direction_inspection(latest_df)  # 何連続で同じ方向に進んでいるか（直近-1まで）
#     # Oldestの期間を検証する
#     oldest_ans = f.range_direction_inspection(oldest_df)  # 何連続で同じ方向に進んでいるか（前半部分）
#     # LatestとOldestの関係性を検証する
#     ans = f.compare_ranges(oldest_ans, latest_ans, gl_now_price_mid)  # 引数順注意。ポジ用の価格情報取得（０は取得無し）
#
#     return {"ans": ans["ans"], "ans_info": ans["ans_info"], "memo": ans['memo'],
#             "type_info": latest_ans['type_info'],  "type_info_old": oldest_ans['type_info'],
#             "latest_ans": latest_df, "oldest_ans": oldest_df}
#

# ans_dic = inspection_candle({"ignore": 1, "latest_n": 3})  # 状況を検査する（買いフラグの確認）
# print(ans_dic)

# later_info = f.range_direction_inspection(df_r)
# print("LATER")
# print(later_info)
#
# df_r = df_r[later_info['count']-1:]
# middle_info = f.range_direction_inspection(df_r)
# print("MIDDLE")
# print(middle_info)
#
# df_r = df_r[middle_info['count']-1:]
# older_info = f.range_direction_inspection(df_r)
# print("OLDER")
# print(older_info)
#
# mo_ratio = round(middle_info['gap']/older_info['gap'], 2)  # middleとoldのGapの比率
# print("Older from:", older_info['oldest_time_jp'], older_info['gap'])
# print("Midle from:", middle_info['oldest_time_jp'], middle_info['gap'])
# print("Later from:", later_info['oldest_time_jp'], later_info['gap'])
# older_count = older_info['count']
# if mo_ratio < 0.5:
#     print("成立", mo_ratio, middle_info['gap'], older_info['gap'], older_count)
# else:
#     print(" 未達", mo_ratio, middle_info['gap'], older_info['gap'], older_count)