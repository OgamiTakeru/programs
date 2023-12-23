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
import programs.fTurnInspection as fTurn
import programs.fGeneric as f
import statistics

oa = oanda_class.Oanda(tk.accountIDl, tk.access_tokenl, "live")  # クラスの定義


def add_stdev(peaks):
    """
    引数として与えられたPeaksに対して、偏差値を付与する
    :return:
    """
    # Gapのみを配列に置き換え（いい方法他にある？）
    targets = []
    for i in range(len(peaks)):
        targets.append(peaks[i]['gap'])
    # 平均と標準偏差を算出
    ave = statistics.mean(targets)
    stdev = statistics.stdev(targets)
    # 各偏差値を算出し、Peaksに追加しておく
    for i, item in enumerate(targets):
        peaks[i]["stdev"] = round((targets[i]-ave)/stdev*10+50, 2)

    return peaks


def turn3Rule(df_r):
    """
    １、大きな変動のピーク①を確認
    　・偏差値にして６０程度
    　・直近２時間において最安、最高を更新するようなピーク
    ２，大きなピークの次（１回の折り返し後）、ピーク①の半分以下の戻しであるピーク②が発生
    　・基本的に大きな後は半分も戻らないことが多い気がするが。。
    ３，ピーク②の後、ピーク①の折り返し地点とほぼ同程度までの戻しのピーク③が直近。
    ４，この場合はピーク①の終了価格とピーク②の終了価格のレンジとなる可能性が高い。
    　　＝ピーク③が確定した瞬間に、レンジ方向にトレール注文発行。（ようするにダブルトップorダブルボトムの形）
    :param df_r:
    :return:
    """
    print("TURN3　ルール")
    df_r_part = df_r[:140]  # 検証に必要な分だけ抜き取る
    peaks_info = p.peaks_collect_main(df_r_part)  # Peaksの算出
    peaks = peaks_info['all_peaks']
    peaks = add_stdev(peaks)  # 偏差値を付与する

    # ピークの設定
    peak1 = peaks[3]  # 一番長いピーク（起点）
    peak2 = peaks[2]
    peak3 = peaks[1]
    latest = peaks[0]
    # print(peak1)
    # print(peak2)
    # print(peak3)
    print(latest)
    print(peak3)
    print(peak2)
    print(peak1)

    # 折り返し出来たてを狙う（ピーク③の発見）
    jd_time = True if latest['count'] <= 2 else False
    print(" TIME", jd_time, latest['count'])

    # ピーク１の変動が大きいかどうか
    jd_big = True if peak1['stdev'] > 65 else False
    print(" BIG", jd_big, peak1['stdev'])

    # 大きなピーク(1)後のピーク(2)が、大きなピークの半分以下か。
    jd_ratio = True if peak2['gap'] < (peak1['gap'] / 2) else False
    print(" RATIO", jd_ratio, peak2['gap'], (peak1['gap'] / 2))

    # ピーク(3)の終了価格が、大きなピーク(1)の終了価格の前後の場合（ダブルトップ）  上と下で分けた方がよい？
    range = 0.07  # 許容される最初のピークとの差（小さければ小さいほど理想のダブルトップ形状となる）
    jd_double = True if peak1['peak'] - range < peak3['peak'] < peak1['peak'] + range else False
    print(" DOUBLE", jd_double, peak1['peak'], peak3['peak'], peak2['peak']-peak1['peak'])

    if jd_big and jd_time and jd_ratio and jd_double:
        start_price = latest['peak']
        latest_direction = latest['direction']
        expect_direction = latest['direction']  # * -1
        ans = True
        print("条件達成", expect_direction)
    else:
        start_price = 0
        latest_direction = 0
        expect_direction = 0
        ans = False

    # LC【価格】を確定する（ピーク２(大きいものからの戻りのピーク）の３分の１だけの移動距離　±　ピーク１の直近価格)
    lc_range_temp = peak2['gap'] / 3
    lc_price = peak1['peak'] + (lc_range_temp * peak1['direction'])
    print(" LCcal", peak2['gap'], lc_range_temp)

    # TP【価格】を確定する
    tp_price = 0.06

    return {
        "ans": ans,
        "start_price": start_price,
        "expect_direction": expect_direction,
        "s_time": df_r_part.iloc[0]['time_jp'],
        "lc_price": round(lc_price, 3),
        "tp_price": round(tp_price, 3)  # 今は幅がそのまま入っている
    }


