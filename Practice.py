import programs.main_functions as f  # とりあえずの関数集
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import numpy as np
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.oanda_class as oanda_class
import programs.main_functions as f  # とりあえずの関数集

oa = oanda_class.Oanda(tk.accountID, tk.access_token, "practice")  # クラスの定義

jp_time = datetime.datetime(2023, 6, 23, 12, 00, 00)
euro_time_datetime = jp_time - datetime.timedelta(hours=9)
euro_time_datetime_iso = str(euro_time_datetime.isoformat()) + ".000000000Z"  # ISOで文字型。.0z付き）
param = {"granularity": "M5", "count": 30, "to": euro_time_datetime_iso}
df = oa.InstrumentsCandles_exe("USD_JPY", param)
# df = oa.InstrumentsCandles_multi_exe("USD_JPY", {"granularity": "M5", "count": 30}, 1)  # 直近の場合
df_r = df.sort_index(ascending=False)
print(df_r.head(5))
print(df_r.tail(5))
print("↓↓")
### ↑これより上は消さない



# def jd_yokoyoko(df_r):
#     """
#     :param df_r: リバース（上が
#     :return:
#     """


def peaks_collect_skip(df_r):
    """
    リバースされたデータフレーム（直近が上）から、極値をN回分求める
    基本的にトップとボトムが交互になる.一瞬の戻し（１足分）はスキップできる
    :return:
    """
    peaks = []

    counter = 0
    for i in range(20):
        ans_current = f.figure_turn_each_inspection(df_r)  # 再起用に０渡しておく。。
        if ans_current['direction'] == 1:
            # 上向きの場合
            peak_latest = ans_current['data'].iloc[0]["inner_high"]
            peak_oldest = ans_current['data'].iloc[-1]["inner_low"]
        else:
            # 下向きの場合
            peak_latest = ans_current['data'].iloc[0]["inner_low"]
            peak_oldest = ans_current['data'].iloc[-1]["inner_high"]
        # 情報の収集
        next_from = ans_current['count']-1
        temp_all = {
            'time_latest': ans_current['data'].iloc[0]['time_jp'],
            'peak_latest': peak_latest,
            'time_oldest': ans_current['data'].iloc[-1]['time_jp'],
            'peak_oldest': peak_oldest,
            'direction': ans_current['direction'],
            'data': ans_current['data'],
            'ans': ans_current,
        }

        # (２回目以降の実行）今回のピークブロックが、２個以下の場合は除外検討を行う
        skip = 0
        if counter != 0 and ans_current['count'] <= 2:
            before_direction = peaks[-1]["direction"]  # ひとつ前に調査した方向（時系列的には直近）
            before_open_price = peaks[-1]["peak_oldest"]  # ひとつ前に調査した部分の開始価格
            ans_next = f.figure_turn_each_inspection(df_r[ans_current['count']-1:])  # 一つ先を見る。
            if ans_next['direction'] == before_direction and ans_next['count'] > 2:  # ひとつ前とNextの方向が同じ、２以上
                if ans_next['direction'] == 1:  # 上向きの場合
                    if before_open_price > ans_next['data'].iloc[-1]["inner_low"]:  # 価格が上昇している
                        print("SKIP対象　Up")
                        skip = 1
                else:  # 下向きの場合
                    if before_open_price < ans_next['data'].iloc[-1]["inner_high"]:
                        print("SKIP対象　Down")
                        skip = 1
        if skip == 1:  # スキップ判定があったばあい、DFのリビルド(ひとつ前の物に、今回＋Nextをする）を行い、Next最後尾までスキップ
            before_ans = peaks[-1]
            before_ans['data'] = pd.concat([before_ans['data'], ans_current['data']])  # １行ラップするけど
            before_ans['data'] = pd.concat([before_ans['data'], ans_next['data']])  # １行ラップするけど
            print("Before")
            print(before_ans['data'])

            if before_ans['direction'] == 1:
                # 上向きの場合
                peak_latest = before_ans['data'].iloc[0]["inner_high"]
                peak_oldest = before_ans['data'].iloc[-1]["inner_low"]
            else:
                # 下向きの場合
                peak_latest = before_ans['data'].iloc[0]["inner_low"]
                peak_oldest = before_ans['data'].iloc[-1]["inner_high"]
            # 情報の収集
            temp_all = {
                'time_latest': before_ans['data'].iloc[0]['time_jp'],
                'peak_latest': peak_latest,
                'time_oldest': before_ans['data'].iloc[-1]['time_jp'],
                'peak_oldest': peak_oldest,
                'direction': before_ans['direction'],
                'data': before_ans['data'],
                'ans': "書き換え済み",
            }
            # print(ans_next['data'])
            next_from = next_from + ans_next['count'] - 1
        else:
            # 何もせず、今の情報を追加（スキップしない時のみ）
            peaks.append(temp_all)
        # 次ループへ
        df_r = df_r[next_from:]  # 次の調査対象
        counter += 1
        # print("Next")
        # print(df_r)
        # print("★", ans['data'])
        # print(ans['data'].iloc[0]['time_jp'], peak_latest, ans['direction'])
    for i in range(len(peaks)):
        print(peaks[i]['time_latest'] , "@")
    return peaks


def peaks_collect(df_r):
    """
    リバースされたデータフレーム（直近が上）から、極値をN回分求める
    基本的にトップとボトムが交互になる
    :return:
    """
    peaks = []
    for i in range(20):
        # print(" 各調査")
        ans = f.figure_turn_each_inspection(df_r)
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
            'time_latest': ans['data'].iloc[0]['time_jp'],
            'peak_latest': peak_latest,
            'time_oldest': ans['data'].iloc[-1]['time_jp'],
            'peak_oldest': peak_oldest,
            'direction': ans['direction'],
            'data': ans['data'],
            'ans': ans,
        }
        peaks.append(temp_all)

        # print(ans['data'].iloc[0]['time_jp'], peak_latest, ans['direction'])
    return peaks


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
            t = {
                'time_latest': peaks[i]['time_latest'],
                'peak_latest': peaks[i]['peak_latest'],
                'direction': peaks[i]['direction'],
                'data': peaks[i]['data'],
                'count': len(peaks[i]['data']) - 1
            }
            # print(peaks[i]['data'])
            if i+1<len(peaks):
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
    ans  # ansは現状上が新しい、下が古いもの
    for i in range(len(ans)):
        p = ans[i]
        if "time_oldest" in p:
            print(p['time_latest'], p['peak_latest'], "-", p['time_oldest'], p['peak_oldest'], p['count'], p['tilt'],
                  p['gap'])
    return ans


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


# # 情報を取得
# peaks = peaks_collect(df_r)
# tops = filter_peaks(peaks, 1, 5)
# bottoms = filter_peaks(peaks, -1, 5)
#
# print("結果")
# tops = inspection_tilt(tops)
# bottoms = inspection_tilt(bottoms)
# print(tops)
# print(bottoms)

test = figure_turn_each_inspection_skip(df_r)