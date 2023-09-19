import datetime  # 日付関係
import pandas as pd  # add_peaks
import programs.tokens as tk  # Token等、各自環境の設定ファイル（git対象外）
import programs.classOanda as classOanda
import programs.fTurnInspection as fTurn
import programs.fGeneric as f


def peaks_collect(df_r):
    """
    リバースされたデータフレーム（直近が上）から、極値をN回分求める
    基本的にトップとボトムが交互になる
    :return:
    """
    # 基本検索と同様、最初の一つは除外する
    df_r = df_r[1:]

    peaks = []  # 結果格納用
    for i in range(20):
        if len(df_r) == 0:
            break
        # ans = turn_each_inspection(df_r)
        ans = fTurn.turn_each_inspection_skip(df_r)
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
    # print(peaks)
    # print(peaks[1:])
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
        "from_last_peak":  from_last_peak,  # 最後のPeakから何分経っているか(自身[最新]を含み、lastPeakを含まない）
        "latest_peak_group": latest_peak_group,  # 直近からみて直近のグループ
        "second_peak_group": second_peak_group
    }


def calChangeFromPeaks(same_peaks_group):
    memo = ""
    line_send = 0
    print("test")
    # (0)情報の収集
    target_peak = same_peaks_group[0]['peak']
    target_time = same_peaks_group[0]['time']
    print("target_peak:", target_peak, target_time)
    # (1)直近二つのピークの情報
    f.delYear(target_time)
    gap_latest2 = round(same_peaks_group[0]['peak'] - same_peaks_group[1]['peak'], 3)  # 直近二つのピークの金額差(変化後＝０＝最新　ー　直前）
    memo_latest = f.delYear(target_time) + "-" + f.delYear(same_peaks_group[1]['time']) + \
                  "[" + str(target_peak) + "-" + str(same_peaks_group[1]['peak']) + "]" + \
                  "方向" + str(same_peaks_group[0]['direction']) + " GAP" + str(gap_latest2)
    print(memo_latest)

    # （２）直近のピークと、一番近い同方向のピークを検索（３個分）
    peaks_target = same_peaks_group[:3]  # 出来れば近いほうがいいので直近３個分の同方向ピークにする
    peaks_gap = 100  # とりあえず大きな値
    skip_peaks = []
    index = 1  # 1からスタート

    for i in range(len(peaks_target)):
        if i == 0:
            # ０個目は同価格になるのでスルー
            ans_dic = peaks_target[i]  # 初期値の設定
        else:
            comp_info = peaks_target[i]
            if abs(target_peak - comp_info['peak']) < peaks_gap:
                ans_dic = comp_info  # Gap最小場所の更新
                peaks_gap = target_peak - comp_info['peak']  # peakGapの更新
                index = i
            else:
                skip_peaks.append(comp_info)
    # 情報表示print("一番ギャップの少ないピーク", index)
    gap_min = round(abs(ans_dic['peak'] - target_peak), 3)
    price_min = ans_dic['peak']
    time_min = ans_dic['time']
    gap_time = classOanda.str_to_time(target_time) - classOanda.str_to_time(time_min)
    memo_mini_gap = f.delYear(target_time) + "-" + f.delYear(time_min) + \
                    "[" + str(target_peak) + "-" + str(price_min) + "]" + \
                    "方向" + str(same_peaks_group[0]['direction']) + " GAP" + str(gap_min) + " TimeGap" + str(gap_time)

    return {
        "gap_latest2" : gap_latest2,
        "memo_latest": memo_latest,
        "gap_min": gap_min,
        "memo_mini_gap": memo_mini_gap,
        "data": same_peaks_group,
    }


def latestFlagFigure(peak_informations):
    # ■■二つのPeakLineの関係性の算出
    # ■各々の変化状況を取得する
    latest_info = calChangeFromPeaks(peak_informations['latest_peak_group'])
    second_info = calChangeFromPeaks(peak_informations['second_peak_group'])
    latest_peak_gap = latest_info['data'][0]['peak'] - second_info['data'][0]['peak']  # ピーク間の差分（大きさ）

    # ■二つがどのような形状か（平行、広がり、縮まり）
    lg = latest_info['gap_latest2']
    sg = second_info['gap_latest2']
    # 平行かの確認
    send_para = 0
    if abs(lg - sg) < 0.005:  # ほぼ平行とみなす場合
        print("平行(", latest_peak_gap, ")")
        para_memo = "平行 " + str(round(latest_peak_gap, 3)) + ")"
        send_para = 1
    else:
        para_memo = "Not平行"
    para_memo = latest_info['memo_latest'] + para_memo

    # フラッグ形状の確認
    level_change = 0.011  # これより小さい場合、傾きが少ないとみなす
    slope_change = 0.02  # これより大きい場合、傾きが大きいとみなす
    ans_memo = ""
    send_ans = 0
    if abs(lg) < level_change:  # 「直近分が」単品の水平基準を満たす
        if slope_change <= abs(sg):  # 「セカンド分が」傾きが大きいとみなされる場合（セカンド群が）
            if sg < 0:  # 「セカンド分」が下向きの場合
                ans_memo = "直近水平(逆フラ)" + str(round(latest_peak_gap, 3)) + ")"
                send_ans = 1
            else:  # 「セカンド分が」上向きの場合
                ans_memo = "直近水平(正フラ)" + str(round(latest_peak_gap, 3)) + ")"
                send_ans = 1
        elif level_change < abs(sg) < slope_change:  # 「セカンド分の」傾きが中途半端な場合
            print("直近水平")
        else:  # 「セカンド分」の傾きが水平の場合
            print("直近水平&平行")
    elif abs(sg) < level_change:  # 「セカンド分が」水平の場合
        if slope_change <= abs(lg):  # 「直近分が」傾きが大きいとみなされる場合（セカンド群が）
            if lg < 0:  # 「直近分が」が下向きの場合
                ans_memo = "セカ水平(逆フラ)" + str(round(latest_peak_gap, 3)) + ")"
                send_ans = 1
            else:  # 「直近分が」上向きの場合
                ans_memo = "セカ水平(正フラ)" + str(round(latest_peak_gap, 3)) + ")"
                send_ans = 1
        elif level_change < abs(lg) < slope_change:  # 「直近分が」傾きが中途半端な場合
            print("セカンド水平")
        else:  # 「セカンド分」の傾きが水平の場合
            print("セカンド水平&平行")
    ans_memo = latest_info['memo_latest'] + ans_memo

    return {
        "para_send": send_para,
        "para_memo": para_memo,
        "ans_memo": ans_memo,
        "ans_send": send_ans
    }


def mainInspectionPeakLine(ins_condition):
    # 引数の情報を入れ替える
    data_r = ins_condition['data_r']
    peak_information = peaks_collect(data_r)  # ピーク情報を取得する（全情報）

    # ■（１）直近の旗形状を分析する
    latest_flag_figure = latestFlagFigure(peak_information)

    return latest_flag_figure

