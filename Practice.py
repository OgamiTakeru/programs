import programs.main_functions as f  # とりあえずの関数集
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import numpy as np
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集

oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, "live")  # クラスの定義

jp_time = datetime.datetime(2023, 8, 12, 5, 10, 00)
euro_time_datetime = jp_time - datetime.timedelta(hours=9)
euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
param = {"granularity": "M5", "count": 50, "to": euro_time_datetime_iso}  # 最低５０行
df = oa.InstrumentsCandles_exe("USD_JPY", param)
df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 直近の場合
df = df["data"]
df.to_csv(tk.folder_path + 'TEST.csv', index=False, encoding="utf-8")  # 直近保存用
df_r = df.sort_index(ascending=False)
print(df_r.head(5))
print(df_r.tail(5))
print("↓↓")
### ↑これより上は消さない

# class order_information:
#     def __init__(self):
#         self.plan = {
#             "base_price": 144.938,
#             "price": 144.938,  # target_priceの事
#             "margin": 0,  # ここでは±あり
#             "direction": -1,
#             "type": "STOP",
#             "lc_range": 0.03,  # ±情報あり　⇒ただし参考用で、クラス内でLCpriceを求める時には±情報不要！
#             "tp_range": 0.03  # ±情報あり
#         }
#         self.order = {"id": 0, "state": "", "time_past": 0}  # オーダー情報 (一部初期値必要）
#         self.position = {"id": 0, "state": "", "time_past": 0, "pips": 0}
#         self.order_permission = False
#         self.life = False
#         self.plan_life = True
#
#     def order_plan_registration(self):  # (self, plan):
#         """
#         【最重要】
#         【最初】オーダー計画情報をクラスに登録する（保存する）。名前やCDCRO情報があれば、その登録含めて行っていく。
#         :param plan:units,ask_bid,price,tp_range,lc_range,type,tr_range は必須。それ以外は任意。
#         :return:
#         """
#
#         # (1)クラスの名前を付ける (引数で指定されている場合）
#         # if 'name' in plan:
#         #     self.name = plan['name']  # 名前を入れる(クラス内の変更）
#
#         # (2)各フラグを指定しておく
#         self.order_permission = True  # 即時のオーダー判断に利用する
#
#         # (3-1) 付加情報１　各便利情報を格納しておく
#         self.plan['lc_price'] = round(self.plan['price'] -
#                                       (abs(self.plan['lc_range']) * self.plan['direction']), 3)
#         self.plan['tp_price'] = round(self.plan['price'] +
#                                       (abs(self.plan['tp_range']) * self.plan['direction']), 3)
#         self.plan['target_price'] = self.plan['margin'] + self.plan['price']
#
#         if self.order_permission:
#             self.make_order()
#
#     def make_order(self, data):
#         # self.order['id'] = 1  # orderIDを代入（これでアリと認識する
#         # self.order['state'] = "PENDING"
#         # self.life = True
#         self.order = {  # 成立情報を取り込む
#             "price": self.plan['target_price'],  # オーダー価格はここでのみ取得
#             "id": 1,
#             "time": data['time_jp'],  # いつに使用？
#             "cancel": 0,
#             "state": "PENDING",  # 強引だけど初期値にPendingを入れておく
#             "tp_price": self.plan['tp_price'],
#             "lc_price": self.plan['lc_price'],
#             "units": self.plan['units'],
#             "direction": self.plan['direction'],
#             "tp_range": self.plan['tp_range'],
#             "lc_range": self.plan['lc_range']
#         }
#
#     def update_information(self, data):
#         # オーダーを取得する（オーダー許可有&オーダー発行済
#         if self.order_permission and self.life and self.order['state'] == "PENDING":  # orderid=0
#             if data['low'] <= self.plan['target_price'] <= data['high']:
#                 print(" 取得", data['time_jp'])
#                 self.order['state'] = "FILLED"
#                 self.position['state'] = "OPEN"
#                 self.position['time'] = data['time_jp']
#             else:
#                 print(" 範囲無し")
#         else:
#             print(" 未合致", self.order_permission, self.life, self.order['state'])
#
#         # オーダーを解消する　(同時の場合はマイナスが優先）
#         if self.life and self.order['state'] == "FILLED" and self.position['state'] == "OPEN":
#             if data['low'] <= self.plan['lc_price'] <= data['high']:
#                 print(" LC入ります", data['time_jp'])
#                 self.position['state'] = "CLOSED"
#                 self.position['close_time'] = data['time_jp']
#                 self.life = False
#             elif data['low'] <= self.plan['tp_price'] <= data['high']:
#                 print(" TP入ります", data['time_jp'])
#                 self.position['state'] = "CLOSED"
#                 self.position['close_time'] = data['time_jp']
#                 self.life = False
#
#         res = {
#             "func_complete": 0,  # APIエラーなく完了しているかどうか
#             "order_id": 1,
#             "order_time": self.order['time'],
#             "order_time_past": cal_past_time_single(iso_to_jstdt_single(res_json['order']['createTime'])),
#             "order_units": res_json['order']['units'],
#             "order_price": order_price,  # Marketでは存在しない
#             "order_state": res_json['order']['state'],
#             "position_id": position_id,
#             "position_type": position_type,  # 両建てや部分解消の場合「group」が入る。
#             "position_initial_units": position_initial_units,
#             "position_current_units": position_current_units,
#             "position_time": position_time,
#             "position_time_past": cal_past_time_single(position_time) if position_time != 0 else 0,
#             "position_price": position_price,
#             "position_state": position_state,
#             "position_realize_pl": position_realize_pl,
#             "position_pips": pips,
#             "position_close_time": position_close_time,
#             "position_close_price": position_close_price
#         }
#
#
# def exe_manage():
#     count = 0  # 呼び出す列（経過時間と同等）
#     for i in range(10):
#         target = df.iloc[count]
#         print(target['time_jp'])
#         test_order.update_information(target)
#         count += 1
#
# test_order = order_information()
# test_order.order_plan_registration()
# test_order.make_order()
# print(test_order.plan)
# exe_manage()


def peaks_collect(df_r):
    """
    リバースされたデータフレーム（直近が上）から、極値をN回分求める
    基本的にトップとボトムが交互になる
    :return:
    """
    peaks = []
    for i in range(20):
        # print(" 各調査")
        ans = f.turn_each_inspection_skip(df_r)
        df_r = df_r[ans['count']-1:]
        if ans['direction'] == 1:
            # 上向きの場合
            peak_latest = ans['data'].iloc[0]["inner_high"]
            peak_oldest = ans['data'].iloc[-1]["inner_low"]

        else:
            # 下向きの場合
            peak_latest = ans['data'].iloc[0]["inner_low"]
            peak_oldest = ans['data'].iloc[-1]["inner_high"]

        temp_all = {
            'time': ans['data'].iloc[0]['time_jp'],
            'peak': peak_latest,
            'time_oldest': ans['data'].iloc[-1]['time_jp'],
            'peak_oldest': peak_oldest,
            'direction': ans['direction'],
            'body_ave': ans['body_ave'],
            'count': len(ans["data"])
            # 'data': ans['data'],
            # 'ans': ans,
        }
        peaks.append(temp_all)  # 全部のピークのデータを取得する

    # 一番先頭[0]に格納されたピークは、現在＝自動的にピークになる物となるため、
    print(peaks)
    print(peaks[1:])
    # 直近のピークまでのカウント（足数）を求める
    from_last_peak = peaks[0]
    # 最新のは除外しておく（余計なことになる可能性もあるため）
    peaks = peaks[1:]
    # 上、下のピークをグルーピングする
    top_peaks = []
    bottom_peaks = []
    for i in range(len(peaks)):
        if peaks[i]['direction'] == 1:
            # TopPeakの場合
            top_peaks.append(peaks[i])  # 新規に最後尾に追加する
        else:
            # bottomPeakの場合
            bottom_peaks.append(peaks[i])

    if from_last_peak['direction'] == 1:
        latest_peak_group = bottom_peaks  # 最新を含む方向性が上向きの場合、直近のピークは谷方向となる
        second_peak_group = top_peaks
    else:
        latest_peak_group = top_peaks
        second_peak_group = bottom_peaks

    return {
        "all_peaks": peaks,
        "tops": top_peaks,
        "bottoms": bottom_peaks,
        "from_last_peak": from_last_peak,  # 最後のPeakから何分経っているか(自身[最新]を含み、lastPeakを含まない）
        "latest_peak_group": latest_peak_group,  # 直近からみて直近のグループ
        "second_peak_group": second_peak_group
    }


def filter_peaks(peaks, d, n):
    """
    引数１はTopBottom情報が混合のPeaks
    :param d:direction　１かー１。１の場合はトップ、ー１の場合はボトムの抽出
    :param n:直近何個分のピークを取るか
    :return:
    """
    ans = []
    max_counter = 0
    for i in range(len(peaks)):
        if max_counter >= n:
            break

        if peaks[i]['direction'] == d:
            t = {  # 基礎データ
                'time_latest': peaks[i]['time_latest'],
                'peak_latest': peaks[i]['peak_latest'],
                'direction': peaks[i]['direction'],
                'data': peaks[i]['data'],
                'body_ave': peaks[i]['body_ave'],
                'count': len(peaks[i]['data']) - 1
            }
            # print(peaks[i]['data'])
            if i+1 < len(peaks):
                if peaks[i+1]['direction'] == (d * -1):
                    # 情報を追加する
                    t['time_oldest'] = peaks[i+1]['time_oldest']
                    t['peak_oldest'] = peaks[i+1]['peak_oldest']
                    t['data'] = pd.concat([t['data'], peaks[i+1]['data']], axis=0, ignore_index=True)
                    t['count'] = t['count'] + len(peaks[i+1]['data'])
                    # tilt
                    gap = t['peak_latest']-t['peak_oldest']
                    t['gap'] = gap
                    t['tilt'] = round(gap/t['count'], 3)
            # 結果を格納する
            ans.append(t)
            max_counter = max_counter + 1
    # 表示用
    print("極値表示")
    ans  # ansは現状上が新しい、下が古いもの ⇒
    counter = 0#
    double_ans = {}
    for i in range(len(ans)):
        p = ans[i]
        counter = counter + p['count']
        if i + 1 < len(ans):
            if abs(p['peak_latest'] - ans[i+1]['peak_latest']) < p['body_ave'] * 1.2 and p['count'] < 15:
                # print("ダブルトップ")
                # print(p['peak_latest'] - ans[i+1]['peak_latest'])
                # print(p['body_ave'], p['count'])
                if "time" in double_ans:   # 一回やったら次は入れない（直近のみを抽出）
                    pass
                else:
                    double_ans['time'] = p['time_latest']
                    double_ans['peak'] = p['peak_latest']
                    double_ans['counter_from_latest'] = counter
        if "time_oldest" in p:
            print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'], p['count'], p['tilt'],
                  p['gap'], p['body_ave'])
    return {"ans": ans, "double": double_ans}


# 近似線の算出関数メイン
def inspection_tilt(target_list):
    """
    引数は、最新が先頭にある、極値のみを抜いたデータ
    関数の途中で、過去から先頭に並んでいる状況（通常の関数では、直近から先頭に並んでいる）
    :return:
    """
    # print("test", target_list)
    target_list_r = target_list
    # target_list_r = list(reversed(target_list))  # 過去を先頭に、並微カエル
    y = []  # 価格
    x = []  # 時刻系
    x_span = 0  # 時系列は０スタート
    for i in range(len(tops)):
        p = target_list_r[i]
        if "time_oldest" in p:
            # print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'], p['count'], p['tilt'],
            #       p['gap'])
            y.append(p['peak_latest'])  # Y軸方向
            x.append(x_span)  # X軸方向（時間ではなく、足の数）
            x_span = x_span + p['count']  # 足の数を増やしていく

    # 近似線の算出
    x = np.array(x)  # npListに変換
    y = np.array(y)
    a, b = reg1dim(x, y)
    plt.scatter(x, y, color="k")
    plt.plot([0, x.max()], [b, a * x.max() + b])  # (0, b)地点から(xの最大値,ax + b)地点までの線
    # plt.show()
    print("並び替え後(最新が最後）")
    print(y)
    print(x)
    print(a, b)
    max_price = max(y)
    min_price = min(y)
    res = {
        "max_price": max_price,
        "min_price": min_price,
        "data": y
    }
    return res


# 近似線の算出の計算
def reg1dim(x, y):
    n = len(x)
    a = ((np.dot(x, y)- y.sum() * x.sum()/n)/
        ((x ** 2).sum() - x.sum()**2 / n))
    b = (y.sum() - a * x.sum())/n
    return a, b


# 情報を取得
peaks = peaks_collect(df_r)
print("★TOPS")
print(peaks['tops'])
print("★Bottoms")
print(peaks['bottoms'])
print("★from_last_peak", peaks['from_last_peak'])
print("★latest")
print(peaks['latest_peak_group'])
print("★second")
print(peaks['second_peak_group'])





# Range関係のテスト
# def range_jd(df_r):
#     df_r = df_r[0:3].copy()
#     df_r = df_r.reset_index()
#     # print(df_r)
#     count = 0
#     # bodyサイズ感がそろっているかを確かめる（そろっている＝レンジの可能性）
#     body_ave = df_r.iloc[0]['body_abs']
#
#     # Bodyサイズのサイズ感の統一感
#     for index, data in df_r.iterrows():
#         # print(index)
#         if body_ave * 0.7 <= df_r.iloc[index]['body_abs'] <= body_ave * 1.3:
#             count = count + 1
#         else:
#             # print("out", df_r.iloc[index]['time_jp'])
#             break
#     if count == len(df_r):
#         # print("Body OK")
#         body = 1
#     else:
#         body = 0
#
#     # Rapの判断
#     rap_count = 0
#     for index, data in df_r.iterrows():
#         if index + 1 < len(df_r):
#             # print("latest", df_r.iloc[index]['time_jp'], df_r.iloc[index+1]['time_jp'])
#             # ラップ状態を計算する
#             latest_high = df_r.iloc[index]['inner_high']
#             latest_low = df_r.iloc[index]['inner_low']
#             oldest_high = df_r.iloc[index+1]['inner_high']
#             oldest_low = df_r.iloc[index+1]['inner_low']
#             # print(latest_high,latest_low,oldest_high,oldest_low)
#             if latest_high > oldest_high:
#                 high = latest_high
#                 mid_high = oldest_high
#             else:
#                 high = oldest_high
#                 mid_high = latest_high
#
#             if latest_low < oldest_low:
#                 low = latest_low
#                 mid_low = oldest_low
#             else:
#                 low = oldest_low
#                 mid_low = latest_low
#
#             rap = mid_high - mid_low
#             rap_ratio = round(body_ave / rap, 3)
#             # print(rap, rap_ratio)
#
#             if rap_ratio >= 0.8:
#                 # print(" RAPあり")
#                 rap_flag = 1
#                 rap_count = rap_count + 1
#             else:
#                 # print("END RAP", df_r.iloc[index]['time_jp'])
#                 rap_flag = 0
#                 break
#     # print("RAP　RAIO", rap_count, len(df_r))
#     len_kai = len(df_r)- 1  # 比較は植木算的には間なので、len-1が必要
#     if rap_count == len_kai:
#         rap_ans = 1
#     else:
#         rap_ans = 0
#
#
#     if body == 1 and rap_ans == 1:
#         print("成立")
#         return 1
#     else:
#         print("非成立")
#         return 0
# range_jd(df_r)