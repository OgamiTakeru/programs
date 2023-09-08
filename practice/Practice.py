import programs.fTurnInspection as f  # とりあえずの関数集
import pandas as pd
import json
import datetime
import matplotlib.pyplot as plt
import numpy as np
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.classOanda as oanda_class
import programs.fTurnInspection as t  # とりあえずの関数集
import programs.fPeakLineInspection as p  # とりあえずの関数集
import programs.fGeneric as f

oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, "live")  # クラスの定義

jp_time = datetime.datetime(2023, 9, 5, 13, 15, 6)
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
peak_information = p.peaks_collect(df_r)
print("★TOPS")
print(peak_information['tops'])
print("★Bottoms")
print(peak_information['bottoms'])
print("★from_last_peak", peak_information['from_last_peak'])
print("★latest")
f.print_arr(peak_information['latest_peak_group'])
print("★second")
f.print_arr(peak_information['second_peak_group'])
print("★★")

latest_flag_figure = p.latestFlagFigure(peak_information)
f.print_json(latest_flag_figure)
