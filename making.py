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
    df_r_part = df_r[:90]  # 検証に必要な分だけ抜き取る
    peaks_info = p.peaks_collect_main(df_r_part)  # Peaksの算出
    peaks = peaks_info['all_peaks']
    peaks = add_stdev(peaks)  # 偏差値を付与する
    f.print_arr(peaks)

    # ピークの設定
    peak_big = peaks[3]  # 一番長いピーク（起点）
    peak2 = peaks[2]
    peak3 = peaks[1]
    latest = peaks[0]
    print(latest)
    print(peak3)
    print(peak2)
    print(peak_big)

    # 折り返し出来たてを狙う（ピーク③の発見）
    jd_time = True if latest['count'] <= 2 else False
    print(" TIME", jd_time, latest['count'])

    # ピーク１の変動が大きいかどうか (かつ３本以上のあしで構成される: １つだけが長いのではなく、継続した移動を捉えたい）
    big_border = 58
    jd_big = True if peak_big['stdev'] > big_border else False
    print(" BIG", jd_big, peak_big['stdev'])

    # 大きなピーク(1)後のピーク(2)が、大きなピークの半分以下か。
    jd_ratio = True if peak2['gap'] < (peak_big['gap'] / 2) else False
    print(" RATIO", jd_ratio, peak2['gap'], (peak_big['gap'] / 2))

    # ピーク(3)の終了価格が、大きなピーク(1)の終了価格の前後の場合（ダブルトップ）  上と下で分けた方がよい？
    range = 0.05  # 許容される最初のピークとの差（小さければ小さいほど理想のダブルトップ形状となる）
    jd_double = True if peak_big['peak'] - range < peak3['peak'] < peak_big['peak'] + range else False
    print(" DOUBLE", jd_double, peak_big['peak'], peak3['peak'], peak3['peak']-peak_big['peak'])

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
    lc_price = peak_big['peak'] + (lc_range_temp * peak_big['direction'])
    print(" LCcal", peak2['gap'], lc_range_temp)

    # TP【価格】を確定する
    tp_price = 0.045

    return {
        "ans": ans,
        "s_time": df_r_part.iloc[0]['time_jp'],
        "start_price": start_price,
        "peakBIG_start": peak_big['time_old'],
        "peakBIG_end": peak_big['time'],
        "peakBIG_Gap": peak_big['gap'],
        "BIG": peak_big['stdev'],
        "peakBigNext_END": peak2['time'],
        "peakReturn": peak3['time'],
        "BIG_JD": jd_big,
        "2FEET": latest['count'],
        "2FEET_JD": jd_time,
        "RETURN_big": peak_big['gap'],
        "RETUEN_big_next": peak2['gap'],
        "RETURN_JD": jd_ratio,
        "PEAK_GAP": peak3['peak']-peak_big['peak'],
        "PEAK_GAP_JD": jd_double,
        "expect_direction": expect_direction,
        "lc_price": round(abs(lc_price), 3),
        "lc_range": round(abs(lc_price - start_price), 3),
        "tp_price": round(tp_price, 3),  # 今は幅がそのまま入っている
        "tp_range": round(tp_price, 3)  # 今は幅がそのまま入っている
    }


def turn1Rule(df_r):
    """
    １、
    :return:
    """
    print("TURN1　ルール")
    df_r_part = df_r[:90]  # 検証に必要な分だけ抜き取る
    peaks_info = p.peaks_collect_main(df_r_part)  # Peaksの算出
    peaks = peaks_info['all_peaks']
    peaks = add_stdev(peaks)  # 偏差値を付与する
    f.print_arr(peaks)
    print("PEAKS↑")

    # 必要なピークを出す
    peak_l = peaks[0]  # 最新のピーク
    peak_o = peaks[1]
    peaks_times = "Old:" + f.delYear(peak_l['time_old']) + "-" + f.delYear(peak_o['time']) + "_" + \
                  "Latest:" + f.delYear(peak_o['time_old']) + "-" + f.delYear(peak_o['time'])
    print("対象")
    print(peak_o)
    print(peak_l)

    # 条件ごとにフラグを立てていく
    # ①カウントの条件
    if peak_l['count'] == 2 and peak_o['count'] >= 4:
        f_count = True
        print("  カウント達成")
    else:
        f_count = False
        print(" カウント未達")

    # ②戻り割合の条件
    if peak_l['gap'] / peak_o['gap'] < 0.5:
        f_return = True
        print("  割合達成", peak_l['gap'], peak_o['gap'], round(peak_l['gap'] / peak_o['gap'], 1))
    else:
        f_return = False
        print("  割合未達", peak_l['gap'], peak_o['gap'], round(peak_l['gap'] / peak_o['gap'], 1))

    # ③偏差値の条件
    if peak_o['stdev'] > 50:
        f_size = True
        print("  偏差値達成", peak_o['stdev'])
    else:
        f_size = False
        print("  偏差値未達", peak_o['stdev'])

    if f_count and f_return and f_size:
        ans = True
    else:
        ans = False

    return {
        "ans": ans,
        "start_price": peak_l['peak'],
        "lc_range": peak_o['gap']/4,
        "tp_range": 0.05,
        "expect_direction": peak_o['direction'],
    }




